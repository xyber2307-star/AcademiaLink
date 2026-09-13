import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.firebase import get_db
from app.models import (
    DataProvenance,
    SkillRecommendationItem,
    SkillRecommendationsResponse,
    SkillTaxonomyCategoriesResponse,
    SkillTaxonomyEntry,
    SkillTaxonomyType,
    UserProfileResponse,
)

logger = logging.getLogger("academialink.skills_taxonomy")

router = APIRouter(prefix="/skills/taxonomy", tags=["Skill Taxonomy"])


def _serialize(doc_id: str, data: dict) -> SkillTaxonomyEntry:
    return SkillTaxonomyEntry(
        id=doc_id,
        name=data.get("name", doc_id),
        category=data.get("category", "Uncategorized"),
        subcategory=data.get("subcategory"),
        type=data.get("type", "technical"),
        description=data.get("description", ""),
        aliases=data.get("aliases") or [],
        relatedSkills=data.get("relatedSkills") or [],
        parentSkill=data.get("parentSkill"),
        assessmentAvailable=bool(data.get("assessmentAvailable", False)),
        active=bool(data.get("active", True)),
        source=data.get("source", "seed"),
        version=int(data.get("version", 1)),
        popularity=int(data.get("popularity", 0)),
        createdAt=data.get("createdAt"),
        updatedAt=data.get("updatedAt"),
    )


@router.get("/search", response_model=List[SkillTaxonomyEntry], summary="Search the canonical skill taxonomy")
async def search_skills(
    q: Optional[str] = Query(None, max_length=150, description="Search text - matches skill name or alias"),
    category: Optional[str] = Query(None, max_length=150, description="Filter by top-level category"),
    subcategory: Optional[str] = Query(None, max_length=150, description="Filter by subcategory"),
    type: Optional[SkillTaxonomyType] = Query(None, description="Filter by type: technical, tool, soft, domain"),
    limit: int = Query(50, ge=1, le=200),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Dynamic skill search across the entire Firestore-backed taxonomy - never requires a
    frontend redeploy when new skills are added by an admin.
    """
    db = get_db()
    docs = db.collection("skills").where("active", "==", True).stream()

    results: List[SkillTaxonomyEntry] = []
    q_low = q.strip().lower() if q else None

    for doc in docs:
        data = doc.to_dict() or {}
        if category and data.get("category") != category:
            continue
        if subcategory and data.get("subcategory") != subcategory:
            continue
        if type and data.get("type") != type:
            continue
        if q_low:
            name_low = str(data.get("name", "")).lower()
            aliases_low = [a.lower() for a in (data.get("aliases") or [])]
            if q_low not in name_low and not any(q_low in a for a in aliases_low):
                continue
        results.append(_serialize(doc.id, data))

    results.sort(key=lambda s: s.name.lower())
    return results[:limit]


@router.get("/categories", response_model=SkillTaxonomyCategoriesResponse, summary="List taxonomy categories and subcategories")
async def get_taxonomy_categories(current_user: UserProfileResponse = Depends(get_current_user)):
    """Returns categories/subcategories actually present in the live taxonomy (never hard-coded)."""
    db = get_db()
    docs = db.collection("skills").where("active", "==", True).stream()

    categories = set()
    sub_by_cat: Dict[str, set] = {}
    for doc in docs:
        data = doc.to_dict() or {}
        cat = data.get("category")
        sub = data.get("subcategory")
        if not cat:
            continue
        categories.add(cat)
        sub_by_cat.setdefault(cat, set())
        if sub:
            sub_by_cat[cat].add(sub)

    return SkillTaxonomyCategoriesResponse(
        categories=sorted(categories),
        subcategories_by_category={k: sorted(v) for k, v in sub_by_cat.items()},
    )


@router.get("/popular", response_model=List[SkillTaxonomyEntry], summary="Most popular skills by real usage")
async def get_popular_skills(
    limit: int = Query(12, ge=1, le=50),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Popularity is a real counter incremented each time a student adds or is assessed on a skill
    (see app/routes/skills.py) - never an arbitrary/editorial ranking.
    """
    db = get_db()
    docs = (
        db.collection("skills")
        .where("active", "==", True)
        .order_by("popularity", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [_serialize(d.id, d.to_dict() or {}) for d in docs]


@router.get("/{skill_id}", response_model=SkillTaxonomyEntry, summary="Get a single taxonomy skill by id")
async def get_taxonomy_skill(skill_id: str, current_user: UserProfileResponse = Depends(get_current_user)):
    db = get_db()
    doc = db.collection("skills").document(skill_id).get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found")
    return _serialize(doc.id, doc.to_dict() or {})


@router.get("/recommendations/me", response_model=SkillRecommendationsResponse, summary="Get data-driven skill recommendations for the current student")
async def get_skill_recommendations(current_user: UserProfileResponse = Depends(get_current_user)):
    """
    Recommends skills based on REAL system data only:
      1. The student's stored targetRole (from their profile).
      2. Live market skill demand for that role, from the Job Market Intelligence engine
         (Adzuna-backed, see app/services/market_data_provider.py) filtered by role keyword.
      3. The student's current verified/self-declared skills (users/{uid}/skills).
    Recommended skills = market-demanded skills the student does not already have, ranked by
    real market frequency. Never an arbitrary/static suggestion list.
    """
    from app.services.market_data_provider import market_data_manager

    db = get_db()
    target_role = getattr(current_user, "targetRole", None)

    current_skills: List[str] = []
    try:
        skills_ref = db.collection("users").document(current_user.uid).collection("skills")
        for doc in skills_ref.stream():
            data = doc.to_dict() or {}
            name = str(data.get("name") or "").strip()
            if name:
                current_skills.append(name)
    except Exception as e:
        logger.warning("Could not load current skills for %s: %s", current_user.uid, e)

    if not target_role:
        return SkillRecommendationsResponse(
            target_role=None,
            current_skills=current_skills,
            recommendations=[],
            explanation="Set a target role on your profile to get market-driven skill recommendations.",
            provenance=DataProvenance(source="skill_recommendation_engine", data_status="unavailable"),
        )

    demand = market_data_manager.get_skill_demand(role=target_role, time_range="all")
    if demand.status != "available" or not demand.skills:
        return SkillRecommendationsResponse(
            target_role=target_role,
            current_skills=current_skills,
            recommendations=[],
            explanation=f"No live market postings found for role '{target_role}' yet to base recommendations on.",
            provenance=DataProvenance(source="skill_recommendation_engine", data_status="unavailable"),
        )

    current_skills_low = {s.lower() for s in current_skills}
    recs: List[SkillRecommendationItem] = []
    for item in demand.skills:
        if item.skill.lower() in current_skills_low:
            continue
        priority = "High" if item.percentage >= 30 else ("Medium" if item.percentage >= 10 else "Low")
        recs.append(SkillRecommendationItem(
            skill=item.skill,
            reason=f"Required in {item.percentage}% of live '{target_role}' postings analyzed ({item.observed_postings} postings).",
            market_frequency_percentage=item.percentage,
            priority=priority,
        ))

    recs = recs[:10]
    explanation = (
        f"Based on {demand.total_postings_analyzed} live job postings for '{target_role}' and your "
        f"{len(current_skills)} current skill(s)."
    )

    return SkillRecommendationsResponse(
        target_role=target_role,
        current_skills=current_skills,
        recommendations=recs,
        explanation=explanation,
        provenance=DataProvenance(source="skill_recommendation_engine", data_status="available", retrieved_at=datetime.now(timezone.utc).isoformat()),
    )

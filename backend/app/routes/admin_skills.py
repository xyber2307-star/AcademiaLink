import logging
import re
from datetime import datetime, timezone
from typing import List, Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import require_admin
from app.firebase import get_db
from app.models import (
    SkillMergeRequest,
    SkillReviewQueueItem,
    SkillTaxonomyCreate,
    SkillTaxonomyEntry,
    SkillTaxonomyType,
    SkillTaxonomyUpdate,
    UserProfileResponse,
)

logger = logging.getLogger("academialink.admin_skills")

router = APIRouter(prefix="/admin/skills", tags=["Admin: Skill Taxonomy Management"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return slug.strip("_") or "skill"


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


def _find_existing_by_name_or_alias(db, name: str, exclude_id: Optional[str] = None) -> Optional[str]:
    """Case-insensitive search across name AND aliases of every active/inactive skill, to prevent duplicates."""
    name_low = name.strip().lower()
    for doc in db.collection("skills").stream():
        if exclude_id and doc.id == exclude_id:
            continue
        data = doc.to_dict() or {}
        if str(data.get("name", "")).strip().lower() == name_low:
            return doc.id
        if name_low in [a.strip().lower() for a in (data.get("aliases") or [])]:
            return doc.id
    return None


@router.get("", response_model=List[SkillTaxonomyEntry], summary="List all skills (including inactive) for admin management")
async def list_all_skills(
    include_inactive: bool = Query(True),
    q: Optional[str] = Query(None, max_length=150),
    current_user: UserProfileResponse = Depends(require_admin),
):
    db = get_db()
    docs = list(db.collection("skills").stream())
    results = []
    q_low = q.strip().lower() if q else None
    for doc in docs:
        data = doc.to_dict() or {}
        if not include_inactive and not data.get("active", True):
            continue
        if q_low and q_low not in str(data.get("name", "")).lower():
            continue
        results.append(_serialize(doc.id, data))
    results.sort(key=lambda s: s.name.lower())
    return results


@router.post("", response_model=SkillTaxonomyEntry, status_code=status.HTTP_201_CREATED, summary="Add a new canonical skill")
async def create_skill(
    payload: SkillTaxonomyCreate,
    current_user: UserProfileResponse = Depends(require_admin),
):
    """Admin-only. Rejects duplicate names/aliases with HTTP 409 rather than silently creating a copy."""
    db = get_db()
    existing_id = _find_existing_by_name_or_alias(db, payload.name)
    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A skill named or aliased '{payload.name}' already exists (id: {existing_id}). Use an alias or merge instead.",
        )

    slug = _slugify(payload.name)
    doc_ref = db.collection("skills").document(slug)
    if doc_ref.get().exists:
        # Extremely unlikely slug collision between two different names - disambiguate.
        slug = f"{slug}_{db.collection('skills').document().id[:6].lower()}"
        doc_ref = db.collection("skills").document(slug)

    now_iso = datetime.now(timezone.utc).isoformat()
    data = payload.model_dump()
    data.update({
        "active": True,
        "source": f"admin:{current_user.uid}",
        "version": 1,
        "popularity": 0,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    })
    doc_ref.set(data)
    logger.info("Admin %s created skill '%s' (id=%s)", current_user.uid, payload.name, slug)
    return _serialize(slug, data)


@router.put("/{skill_id}", response_model=SkillTaxonomyEntry, summary="Edit a skill's metadata")
async def update_skill(
    skill_id: str,
    payload: SkillTaxonomyUpdate,
    current_user: UserProfileResponse = Depends(require_admin),
):
    db = get_db()
    doc_ref = db.collection("skills").document(skill_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found")

    update_data = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if "name" in update_data:
        clash_id = _find_existing_by_name_or_alias(db, update_data["name"], exclude_id=skill_id)
        if clash_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another skill already uses the name/alias '{update_data['name']}' (id: {clash_id}).",
            )
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    doc_ref.set(update_data, merge=True)
    fresh = doc_ref.get()
    logger.info("Admin %s updated skill '%s'", current_user.uid, skill_id)
    return _serialize(fresh.id, fresh.to_dict() or {})


@router.delete("/{skill_id}", response_model=SkillTaxonomyEntry, summary="Deactivate a skill (soft delete)")
async def deactivate_skill(skill_id: str, current_user: UserProfileResponse = Depends(require_admin)):
    """
    Soft delete only - a skill is never hard-deleted, since students may already hold verified
    assessment history / evidence referencing it by this id.
    """
    db = get_db()
    doc_ref = db.collection("skills").document(skill_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found")
    doc_ref.set({"active": False, "updatedAt": datetime.now(timezone.utc).isoformat()}, merge=True)
    fresh = doc_ref.get()
    logger.info("Admin %s deactivated skill '%s'", current_user.uid, skill_id)
    return _serialize(fresh.id, fresh.to_dict() or {})


@router.post("/{skill_id}/reactivate", response_model=SkillTaxonomyEntry, summary="Reactivate a previously deactivated skill")
async def reactivate_skill(skill_id: str, current_user: UserProfileResponse = Depends(require_admin)):
    db = get_db()
    doc_ref = db.collection("skills").document(skill_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill '{skill_id}' not found")
    doc_ref.set({"active": True, "updatedAt": datetime.now(timezone.utc).isoformat()}, merge=True)
    fresh = doc_ref.get()
    return _serialize(fresh.id, fresh.to_dict() or {})


@router.post("/merge", response_model=SkillTaxonomyEntry, summary="Merge a duplicate skill into a canonical target")
async def merge_skills(
    payload: SkillMergeRequest,
    current_user: UserProfileResponse = Depends(require_admin),
):
    """
    Deactivates the source skill, adds its name (and aliases) as aliases of the target, and
    points source.parentSkill at the target. Does NOT retroactively rewrite existing students'
    skill records that reference the source skill id - see admin documentation / final report
    for this known limitation.
    """
    db = get_db()
    source_ref = db.collection("skills").document(payload.source_skill_id)
    target_ref = db.collection("skills").document(payload.target_skill_id)
    source_doc = source_ref.get()
    target_doc = target_ref.get()

    if not source_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Source skill '{payload.source_skill_id}' not found")
    if not target_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Target skill '{payload.target_skill_id}' not found")
    if payload.source_skill_id == payload.target_skill_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot merge a skill into itself")

    source_data = source_doc.to_dict() or {}
    target_data = target_doc.to_dict() or {}

    now_iso = datetime.now(timezone.utc).isoformat()
    new_aliases = list(set((target_data.get("aliases") or []) + [source_data.get("name", "")] + (source_data.get("aliases") or [])))
    new_aliases = [a for a in new_aliases if a]

    target_ref.set({"aliases": new_aliases, "updatedAt": now_iso}, merge=True)
    source_ref.set({
        "active": False,
        "parentSkill": payload.target_skill_id,
        "updatedAt": now_iso,
    }, merge=True)

    logger.info("Admin %s merged skill '%s' into '%s'", current_user.uid, payload.source_skill_id, payload.target_skill_id)
    fresh_target = target_ref.get()
    return _serialize(fresh_target.id, fresh_target.to_dict() or {})


@router.get("/review-queue", response_model=List[SkillReviewQueueItem], summary="View terms discovered from job descriptions pending taxonomy review")
async def get_review_queue(
    status_filter: Literal["pending", "approved", "rejected"] = Query("pending", alias="status"),
    current_user: UserProfileResponse = Depends(require_admin),
):
    db = get_db()
    docs = db.collection("skill_review_queue").where("status", "==", status_filter).stream()
    items = []
    for doc in docs:
        data = doc.to_dict() or {}
        items.append(SkillReviewQueueItem(
            id=doc.id,
            term=data.get("term", doc.id),
            occurrences=int(data.get("occurrences", 1)),
            example_context=data.get("example_context"),
            status=data.get("status", "pending"),
            createdAt=data.get("createdAt"),
            updatedAt=data.get("updatedAt"),
        ))
    items.sort(key=lambda i: i.occurrences, reverse=True)
    return items


@router.post("/review-queue/{item_id}/approve", response_model=SkillTaxonomyEntry, summary="Approve a discovered term as a new canonical skill")
async def approve_review_item(
    item_id: str,
    category: str = Query(..., min_length=1, max_length=150, description="Category to assign to the new skill"),
    subcategory: Optional[str] = Query(None, max_length=150),
    type: SkillTaxonomyType = Query("tool", description="technical, tool, soft, or domain"),
    current_user: UserProfileResponse = Depends(require_admin),
):
    db = get_db()
    queue_ref = db.collection("skill_review_queue").document(item_id)
    queue_doc = queue_ref.get()
    if not queue_doc.exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review item '{item_id}' not found")

    term = (queue_doc.to_dict() or {}).get("term", item_id)
    existing_id = _find_existing_by_name_or_alias(db, term)
    now_iso = datetime.now(timezone.utc).isoformat()

    if existing_id:
        # Term turned out to already be a known alias/name - just close the queue item.
        queue_ref.set({"status": "approved", "updatedAt": now_iso, "resolvedAs": existing_id}, merge=True)
        fresh = db.collection("skills").document(existing_id).get()
        return _serialize(fresh.id, fresh.to_dict() or {})

    slug = _slugify(term)
    doc_ref = db.collection("skills").document(slug)
    data = {
        "name": term,
        "category": category,
        "subcategory": subcategory,
        "type": type,
        "description": "",
        "aliases": [],
        "relatedSkills": [],
        "parentSkill": None,
        "assessmentAvailable": False,
        "active": True,
        "source": f"job_intelligence_review:{current_user.uid}",
        "version": 1,
        "popularity": 0,
        "createdAt": now_iso,
        "updatedAt": now_iso,
    }
    doc_ref.set(data)
    queue_ref.set({"status": "approved", "updatedAt": now_iso, "resolvedAs": slug}, merge=True)
    logger.info("Admin %s approved review-queue term '%s' as new skill '%s'", current_user.uid, term, slug)
    return _serialize(slug, data)


@router.post("/review-queue/{item_id}/reject", summary="Reject a discovered term (not a legitimate skill)")
async def reject_review_item(item_id: str, current_user: UserProfileResponse = Depends(require_admin)):
    db = get_db()
    queue_ref = db.collection("skill_review_queue").document(item_id)
    if not queue_ref.get().exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review item '{item_id}' not found")
    queue_ref.set({"status": "rejected", "updatedAt": datetime.now(timezone.utc).isoformat()}, merge=True)
    return {"success": True, "id": item_id, "status": "rejected"}

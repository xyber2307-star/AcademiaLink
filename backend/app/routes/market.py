from datetime import datetime, timezone
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user, verify_firebase_token
from app.firebase import get_db
from app.models import (
    CompanyMarketDetailResponse,
    CompanyMarketSummary,
    CompanyPreferenceRequest,
    DataProvenance,
    MarketJobRecord,
    MarketLocationOptionsResponse,
    MarketOverviewResponse,
    MarketTimeRange,
    MarketTrendsResponse,
    SkillDemandResponse,
    StudentMarketSkillGapResponse,
    UserProfileResponse,
)
from app.rate_limit import require_public_rate_limit
from app.services.market_data_provider import market_data_manager

logger = logging.getLogger("academialink.market_routes")

router = APIRouter(prefix="/market", tags=["Job Market Intelligence"])


@router.get("/overview", response_model=MarketOverviewResponse, summary="Get high-level real market intelligence overview", dependencies=[Depends(require_public_rate_limit)])
async def get_market_overview(
    country: Optional[str] = Query(None, max_length=150, description="Filter by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter by state or province"),
    city: Optional[str] = Query(None, max_length=150, description="Filter by city"),
    company: Optional[str] = Query(None, max_length=150, description="Filter by company"),
    role: Optional[str] = Query(None, max_length=150, description="Filter by job role/title"),
    category: Optional[str] = Query(None, max_length=150, description="Filter by skill category"),
    time_range: Optional[MarketTimeRange] = Query("last_3_months", description="Time filter: current, last_1_month, last_3_months, custom, all"),
    start_date: Optional[str] = Query(None, max_length=150, description="Custom start date (ISO string)"),
    end_date: Optional[str] = Query(None, max_length=150, description="Custom end date (ISO string)"),
):
    """
    Calculates aggregated real-world market intelligence.
    Distinguishes observed job postings from verified hiring data.
    Returns transparent empty states if no data exists.
    """
    return market_data_manager.get_market_overview(
        country=country,
        state=state,
        city=city,
        company=company,
        role=role,
        category=category,
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/live-count", summary="Get the live headline vacancy count reported directly by the connected job-data provider", dependencies=[Depends(require_public_rate_limit)])
async def get_live_vacancy_count(
    location: Optional[str] = Query(None, max_length=150, description="City/region to search, e.g. Hyderabad, Bengaluru. Omit for country-wide."),
    keyword: Optional[str] = Query(None, max_length=150, description="Search keyword, e.g. 'software engineer'"),
    country: Optional[str] = Query(None, max_length=150, description="Two-letter provider country code, defaults to the configured country"),
):
    """
    Returns the real total-match count reported by the connected job-data provider (Adzuna) for
    the given location/keyword - not a locally-fabricated estimate. Use for a headline
    "X accessible vacancies found through connected job-data sources" style figure.
    """
    return market_data_manager.get_live_vacancy_count(location=location, keyword=keyword, country=country)


@router.get("/locations", response_model=MarketLocationOptionsResponse, summary="Get dynamic locations available in market data", dependencies=[Depends(require_public_rate_limit)])
async def get_market_locations():
    """Returns dynamic countries, states, and cities present in the actual dataset (never hard-coded)."""
    return market_data_manager.get_distinct_locations()


@router.get("/companies", response_model=List[CompanyMarketSummary], summary="List companies with observed postings and target/dream company status", dependencies=[Depends(require_public_rate_limit)])
async def get_market_companies(
    country: Optional[str] = Query(None, max_length=150, description="Filter by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter by state"),
    city: Optional[str] = Query(None, max_length=150, description="Filter by city"),
    time_range: Optional[MarketTimeRange] = Query("last_3_months", description="Time period filter"),
    search: Optional[str] = Query(None, max_length=150, description="Search company name"),
):
    """
    Lists companies based on real observed postings.
    Does not assume high-volume companies are student dream companies.
    """
    return market_data_manager.get_companies_summary(
        country=country,
        state=state,
        city=city,
        time_range=time_range,
        search=search,
    )


@router.get("/company/{company}", response_model=CompanyMarketDetailResponse, summary="Get deep company market analytics", dependencies=[Depends(require_public_rate_limit)])
async def get_company_detail(
    company: str,
    country: Optional[str] = Query(None, max_length=150, description="Filter by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter by state"),
    city: Optional[str] = Query(None, max_length=150, description="Filter by city"),
    time_range: Optional[MarketTimeRange] = Query("last_3_months", description="Time period filter"),
):
    """
    Detailed company analysis including observed postings, open roles, posting dates,
    locations, required/preferred skills, experience requirements, employment types,
    and historical monthly posting activity.
    Works for Reliance, Google, Microsoft, startups, or any company present in real data.
    """
    return market_data_manager.get_company_detail(
        company=company,
        country=country,
        state=state,
        city=city,
        time_range=time_range,
    )


@router.get("/jobs", response_model=List[MarketJobRecord], summary="List filtered raw market job postings", dependencies=[Depends(require_public_rate_limit)])
async def get_market_jobs(
    country: Optional[str] = Query(None, max_length=150, description="Filter by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter by state"),
    city: Optional[str] = Query(None, max_length=150, description="Filter by city"),
    company: Optional[str] = Query(None, max_length=150, description="Filter by company"),
    role: Optional[str] = Query(None, max_length=150, description="Filter by role"),
    category: Optional[str] = Query(None, max_length=150, description="Filter by category"),
    skill: Optional[str] = Query(None, max_length=150, description="Filter by exact skill name"),
    time_range: Optional[MarketTimeRange] = Query("last_3_months", description="Time period filter"),
    start_date: Optional[str] = Query(None, max_length=150, description="Custom start date"),
    end_date: Optional[str] = Query(None, max_length=150, description="Custom end date"),
    limit: int = Query(50, ge=1, le=200, description="Max jobs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Returns normalized individual market job records matching query parameters."""
    all_jobs, configured, _ = market_data_manager.get_all_jobs()
    if not configured or not all_jobs:
        return []

    filtered = market_data_manager.filter_jobs(
        all_jobs,
        country=country,
        state=state,
        city=city,
        company=company,
        role=role,
        category=category,
        skill=skill,
        time_range=time_range,
        start_date=start_date,
        end_date=end_date,
    )
    return filtered[offset : offset + limit]


@router.get("/jobs/count", summary="Get total count of filtered market job postings (for pagination)", dependencies=[Depends(require_public_rate_limit)])
async def get_market_jobs_count(
    country: Optional[str] = Query(None, max_length=150, description="Filter by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter by state"),
    city: Optional[str] = Query(None, max_length=150, description="Filter by city"),
    company: Optional[str] = Query(None, max_length=150, description="Filter by company"),
    role: Optional[str] = Query(None, max_length=150, description="Filter by role"),
    category: Optional[str] = Query(None, max_length=150, description="Filter by category"),
    skill: Optional[str] = Query(None, max_length=150, description="Filter by exact skill name"),
    time_range: Optional[MarketTimeRange] = Query("last_3_months", description="Time period filter"),
):
    """Returns the total number of live market postings matching the given filters, for pagination."""
    all_jobs, configured, msg = market_data_manager.get_all_jobs()
    if not configured:
        return {"total": 0, "configured": False, "message": msg}

    filtered = market_data_manager.filter_jobs(
        all_jobs,
        country=country,
        state=state,
        city=city,
        company=company,
        role=role,
        category=category,
        skill=skill,
        time_range=time_range,
    )
    return {"total": len(filtered), "configured": True, "message": msg}


@router.get("/skills", response_model=SkillDemandResponse, summary="Analyze market skill demand percentages and frequencies", dependencies=[Depends(require_public_rate_limit)])
async def get_skill_demand(
    country: Optional[str] = Query(None, max_length=150, description="Filter by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter by state"),
    city: Optional[str] = Query(None, max_length=150, description="Filter by city"),
    company: Optional[str] = Query(None, max_length=150, description="Filter by company"),
    role: Optional[str] = Query(None, max_length=150, description="Filter by role"),
    category: Optional[str] = Query(None, max_length=150, description="Filter by category"),
    time_range: Optional[MarketTimeRange] = Query("last_3_months", description="Time period filter"),
):
    """
    Computes exact frequency and percentages of skills across observed job postings.
    Formula: percentage = (skill_postings_count / total_postings_analyzed) * 100.
    """
    return market_data_manager.get_skill_demand(
        country=country,
        state=state,
        city=city,
        company=company,
        role=role,
        category=category,
        time_range=time_range,
    )


@router.get("/trends", response_model=MarketTrendsResponse, summary="Calculate 3-month market trends", dependencies=[Depends(require_public_rate_limit)])
async def get_market_trends(
    country: Optional[str] = Query(None, max_length=150, description="Filter by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter by state"),
    city: Optional[str] = Query(None, max_length=150, description="Filter by city"),
    company: Optional[str] = Query(None, max_length=150, description="Filter by company"),
):
    """
    Calculates previous three months trend across observed postings, companies, and skills.
    If fewer than 2 distinct calendar months or < 30 days of data exist, returns:
    'Insufficient historical data for this trend.'
    """
    return market_data_manager.get_market_trends(
        country=country,
        state=state,
        city=city,
        company=company,
    )


@router.get("/skill-gap", response_model=StudentMarketSkillGapResponse, summary="Connect student skills to real market demand")
async def get_student_market_skill_gap(
    company: Optional[str] = Query(None, max_length=150, description="Target company to analyze gap against"),
    role: Optional[str] = Query(None, max_length=150, description="Target role to analyze gap against"),
    country: Optional[str] = Query(None, max_length=150, description="Filter market requirements by country"),
    state: Optional[str] = Query(None, max_length=150, description="Filter market requirements by state"),
    city: Optional[str] = Query(None, max_length=150, description="Filter market requirements by city"),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Student Personalization (Requirement 10):
    Connects Job Market Intelligence to the existing student skill-gap system (Step 29).
    Flow: Market Demand -> Company/Role -> Required Skills -> Student Skills -> Skill Gap -> Learning Priority.
    Reuses deterministic compute_weighted_job_match. Never modifies verified student proficiency.
    """
    db = get_db()
    student_skills: Dict[str, float] = {}

    try:
        skills_ref = db.collection("users").document(current_user.uid).collection("skills")
        for doc in skills_ref.stream():
            s_data = doc.to_dict() or {}
            s_name = str(s_data.get("name") or doc.id).strip()
            prof = float(s_data.get("proficiency", 1.0))
            student_skills[s_name] = prof
    except Exception as e:
        logger.error("Error retrieving student skills for UID %s: %s", current_user.uid, e)

    return market_data_manager.compute_student_market_gap(
        student_skills=student_skills,
        target_company=company,
        target_role=role,
        country=country,
        state=state,
        city=city,
    )


@router.post("/companies/preference", summary="Mark company as Target Company or Dream Company")
async def set_company_preference(
    payload: CompanyPreferenceRequest,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Allows the student to mark companies as Target Company or Dream Company.
    Persists preferences in the user's Firestore profile under target_companies / dream_companies.
    """
    db = get_db()
    user_ref = db.collection("users").document(current_user.uid)
    user_doc = user_ref.get()
    u_data = user_doc.to_dict() or {}

    target_comps = list(u_data.get("target_companies") or [])
    dream_comps = list(u_data.get("dream_companies") or [])

    comp_name = payload.company.strip()

    if payload.preference_type == "target":
        if payload.action == "add" and comp_name not in target_comps:
            target_comps.append(comp_name)
        elif payload.action == "remove" and comp_name in target_comps:
            target_comps.remove(comp_name)
    elif payload.preference_type == "dream":
        if payload.action == "add" and comp_name not in dream_comps:
            dream_comps.append(comp_name)
        elif payload.action == "remove" and comp_name in dream_comps:
            dream_comps.remove(comp_name)

    user_ref.set(
        {
            "target_companies": target_comps,
            "dream_companies": dream_comps,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        },
        merge=True,
    )

    return {
        "success": True,
        "company": comp_name,
        "preference_type": payload.preference_type,
        "action": payload.action,
        "target_companies": target_comps,
        "dream_companies": dream_comps,
    }

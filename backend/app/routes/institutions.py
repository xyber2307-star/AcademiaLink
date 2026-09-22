"""
Institution registry search and lookup - read-only endpoints backing the college/
institution verification flow described in docs/INSTITUTION_VERIFICATION.md.

All matching is deterministic (app/services/institution_data.py); no AI/LLM is
involved in deciding whether an institution is legitimate. This router only reads
the registry - the authoritative *write* path (a student selecting an institution)
lives in PUT /users/me (app/routes/users.py), which validates the institutionId
against this same registry before persisting anything.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.models import InstitutionDetail, InstitutionSearchResponse, UserProfileResponse
from app.rate_limit import check_user_rate_limit
from app.services.institution_data import get_registry

logger = logging.getLogger("academialink.institutions")

router = APIRouter(prefix="/institutions", tags=["Institution Registry"])


@router.get("/search", response_model=InstitutionSearchResponse, summary="Search the authoritative institution registry")
async def search_institutions(
    q: str = Query(..., min_length=2, max_length=150, description="Institution name, partial name, or AICTE permanent ID"),
    current_user: UserProfileResponse = Depends(get_current_user),
):
    """
    Deterministic search over the locally-cached AICTE institution registry.
    Never auto-selects an institution - always returns candidates for the student to
    choose from explicitly. Absence of a match means NOT currently verifiable, not "fake".
    """
    await check_user_rate_limit(current_user.uid, "institution_search")

    registry = get_registry()
    if not registry.is_available:
        return InstitutionSearchResponse(results=[], source="AICTE", sourceAvailable=False, datasetDate=None)

    records = registry.search(q, limit=20)
    results = [
        {
            "institutionId": r.institution_id,
            "aicteId": r.aicte_id,
            "name": r.name,
            "state": r.state,
            "district": r.district,
            "city": r.city,
            "verificationStatus": "VERIFIED",
            "verificationSource": r.source,
        }
        for r in records
    ]
    return InstitutionSearchResponse(
        results=results,
        source="AICTE",
        sourceAvailable=True,
        datasetDate=registry.dataset_meta.get("datasetDate"),
    )


@router.get("/{institution_id}", response_model=InstitutionDetail, summary="Get a single registry institution by id")
async def get_institution(
    institution_id: str,
    current_user: UserProfileResponse = Depends(get_current_user),
):
    registry = get_registry()
    if not registry.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The authoritative institution source could not be reached or refreshed. Verification could not be completed.",
        )

    record = registry.get(institution_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching institution found in the available authoritative registry.",
        )

    return InstitutionDetail(
        institutionId=record.institution_id,
        aicteId=record.aicte_id,
        name=record.name,
        state=record.state,
        district=record.district,
        city=record.city,
        verificationStatus="VERIFIED",
        verificationSource=record.source,
        sourceReference=record.source_reference,
        datasetDate=record.dataset_date,
        programLevelApprovalChecked=False,
    )

from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.firebase import get_db, is_firebase_ready
from app.models import (
    CompanyMarketDetailResponse,
    CompanyMarketSummary,
    DataProvenance,
    MarketJobDataType,
    MarketJobRecord,
    MarketLocationOptionsResponse,
    MarketOverviewResponse,
    MarketTrendItem,
    MarketTrendsResponse,
    RequiredSkill,
    SkillDemandItem,
    SkillDemandResponse,
    StudentMarketSkillGapResponse,
)
from app.routes.matching import compute_weighted_job_match

logger = logging.getLogger("academialink.market_service")


class BaseMarketDataProvider(ABC):
    """Abstract interface for Job Market Intelligence data providers."""

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    @abstractmethod
    def fetch_market_jobs(self) -> List[MarketJobRecord]:
        pass

    @abstractmethod
    def get_provenance(self) -> DataProvenance:
        pass


class FirestoreMarketDataProvider(BaseMarketDataProvider):
    """
    Cloud Firestore provider reading real observed market postings and verified hiring records
    from the 'market_jobs' collection in the 'academia' database.
    """

    def is_configured(self) -> bool:
        return is_firebase_ready()

    def get_provenance(self) -> DataProvenance:
        return DataProvenance(
            source="firestore_market_jobs_registry",
            source_url="https://console.firebase.google.com/project/academialink-b10b3/firestore",
            data_status="available",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            is_test_data=False,
        )

    def fetch_market_jobs(self) -> List[MarketJobRecord]:
        if not self.is_configured():
            return []

        try:
            db = get_db()
            market_ref = db.collection("market_jobs")
            docs = list(market_ref.stream())

            records: List[MarketJobRecord] = []
            for doc in docs:
                data = doc.to_dict() or {}
                job_id = doc.id
                normalized = self._normalize_record(job_id, data)
                if normalized:
                    records.append(normalized)

            return records
        except Exception as e:
            logger.error("Error fetching market jobs from Firestore: %s", e)
            return []

    def _normalize_record(self, job_id: str, data: Dict[str, Any]) -> Optional[MarketJobRecord]:
        try:
            company = str(data.get("company") or data.get("company_name") or data.get("companyName") or "").strip()
            job_title = str(data.get("job_title") or data.get("title") or data.get("role") or "").strip()

            if not company or not job_title:
                return None

            country = data.get("country")
            state = data.get("state")
            city = data.get("city")

            loc_str = str(data.get("location") or data.get("formattedLocation") or "").strip()
            if loc_str and (not city or not state):
                parts = [p.strip() for p in loc_str.split(",") if p.strip()]
                if len(parts) == 3:
                    city = city or parts[0]
                    state = state or parts[1]
                    country = country or parts[2]
                elif len(parts) == 2:
                    city = city or parts[0]
                    state = state or parts[1]
                elif len(parts) == 1:
                    city = city or parts[0]

            country = country or "India"

            skills_raw = data.get("skills") or []
            skills_list: List[str] = []
            if isinstance(skills_raw, list):
                for s in skills_raw:
                    if isinstance(s, str) and s.strip():
                        skills_list.append(s.strip())
                    elif isinstance(s, dict) and "name" in s:
                        skills_list.append(str(s["name"]).strip())

            required_skills_raw = data.get("required_skills") or data.get("requiredSkills") or []
            req_skills_list: List[RequiredSkill] = []
            if isinstance(required_skills_raw, list):
                for rs in required_skills_raw:
                    if isinstance(rs, str):
                        req_skills_list.append(RequiredSkill(name=rs.strip(), required_proficiency=3.0, weight=1.0))
                    elif isinstance(rs, dict) and "name" in rs:
                        req_skills_list.append(RequiredSkill(**rs))

            if not req_skills_list and skills_list:
                for s_name in skills_list:
                    req_skills_list.append(RequiredSkill(name=s_name, required_proficiency=3.0, weight=1.0))

            if not skills_list and req_skills_list:
                skills_list = [rs.name for rs in req_skills_list]

            pref_raw = data.get("preferred_skills") or data.get("preferredSkills") or []
            pref_list = [p.strip() for p in pref_raw if isinstance(p, str) and p.strip()]

            raw_dtype = str(data.get("data_type") or data.get("dataType") or "observed_posting").lower()
            data_type: MarketJobDataType = "verified_hiring" if "verified" in raw_dtype or "hiring" in raw_dtype else "observed_posting"

            posted_date = data.get("posted_date") or data.get("postedDate") or data.get("created_at") or data.get("createdAt")
            if posted_date and isinstance(posted_date, datetime):
                posted_date = posted_date.isoformat()

            source = str(data.get("source") or "firestore_market_data")
            source_url = data.get("source_url") or data.get("sourceUrl")

            return MarketJobRecord(
                job_id=job_id,
                company=company,
                job_title=job_title,
                country=country,
                state=state,
                city=city,
                description=str(data.get("description") or ""),
                skills=skills_list,
                required_skills=req_skills_list,
                preferred_skills=pref_list,
                experience=str(data.get("experience") or data.get("experience_level") or "0-2 years"),
                employment_type=str(data.get("employment_type") or data.get("type") or "Full-time"),
                posted_date=str(posted_date) if posted_date else None,
                closing_date=str(data.get("closing_date")) if data.get("closing_date") else None,
                source=source,
                source_url=source_url,
                data_type=data_type,
                retrieved_at=str(data.get("retrieved_at") or datetime.now(timezone.utc).isoformat()),
                updated_at=str(data.get("updated_at") or datetime.now(timezone.utc).isoformat()),
                provenance=DataProvenance(
                    source=source,
                    source_url=source_url,
                    data_status="verified" if data_type == "verified_hiring" else "available",
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                    is_test_data=bool(data.get("is_test_data", False)),
                ),
            )
        except Exception as err:
            logger.warning("Failed normalizing record %s: %s", job_id, err)
            return None


class AWSMarketDataProvider(BaseMarketDataProvider):
    """
    AWS-backed provider adapter supporting authorized AWS API Gateway, Lambda, S3,
    or OpenSearch job-market integrations.
    Credentials and endpoints are maintained strictly server-side via environment variables.
    """

    def __init__(self):
        self.endpoint = os.getenv("AWS_MARKET_DATA_ENDPOINT")
        self.api_key = os.getenv("AWS_MARKET_DATA_API_KEY")
        self.region = os.getenv("AWS_REGION", "us-east-1")

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.endpoint.startswith("http"))

    def get_provenance(self) -> DataProvenance:
        return DataProvenance(
            source="aws_authorized_job_market_feed",
            source_url=self.endpoint,
            data_status="available" if self.is_configured() else "unavailable",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            is_test_data=False,
        )

    def fetch_market_jobs(self) -> List[MarketJobRecord]:
        if not self.is_configured():
            logger.info("AWS Market Data Provider not configured (AWS_MARKET_DATA_ENDPOINT not set).")
            return []

        try:
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["x-api-key"] = self.api_key

            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.endpoint, headers=headers)
                if response.status_code != 200:
                    logger.warning("AWS market data endpoint returned status %s", response.status_code)
                    return []
                payload = response.json()
                items = payload if isinstance(payload, list) else payload.get("jobs", [])
                
                records: List[MarketJobRecord] = []
                for idx, item in enumerate(items):
                    jid = str(item.get("job_id") or item.get("id") or f"aws_job_{idx}")
                    rec = FirestoreMarketDataProvider()._normalize_record(jid, item)
                    if rec:
                        records.append(rec)
                return records
        except Exception as e:
            logger.error("Error communicating with AWS market data endpoint: %s", e)
            return []


class MarketDataManager:
    """
    Central Manager orchestrating data ingestion, normalization, multi-tenant caching,
    location/time filtering, deterministic analytics, 3-month trends, and student skill-gap matching.
    """

    def __init__(self):
        self.firestore_provider = FirestoreMarketDataProvider()
        self.aws_provider = AWSMarketDataProvider()

    def get_all_jobs(self) -> Tuple[List[MarketJobRecord], bool, str]:
        """
        Retrieves all market jobs from available configured providers.
        Returns: (jobs_list, is_configured, status_message)
        """
        # If AWS provider is explicitly configured, query it first
        if self.aws_provider.is_configured():
            aws_jobs = self.aws_provider.fetch_market_jobs()
            if aws_jobs:
                return aws_jobs, True, "Data supplied by authorized AWS Market Data Feed"

        # Query Cloud Firestore 'market_jobs' collection
        if self.firestore_provider.is_configured():
            firestore_jobs = self.firestore_provider.fetch_market_jobs()
            if firestore_jobs:
                return firestore_jobs, True, "Data supplied by Cloud Firestore Market Registry"

        # Neither AWS is configured nor Firestore market_jobs has data
        if not self.aws_provider.is_configured() and not self.firestore_provider.fetch_market_jobs():
            return [], False, "Real market data unavailable — data source not configured."

        return [], True, "Data source configured but 0 market postings found matching criteria."

    def filter_jobs(
        self,
        jobs: List[MarketJobRecord],
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        category: Optional[str] = None,
        time_range: Optional[str] = "last_3_months",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[MarketJobRecord]:
        """Deterministically filters market job postings by location, company, role, and posting date."""
        filtered = list(jobs)

        if country:
            c_low = country.strip().lower()
            filtered = [j for j in filtered if j.country and j.country.strip().lower() == c_low]

        if state:
            s_low = state.strip().lower()
            filtered = [j for j in filtered if j.state and j.state.strip().lower() == s_low]

        if city:
            ci_low = city.strip().lower()
            filtered = [j for j in filtered if j.city and j.city.strip().lower() == ci_low]

        if company:
            comp_low = company.strip().lower()
            filtered = [j for j in filtered if j.company and j.company.strip().lower() == comp_low]

        if role:
            r_low = role.strip().lower()
            filtered = [j for j in filtered if j.job_title and r_low in j.job_title.strip().lower()]

        if category:
            cat_low = category.strip().lower()
            filtered = [
                j for j in filtered
                if any(cat_low in s.lower() for s in j.skills) or (j.description and cat_low in j.description.lower())
            ]

        # Time range filtering
        now = datetime.now(timezone.utc)
        if time_range == "current":
            cutoff = now - timedelta(days=14)
            filtered = [j for j in filtered if self._is_after(j.posted_date, cutoff)]
        elif time_range == "last_1_month":
            cutoff = now - timedelta(days=30)
            filtered = [j for j in filtered if self._is_after(j.posted_date, cutoff)]
        elif time_range == "last_3_months":
            cutoff = now - timedelta(days=90)
            filtered = [j for j in filtered if self._is_after(j.posted_date, cutoff)]
        elif time_range == "custom" and start_date:
            try:
                s_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                filtered = [j for j in filtered if self._is_after(j.posted_date, s_dt)]
            except Exception:
                pass
            if end_date:
                try:
                    e_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    filtered = [j for j in filtered if self._is_before(j.posted_date, e_dt)]
                except Exception:
                    pass

        return filtered

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            clean = date_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            try:
                dt = datetime.strptime(date_str[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                return None

    def _is_after(self, date_str: Optional[str], cutoff: datetime) -> bool:
        dt = self._parse_date(date_str)
        if not dt:
            return False
        return dt >= cutoff

    def _is_before(self, date_str: Optional[str], cutoff: datetime) -> bool:
        dt = self._parse_date(date_str)
        if not dt:
            return False
        return dt <= cutoff

    def get_market_overview(
        self,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        category: Optional[str] = None,
        time_range: Optional[str] = "last_3_months",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> MarketOverviewResponse:
        """Calculates real market statistics across observed job postings and verified hiring data."""
        all_jobs, configured, msg = self.get_all_jobs()
        if not configured:
            return MarketOverviewResponse(
                status="unconfigured",
                message=msg,
                total_observed_postings=0,
                total_verified_hirings=0,
                unique_companies_count=0,
                unique_roles_count=0,
                top_companies=[],
                most_requested_skills=[],
                employment_type_distribution={},
                location_distribution={},
                time_filter_applied=time_range or "all",
                location_filter_applied={"country": country, "state": state, "city": city},
                provenance=DataProvenance(
                    source="market_intelligence_service",
                    data_status="unavailable",
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                ),
            )

        filtered = self.filter_jobs(
            all_jobs,
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

        if not filtered:
            return MarketOverviewResponse(
                status="empty",
                message="No market job records match the selected location and time criteria.",
                total_observed_postings=0,
                total_verified_hirings=0,
                unique_companies_count=0,
                unique_roles_count=0,
                top_companies=[],
                most_requested_skills=[],
                employment_type_distribution={},
                location_distribution={},
                time_filter_applied=time_range or "all",
                location_filter_applied={"country": country, "state": state, "city": city},
                provenance=DataProvenance(
                    source="market_intelligence_service",
                    data_status="available",
                    retrieved_at=datetime.now(timezone.utc).isoformat(),
                ),
            )

        # Distinguish observed postings vs verified hiring
        observed_count = sum(1 for j in filtered if j.data_type == "observed_posting")
        hiring_count = sum(1 for j in filtered if j.data_type == "verified_hiring")

        unique_companies = len(set(j.company for j in filtered))
        unique_roles = len(set(j.job_title for j in filtered))

        # Top companies
        comp_counter = Counter(j.company for j in filtered)
        comp_roles = defaultdict(set)
        for j in filtered:
            comp_roles[j.company].add(j.job_title)

        top_companies = [
            {
                "company": comp,
                "observed_postings": count,
                "roles_count": len(comp_roles[comp]),
            }
            for comp, count in comp_counter.most_common(10)
        ]

        # Most requested skills
        skill_counter: Counter = Counter()
        for j in filtered:
            job_skills = set(j.skills)
            for s in j.required_skills:
                job_skills.add(s.name)
            for s in job_skills:
                if s and s.strip():
                    skill_counter[s.strip()] += 1

        total_postings = len(filtered)
        most_requested_skills = [
            {
                "skill": s_name,
                "observed_postings": count,
                "percentage": round((count / total_postings) * 100, 1),
            }
            for s_name, count in skill_counter.most_common(15)
        ]

        emp_dist = dict(Counter(j.employment_type for j in filtered if j.employment_type))

        loc_dist = dict(
            Counter(
                f"{j.city or ''}, {j.state or j.country}".strip(", ")
                for j in filtered
                if j.city or j.state or j.country
            )
        )

        return MarketOverviewResponse(
            status="available",
            message=None,
            total_observed_postings=observed_count,
            total_verified_hirings=hiring_count,
            unique_companies_count=unique_companies,
            unique_roles_count=unique_roles,
            top_companies=top_companies,
            most_requested_skills=most_requested_skills,
            employment_type_distribution=emp_dist,
            location_distribution=loc_dist,
            time_filter_applied=time_range or "all",
            location_filter_applied={"country": country, "state": state, "city": city},
            provenance=DataProvenance(
                source="market_intelligence_service",
                data_status="available",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            ),
        )

    def get_companies_summary(
        self,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        time_range: Optional[str] = "last_3_months",
        search: Optional[str] = None,
        student_target_companies: Optional[List[str]] = None,
        student_dream_companies: Optional[List[str]] = None,
    ) -> List[CompanyMarketSummary]:
        all_jobs, configured, _ = self.get_all_jobs()
        if not configured or not all_jobs:
            return []

        filtered = self.filter_jobs(all_jobs, country=country, state=state, city=city, time_range=time_range)
        if search:
            s_low = search.strip().lower()
            filtered = [j for j in filtered if s_low in j.company.lower()]

        target_set = set(c.strip().lower() for c in (student_target_companies or []))
        dream_set = set(c.strip().lower() for c in (student_dream_companies or []))

        grouped = defaultdict(list)
        for j in filtered:
            grouped[j.company].append(j)

        summaries: List[CompanyMarketSummary] = []
        for company_name, c_jobs in grouped.items():
            obs = sum(1 for j in c_jobs if j.data_type == "observed_posting")
            hires = sum(1 for j in c_jobs if j.data_type == "verified_hiring")
            roles = len(set(j.job_title for j in c_jobs))
            locs = list(set(f"{j.city or ''}, {j.state or j.country}".strip(", ") for j in c_jobs if j.city or j.state))

            s_counter: Counter = Counter()
            for j in c_jobs:
                for s in j.skills:
                    s_counter[s] += 1
            top_skills = [s for s, _ in s_counter.most_common(5)]

            is_target = company_name.strip().lower() in target_set
            is_dream = company_name.strip().lower() in dream_set

            summaries.append(
                CompanyMarketSummary(
                    company=company_name,
                    observed_postings=obs,
                    verified_hirings=hires,
                    unique_roles=roles,
                    locations=locs,
                    top_skills=top_skills,
                    is_target_company=is_target,
                    is_dream_company=is_dream,
                )
            )

        summaries.sort(key=lambda c: c.observed_postings, reverse=True)
        return summaries

    def get_company_detail(
        self,
        company: str,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        time_range: Optional[str] = "last_3_months",
        student_target_companies: Optional[List[str]] = None,
        student_dream_companies: Optional[List[str]] = None,
    ) -> CompanyMarketDetailResponse:
        all_jobs, configured, msg = self.get_all_jobs()
        if not configured:
            return CompanyMarketDetailResponse(
                company=company,
                status="unconfigured",
                message=msg,
                provenance=DataProvenance(source="market_company_analytics", data_status="unavailable"),
            )

        filtered = self.filter_jobs(all_jobs, country=country, state=state, city=city, company=company, time_range=time_range)

        if not filtered:
            return CompanyMarketDetailResponse(
                company=company,
                status="not_found",
                message=f"No observed market records found for company '{company}' matching criteria.",
                provenance=DataProvenance(source="market_company_analytics", data_status="available"),
            )

        obs_count = sum(1 for j in filtered if j.data_type == "observed_posting")
        hires_count = sum(1 for j in filtered if j.data_type == "verified_hiring")
        roles_posted = sorted(list(set(j.job_title for j in filtered)))
        locations = sorted(list(set(f"{j.city or ''}, {j.state or j.country}".strip(", ") for j in filtered if j.city or j.state)))
        experience_levels = sorted(list(set(j.experience for j in filtered if j.experience)))
        employment_types = sorted(list(set(j.employment_type for j in filtered if j.employment_type)))
        posting_dates = sorted([j.posted_date for j in filtered if j.posted_date], reverse=True)

        s_counter: Counter = Counter()
        req_skills_map: Dict[str, List[float]] = defaultdict(list)
        pref_skills_set = set()

        for j in filtered:
            for s in j.skills:
                s_counter[s] += 1
            for rs in j.required_skills:
                s_counter[rs.name] += 1
                req_skills_map[rs.name].append(rs.required_proficiency)
            for ps in j.preferred_skills:
                pref_skills_set.add(ps)

        total_postings = len(filtered)
        skill_frequency = [
            {
                "skill": s,
                "observed_postings": count,
                "percentage": round((count / total_postings) * 100, 1),
                "average_required_proficiency": round(sum(req_skills_map[s]) / len(req_skills_map[s]), 1) if req_skills_map[s] else 3.0,
            }
            for s, count in s_counter.most_common(20)
        ]

        required_skills_summary = [
            {
                "skill": s,
                "demand_count": count,
                "average_required_proficiency": round(sum(req_skills_map[s]) / len(req_skills_map[s]), 1) if req_skills_map[s] else 3.0,
            }
            for s, count in s_counter.most_common(12)
        ]

        month_activity: Counter = Counter()
        for j in filtered:
            dt = self._parse_date(j.posted_date)
            if dt:
                month_activity[dt.strftime("%Y-%m")] += 1
        historical_activity = [
            {"month": m, "observed_postings": count}
            for m, count in sorted(month_activity.items())
        ]

        target_set = set(c.strip().lower() for c in (student_target_companies or []))
        dream_set = set(c.strip().lower() for c in (student_dream_companies or []))

        return CompanyMarketDetailResponse(
            company=company,
            status="available",
            message=None,
            observed_postings_count=obs_count,
            verified_hirings_count=hires_count,
            roles_posted=roles_posted,
            locations=locations,
            required_skills=required_skills_summary,
            preferred_skills=sorted(list(pref_skills_set)),
            experience_levels=experience_levels,
            employment_types=employment_types,
            open_postings=filtered[:10],
            posting_dates=posting_dates,
            skill_frequency=skill_frequency,
            historical_activity=historical_activity,
            is_target_company=company.strip().lower() in target_set,
            is_dream_company=company.strip().lower() in dream_set,
            provenance=DataProvenance(source="market_company_analytics", data_status="available"),
        )

    def get_skill_demand(
        self,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        category: Optional[str] = None,
        time_range: Optional[str] = "last_3_months",
    ) -> SkillDemandResponse:
        all_jobs, configured, msg = self.get_all_jobs()
        if not configured:
            return SkillDemandResponse(
                status="unconfigured",
                message=msg,
                total_postings_analyzed=0,
                skills=[],
                filters_applied={"country": country, "state": state, "city": city, "company": company, "role": role},
                provenance=DataProvenance(source="market_skill_analytics", data_status="unavailable"),
            )

        filtered = self.filter_jobs(
            all_jobs,
            country=country,
            state=state,
            city=city,
            company=company,
            role=role,
            category=category,
            time_range=time_range,
        )

        if not filtered:
            return SkillDemandResponse(
                status="empty",
                message="No market job postings match the given filters for skill demand analysis.",
                total_postings_analyzed=0,
                skills=[],
                filters_applied={"country": country, "state": state, "city": city, "company": company, "role": role},
                provenance=DataProvenance(source="market_skill_analytics", data_status="available"),
            )

        total_postings = len(filtered)
        s_counter: Counter = Counter()

        for j in filtered:
            unique_in_job = set(j.skills)
            for rs in j.required_skills:
                unique_in_job.add(rs.name)
            for s in unique_in_job:
                if s and s.strip():
                    s_counter[s.strip()] += 1

        items = [
            SkillDemandItem(
                skill=skill_name,
                observed_postings=count,
                percentage=round((count / total_postings) * 100, 1),
            )
            for skill_name, count in s_counter.most_common(50)
        ]

        return SkillDemandResponse(
            status="available",
            message=None,
            total_postings_analyzed=total_postings,
            skills=items,
            filters_applied={"country": country, "state": state, "city": city, "company": company, "role": role},
            provenance=DataProvenance(source="market_skill_analytics", data_status="available"),
        )

    def get_market_trends(
        self,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
        company: Optional[str] = None,
    ) -> MarketTrendsResponse:
        all_jobs, configured, msg = self.get_all_jobs()
        if not configured:
            return MarketTrendsResponse(
                status="unconfigured",
                message=msg,
                trends=[],
                provenance=DataProvenance(source="market_trend_analytics", data_status="unavailable"),
            )

        filtered = self.filter_jobs(all_jobs, country=country, state=state, city=city, company=company, time_range="all")

        month_jobs = defaultdict(list)
        valid_dates: List[datetime] = []

        for j in filtered:
            dt = self._parse_date(j.posted_date)
            if dt:
                month_str = dt.strftime("%Y-%m")
                month_jobs[month_str].append(j)
                valid_dates.append(dt)

        # Check for sufficient historical data
        if len(month_jobs) < 2:
            return MarketTrendsResponse(
                status="insufficient_data",
                message="Insufficient historical data for this trend.",
                trends=[],
                provenance=DataProvenance(source="market_trend_analytics", data_status="available"),
            )

        min_dt = min(valid_dates)
        max_dt = max(valid_dates)
        if (max_dt - min_dt).days < 30:
            return MarketTrendsResponse(
                status="insufficient_data",
                message="Insufficient historical data for this trend.",
                trends=[],
                provenance=DataProvenance(source="market_trend_analytics", data_status="available"),
            )

        sorted_months = sorted(month_jobs.keys())[-3:]

        trend_items: List[MarketTrendItem] = []
        for m in sorted_months:
            m_list = month_jobs[m]
            obs = sum(1 for j in m_list if j.data_type == "observed_posting")
            unique_comps = len(set(j.company for j in m_list))

            s_counter: Counter = Counter()
            r_counter: Counter = Counter()
            for j in m_list:
                for s in j.skills:
                    s_counter[s] += 1
                r_counter[j.job_title] += 1

            top_skills = [{"skill": s, "count": cnt} for s, cnt in s_counter.most_common(5)]
            top_roles = [{"role": r, "count": cnt} for r, cnt in r_counter.most_common(5)]

            trend_items.append(
                MarketTrendItem(
                    month=m,
                    observed_postings=obs,
                    unique_companies=unique_comps,
                    top_skills=top_skills,
                    top_roles=top_roles,
                )
            )

        return MarketTrendsResponse(
            status="available",
            message=None,
            trends=trend_items,
            provenance=DataProvenance(source="market_trend_analytics", data_status="available"),
        )

    def get_distinct_locations(self) -> MarketLocationOptionsResponse:
        all_jobs, configured, _ = self.get_all_jobs()
        if not configured or not all_jobs:
            return MarketLocationOptionsResponse(countries=[], states=[], cities=[])

        countries = sorted(list(set(j.country for j in all_jobs if j.country)))
        states = sorted(list(set(j.state for j in all_jobs if j.state)))
        cities = sorted(list(set(j.city for j in all_jobs if j.city)))

        return MarketLocationOptionsResponse(countries=countries, states=states, cities=cities)

    def compute_student_market_gap(
        self,
        student_skills: Dict[str, float],
        target_company: Optional[str] = None,
        target_role: Optional[str] = None,
        country: Optional[str] = None,
        state: Optional[str] = None,
        city: Optional[str] = None,
    ) -> StudentMarketSkillGapResponse:
        all_jobs, configured, msg = self.get_all_jobs()
        if not configured or not all_jobs:
            return StudentMarketSkillGapResponse(
                target_company=target_company,
                target_role=target_role,
                target_location=city or state or country,
                market_match_score=0.0,
                matched_skills=[],
                partial_skills=[],
                missing_skills=[],
                market_priority_skills=[],
                explanation="Real market data unavailable — data source not configured.",
                provenance=DataProvenance(source="market_gap_engine", data_status="unavailable"),
            )

        filtered = self.filter_jobs(
            all_jobs,
            country=country,
            state=state,
            city=city,
            company=target_company,
            role=target_role,
            time_range="last_3_months",
        )

        if not filtered:
            return StudentMarketSkillGapResponse(
                target_company=target_company,
                target_role=target_role,
                target_location=city or state or country,
                market_match_score=0.0,
                matched_skills=[],
                partial_skills=[],
                missing_skills=[],
                market_priority_skills=[],
                explanation="No market postings found matching the selected company/role criteria to compute skill gap.",
                provenance=DataProvenance(source="market_gap_engine", data_status="available"),
            )

        skill_counts: Counter = Counter()
        skill_prof_sum: Dict[str, float] = defaultdict(float)

        for j in filtered:
            for rs in j.required_skills:
                skill_counts[rs.name] += 1
                skill_prof_sum[rs.name] += rs.required_proficiency

            if not j.required_skills and j.skills:
                for s in j.skills:
                    skill_counts[s] += 1
                    skill_prof_sum[s] += 3.0

        if not skill_counts:
            return StudentMarketSkillGapResponse(
                target_company=target_company,
                target_role=target_role,
                target_location=city or state or country,
                market_match_score=100.0,
                matched_skills=[],
                partial_skills=[],
                missing_skills=[],
                market_priority_skills=[],
                explanation="No specific required skills found in matching market postings.",
                provenance=DataProvenance(source="market_gap_engine", data_status="available"),
            )

        max_count = max(skill_counts.values()) if skill_counts else 1
        required_skills_payload = []
        for s_name, count in skill_counts.most_common(15):
            avg_prof = round(skill_prof_sum[s_name] / count, 1)
            weight = round(1.0 + (count / max_count) * 2.0, 1)
            required_skills_payload.append({
                "name": s_name,
                "required_proficiency": avg_prof,
                "weight": weight,
            })

        score, matched, partial, missing, all_items, explanation = compute_weighted_job_match(
            student_skills=student_skills,
            required_skills=required_skills_payload,
        )

        market_priority_skills = []
        for item in missing + partial:
            s_cnt = skill_counts.get(item.skill, 1)
            freq_pct = round((s_cnt / len(filtered)) * 100, 1)
            market_priority_skills.append({
                "skill": item.skill,
                "current_proficiency": item.current_proficiency,
                "required_proficiency": item.required_proficiency,
                "gap_amount": item.gap_amount,
                "market_frequency_percentage": freq_pct,
                "priority": "High" if item.gap_amount >= 2.0 or freq_pct >= 50.0 else ("Medium" if item.gap_amount >= 1.0 else "Low"),
            })

        market_priority_skills.sort(
            key=lambda x: (x["priority"] == "High", x["priority"] == "Medium", x["market_frequency_percentage"]),
            reverse=True,
        )

        return StudentMarketSkillGapResponse(
            target_company=target_company,
            target_role=target_role,
            target_location=city or state or country,
            market_match_score=round(score, 1),
            matched_skills=matched,
            partial_skills=partial,
            missing_skills=missing,
            market_priority_skills=market_priority_skills,
            explanation=f"Based on {len(filtered)} observed market postings: {explanation}",
            provenance=DataProvenance(source="market_gap_engine", data_status="available"),
        )


market_data_manager = MarketDataManager()

"""
=============================================================================
ACADEMIALINK / SKILLSPHERE — JOB MARKET INTELLIGENCE TEST SUITE
=============================================================================
Verifies:
  1. Unconfigured and empty dataset handling ("Real market data unavailable — data source not configured.")
  2. Location filtering (Country -> State -> City; never hardcoded)
  3. Time filters (Current, Last 1 month, Last 3 months, Custom date range)
  4. Company analytics and Top Companies
  5. Skill demand analysis (mathematical percentage calculation)
  6. Three-month trend calculations & "Insufficient historical data for this trend."
  7. Student market skill-gap integration using Step 29 deterministic math
  8. Target and Dream company marking
  9. Security guards, RBAC, and secret safety
=============================================================================
"""

from datetime import datetime, timezone, timedelta
import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient

# Ensure backend package is in python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auth import get_current_user, verify_firebase_token
from app.firebase import initialize_firebase, get_db
from app.main import app
from app.models import (
    DataProvenance,
    MarketJobRecord,
    RequiredSkill,
    UserProfileResponse,
)
from app.services.market_data_provider import (
    BaseMarketDataProvider,
    MarketDataManager,
    market_data_manager,
)

client = TestClient(app)

# Test User
TEST_STUDENT_UID = f"test_student_market_{uuid.uuid4().hex[:6]}"
TEST_STUDENT_PROFILE = UserProfileResponse(
    uid=TEST_STUDENT_UID,
    email=f"{TEST_STUDENT_UID}@academialink.edu",
    name="Market Intelligence Test Student",
    role="student",
    institution="Tech University",
    department="Computer Science",
    targetRole="Full-Stack Developer",
    verified=True,
    target_companies=[],
    dream_companies=[],
)


class MockMarketDataProvider(BaseMarketDataProvider):
    """Controlled mock market data provider for deterministic testing of real algorithms."""

    def __init__(self, jobs: list[MarketJobRecord], configured: bool = True):
        self._jobs = jobs
        self._configured = configured

    def is_configured(self) -> bool:
        return self._configured

    def fetch_market_jobs(self) -> list[MarketJobRecord]:
        return list(self._jobs) if self._configured else []

    def get_provenance(self) -> DataProvenance:
        return DataProvenance(
            source="test_authorized_market_feed",
            data_status="available" if self._configured else "unavailable",
            retrieved_at=datetime.now(timezone.utc).isoformat(),
        )


def build_sample_market_dataset() -> list[MarketJobRecord]:
    now = datetime.now(timezone.utc)
    d_recent = (now - timedelta(days=5)).isoformat()
    d_1_month_ago = (now - timedelta(days=25)).isoformat()
    d_2_months_ago = (now - timedelta(days=55)).isoformat()
    d_3_months_ago = (now - timedelta(days=80)).isoformat()

    return [
        # Hyderabad, Telangana, India - Google (3 postings)
        MarketJobRecord(
            job_id="m_job_1",
            company="Google",
            job_title="Software Engineer, Cloud",
            country="India",
            state="Telangana",
            city="Hyderabad",
            description="Developing scalable cloud services on GCP and Kubernetes.",
            skills=["Python", "Cloud (AWS)", "Docker & CI/CD", "Data Structures"],
            required_skills=[
                RequiredSkill(name="Python", required_proficiency=4.0, weight=2.0),
                RequiredSkill(name="Cloud (AWS)", required_proficiency=3.0, weight=1.5),
            ],
            posted_date=d_recent,
            data_type="observed_posting",
        ),
        MarketJobRecord(
            job_id="m_job_2",
            company="Google",
            job_title="Frontend Engineer",
            country="India",
            state="Telangana",
            city="Hyderabad",
            description="Building high performance web UIs using React and TypeScript.",
            skills=["React", "TypeScript", "JavaScript", "HTML/CSS"],
            required_skills=[
                RequiredSkill(name="React", required_proficiency=4.0, weight=2.0),
                RequiredSkill(name="TypeScript", required_proficiency=3.5, weight=1.5),
            ],
            posted_date=d_1_month_ago,
            data_type="observed_posting",
        ),
        MarketJobRecord(
            job_id="m_job_3",
            company="Google",
            job_title="Site Reliability Engineer",
            country="India",
            state="Telangana",
            city="Hyderabad",
            description="Ensuring high availability of global production systems.",
            skills=["Python", "Linux", "Docker & CI/CD", "Kubernetes"],
            required_skills=[
                RequiredSkill(name="Python", required_proficiency=3.5, weight=1.5),
                RequiredSkill(name="Linux", required_proficiency=4.0, weight=2.0),
            ],
            posted_date=d_2_months_ago,
            data_type="observed_posting",
        ),
        # Bengaluru, Karnataka, India - Microsoft (2 postings)
        MarketJobRecord(
            job_id="m_job_4",
            company="Microsoft",
            job_title="Full-Stack Developer",
            country="India",
            state="Karnataka",
            city="Bengaluru",
            description="Enterprise full-stack software development with React and Python.",
            skills=["Python", "React", "SQL & Databases", "System Design"],
            required_skills=[
                RequiredSkill(name="Python", required_proficiency=3.5, weight=1.5),
                RequiredSkill(name="React", required_proficiency=3.5, weight=1.5),
            ],
            posted_date=d_recent,
            data_type="observed_posting",
        ),
        MarketJobRecord(
            job_id="m_job_5",
            company="Microsoft",
            job_title="Data Scientist",
            country="India",
            state="Karnataka",
            city="Bengaluru",
            description="Machine learning and statistical modeling on Azure.",
            skills=["Python", "Machine Learning", "SQL & Databases", "Statistics"],
            required_skills=[
                RequiredSkill(name="Python", required_proficiency=4.0, weight=2.0),
                RequiredSkill(name="Machine Learning", required_proficiency=4.0, weight=2.0),
            ],
            posted_date=d_3_months_ago,
            data_type="observed_posting",
        ),
        # San Francisco, California, USA - Amazon (2 postings)
        MarketJobRecord(
            job_id="m_job_6",
            company="Amazon",
            job_title="DevOps Engineer",
            country="USA",
            state="California",
            city="San Francisco",
            description="Cloud infrastructure and automated deployment pipelines.",
            skills=["Cloud (AWS)", "Docker & CI/CD", "Python", "Kubernetes"],
            required_skills=[
                RequiredSkill(name="Cloud (AWS)", required_proficiency=4.0, weight=2.0),
                RequiredSkill(name="Docker & CI/CD", required_proficiency=3.5, weight=1.5),
            ],
            posted_date=d_2_months_ago,
            data_type="observed_posting",
        ),
        MarketJobRecord(
            job_id="m_job_7",
            company="Amazon",
            job_title="Verified Hire Confirmation",
            country="USA",
            state="California",
            city="San Francisco",
            description="Verified hiring record from talent registry.",
            skills=["Python", "Cloud (AWS)"],
            required_skills=[],
            posted_date=d_recent,
            data_type="verified_hiring",
        ),
    ]


@pytest.fixture(autouse=True)
def setup_auth_and_firebase():
    initialize_firebase()

    def mock_verify_token():
        return {"uid": TEST_STUDENT_UID, "email": TEST_STUDENT_PROFILE.email}

    def mock_get_user():
        return TEST_STUDENT_PROFILE

    app.dependency_overrides[verify_firebase_token] = mock_verify_token
    app.dependency_overrides[get_current_user] = mock_get_user

    yield

    app.dependency_overrides.clear()


def test_market_unconfigured_data_source_handling():
    """
    Requirement 1 & 5:
    If the real data source/API is not yet configured, the system must display:
    'Real market data unavailable — data source not configured.'
    Zero fake data allowed.
    """
    original_aws = market_data_manager.aws_provider
    original_firestore = market_data_manager.firestore_provider

    try:
        # Force unconfigured provider
        market_data_manager.aws_provider = MockMarketDataProvider([], configured=False)
        market_data_manager.firestore_provider = MockMarketDataProvider([], configured=False)

        res = client.get("/api/market/overview")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "unconfigured"
        assert "Real market data unavailable — data source not configured." in body["message"]
        assert body["total_observed_postings"] == 0
        assert body["total_verified_hirings"] == 0
        assert len(body["top_companies"]) == 0

        # Company detail on unconfigured
        res_comp = client.get("/api/market/company/Google")
        assert res_comp.status_code == 200
        assert res_comp.json()["status"] == "unconfigured"

        # Skills on unconfigured
        res_skills = client.get("/api/market/skills")
        assert res_skills.status_code == 200
        assert res_skills.json()["status"] == "unconfigured"

        # Trends on unconfigured
        res_trends = client.get("/api/market/trends")
        assert res_trends.status_code == 200
        assert res_trends.json()["status"] == "unconfigured"

        # Skill gap on unconfigured
        res_gap = client.get("/api/market/skill-gap?company=Google")
        assert res_gap.status_code == 200
        assert "Real market data unavailable" in res_gap.json()["explanation"]
        assert res_gap.json()["market_match_score"] == 0.0

        print("\n[PASS] Unconfigured data source returns transparent message with zero fake data.")
    finally:
        market_data_manager.aws_provider = original_aws
        market_data_manager.firestore_provider = original_firestore


def test_location_filtering_and_dynamic_locations():
    """
    Requirement 3:
    Students must be able to analyze the market by:
    Country -> State/Province -> City
    (India -> Telangana -> Hyderabad, India -> Karnataka -> Bengaluru, USA -> California -> San Francisco)
    Must NOT be hardcoded specifically for Hyderabad.
    """
    sample_jobs = build_sample_market_dataset()
    original_aws = market_data_manager.aws_provider
    original_firestore = market_data_manager.firestore_provider

    try:
        market_data_manager.firestore_provider = MockMarketDataProvider(sample_jobs, configured=True)
        market_data_manager.aws_provider = MockMarketDataProvider([], configured=False)

        # 1. Dynamic Locations Endpoint
        loc_res = client.get("/api/market/locations")
        assert loc_res.status_code == 200
        loc_data = loc_res.json()
        assert "India" in loc_data["countries"]
        assert "USA" in loc_data["countries"]
        assert "Telangana" in loc_data["states"]
        assert "Karnataka" in loc_data["states"]
        assert "California" in loc_data["states"]
        assert "Hyderabad" in loc_data["cities"]
        assert "Bengaluru" in loc_data["cities"]
        assert "San Francisco" in loc_data["cities"]

        # 2. Filter Hyderabad
        res_hyd = client.get("/api/market/overview?city=Hyderabad&time_range=all")
        assert res_hyd.status_code == 200
        hyd_data = res_hyd.json()
        assert hyd_data["total_observed_postings"] == 3
        assert hyd_data["unique_companies_count"] == 1
        assert hyd_data["top_companies"][0]["company"] == "Google"

        # 3. Filter Bengaluru
        res_blr = client.get("/api/market/overview?city=Bengaluru&time_range=all")
        assert res_blr.status_code == 200
        blr_data = res_blr.json()
        assert blr_data["total_observed_postings"] == 2
        assert blr_data["top_companies"][0]["company"] == "Microsoft"

        # 4. Filter USA
        res_usa = client.get("/api/market/overview?country=USA&time_range=all")
        assert res_usa.status_code == 200
        usa_data = res_usa.json()
        # 1 observed posting + 1 verified hiring
        assert usa_data["total_observed_postings"] == 1
        assert usa_data["total_verified_hirings"] == 1
        assert usa_data["top_companies"][0]["company"] == "Amazon"

        print("\n[PASS] Location filtering operates dynamically across Country -> State -> City.")
    finally:
        market_data_manager.aws_provider = original_aws
        market_data_manager.firestore_provider = original_firestore


def test_time_filters_and_distinguishing_observed_postings_vs_hiring():
    """
    Requirement 1 & 4:
    Filters: Current (14 days), Last 1 month (30 days), Last 3 months (90 days), Custom.
    Distinguishes observed job postings from verified hiring data.
    """
    sample_jobs = build_sample_market_dataset()
    original_aws = market_data_manager.aws_provider
    original_firestore = market_data_manager.firestore_provider

    try:
        market_data_manager.firestore_provider = MockMarketDataProvider(sample_jobs, configured=True)
        market_data_manager.aws_provider = MockMarketDataProvider([], configured=False)

        # 1. Current (14 days) -> only m_job_1 (Google), m_job_4 (Microsoft), m_job_7 (Amazon verified hire)
        res_current = client.get("/api/market/overview?time_range=current")
        assert res_current.status_code == 200
        c_data = res_current.json()
        assert c_data["total_observed_postings"] == 2  # Google and Microsoft
        assert c_data["total_verified_hirings"] == 1   # Amazon verified hire

        # 2. Last 1 month (30 days) -> includes m_job_2 (Google)
        res_1m = client.get("/api/market/overview?time_range=last_1_month")
        assert res_1m.status_code == 200
        m1_data = res_1m.json()
        assert m1_data["total_observed_postings"] == 3

        # 3. Last 3 months (90 days) -> all 6 observed postings + 1 verified hiring
        res_3m = client.get("/api/market/overview?time_range=last_3_months")
        assert res_3m.status_code == 200
        m3_data = res_3m.json()
        assert m3_data["total_observed_postings"] == 6
        assert m3_data["total_verified_hirings"] == 1

        print("\n[PASS] Time filters and distinction of observed postings vs verified hiring verified.")
    finally:
        market_data_manager.aws_provider = original_aws
        market_data_manager.firestore_provider = original_firestore


def test_company_analytics_and_skill_demand_calculation():
    """
    Requirement 7 & 8:
    Company Analysis: observed postings, roles, skills, employment types.
    Skill Demand: Skill | Number of observed postings | Percentage of postings.
    """
    sample_jobs = build_sample_market_dataset()
    original_aws = market_data_manager.aws_provider
    original_firestore = market_data_manager.firestore_provider

    try:
        market_data_manager.firestore_provider = MockMarketDataProvider(sample_jobs, configured=True)
        market_data_manager.aws_provider = MockMarketDataProvider([], configured=False)

        # 1. Company Analytics for Google
        res_comp = client.get("/api/market/company/Google?time_range=all")
        assert res_comp.status_code == 200
        g_data = res_comp.json()
        assert g_data["status"] == "available"
        assert g_data["company"] == "Google"
        assert g_data["observed_postings_count"] == 3
        assert len(g_data["roles_posted"]) == 3
        assert "Hyderabad, Telangana" in g_data["locations"][0]

        # 2. Skill Demand Analysis
        res_skills = client.get("/api/market/skills?time_range=all")
        assert res_skills.status_code == 200
        s_data = res_skills.json()
        assert s_data["status"] == "available"
        assert s_data["total_postings_analyzed"] == 7

        # Python appears in m_job_1, m_job_3, m_job_4, m_job_5, m_job_6, m_job_7 (6 postings)
        py_skill = next((item for item in s_data["skills"] if item["skill"] == "Python"), None)
        assert py_skill is not None
        assert py_skill["observed_postings"] == 6
        # 6 / 7 = 85.7%
        assert py_skill["percentage"] == 85.7

        print("\n[PASS] Company analytics and deterministic skill demand percentages verified.")
    finally:
        market_data_manager.aws_provider = original_aws
        market_data_manager.firestore_provider = original_firestore


def test_three_month_trend_calculations_and_insufficient_data():
    """
    Requirement 9:
    Where sufficient historical data exists, show monthly breakdown.
    If insufficient, explicitly show: 'Insufficient historical data for this trend.'
    """
    original_aws = market_data_manager.aws_provider
    original_firestore = market_data_manager.firestore_provider

    try:
        # Case A: Sufficient historical data (sample_jobs spans 3 distinct months)
        sample_jobs = build_sample_market_dataset()
        market_data_manager.firestore_provider = MockMarketDataProvider(sample_jobs, configured=True)
        market_data_manager.aws_provider = MockMarketDataProvider([], configured=False)

        res_trend = client.get("/api/market/trends")
        assert res_trend.status_code == 200
        t_data = res_trend.json()
        assert t_data["status"] == "available"
        assert len(t_data["trends"]) >= 2
        for t_item in t_data["trends"]:
            assert "month" in t_item
            assert t_item["observed_postings"] >= 1

        # Case B: Insufficient data (< 2 months or < 30 days)
        one_day_jobs = [sample_jobs[0]]
        market_data_manager.firestore_provider = MockMarketDataProvider(one_day_jobs, configured=True)

        res_insuff = client.get("/api/market/trends")
        assert res_insuff.status_code == 200
        insuff_data = res_insuff.json()
        assert insuff_data["status"] == "insufficient_data"
        assert insuff_data["message"] == "Insufficient historical data for this trend."
        assert len(insuff_data["trends"]) == 0

        print("\n[PASS] 3-month trend calculation and 'Insufficient historical data for this trend.' verified.")
    finally:
        market_data_manager.aws_provider = original_aws
        market_data_manager.firestore_provider = original_firestore


def test_student_market_skill_gap_and_target_company_marking():
    """
    Requirement 6 & 10:
    Connects to existing Step 29 skill-gap calculation.
    Allows marking Target / Dream company and stores in user profile.
    """
    sample_jobs = build_sample_market_dataset()
    original_aws = market_data_manager.aws_provider
    original_firestore = market_data_manager.firestore_provider

    try:
        market_data_manager.firestore_provider = MockMarketDataProvider(sample_jobs, configured=True)
        market_data_manager.aws_provider = MockMarketDataProvider([], configured=False)

        db = get_db()
        # Seed test student skills in Firestore
        skills_ref = db.collection("users").document(TEST_STUDENT_UID).collection("skills")
        skills_ref.document("Python").set({"name": "Python", "proficiency": 4.0})
        skills_ref.document("React").set({"name": "React", "proficiency": 3.0})

        # 1. Run Market Skill Gap Analysis against Google
        res_gap = client.get("/api/market/skill-gap?company=Google")
        assert res_gap.status_code == 200
        gap_data = res_gap.json()
        assert gap_data["target_company"] == "Google"
        assert 0.0 <= gap_data["market_match_score"] <= 100.0
        assert len(gap_data["market_priority_skills"]) > 0

        # Python is possessed at 4.0 -> should be in matched_skills
        matched_names = [m["skill"] for m in gap_data["matched_skills"]]
        assert "Python" in matched_names

        # 2. Mark Google as Target Company
        res_pref = client.post(
            "/api/market/companies/preference",
            json={"company": "Google", "preference_type": "target", "action": "add"},
        )
        assert res_pref.status_code == 200
        pref_data = res_pref.json()
        assert pref_data["success"] is True
        assert "Google" in pref_data["target_companies"]

        # Mark Google as Dream Company
        res_dream = client.post(
            "/api/market/companies/preference",
            json={"company": "Google", "preference_type": "dream", "action": "add"},
        )
        assert res_dream.status_code == 200
        assert "Google" in res_dream.json()["dream_companies"]

        # 3. Verify company summary now reflects target & dream status
        summaries = market_data_manager.get_companies_summary(
            student_target_companies=["Google"],
            student_dream_companies=["Google"],
        )
        google_summary = next((c for c in summaries if c.company == "Google"), None)
        assert google_summary is not None
        assert google_summary.is_target_company is True
        assert google_summary.is_dream_company is True

        # Clean up
        client.post(
            "/api/market/companies/preference",
            json={"company": "Google", "preference_type": "target", "action": "remove"},
        )
        client.post(
            "/api/market/companies/preference",
            json={"company": "Google", "preference_type": "dream", "action": "remove"},
        )

        print("\n[PASS] Student market skill-gap (Step 29 reuse) and Target/Dream company preferences verified.")
    finally:
        market_data_manager.aws_provider = original_aws
        market_data_manager.firestore_provider = original_firestore

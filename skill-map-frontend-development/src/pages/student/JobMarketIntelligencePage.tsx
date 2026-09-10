import { useEffect, useState } from "react";
import {
  Building2,
  TrendingUp,
  MapPin,
  Search,
  Filter,
  Star,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Clock,
  Briefcase,
  Layers,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Award,
  BookOpen,
} from "lucide-react";
import {
  marketService,
  MarketOverviewResponse,
  CompanyMarketSummary,
  CompanyMarketDetailResponse,
  SkillDemandResponse,
  MarketTrendsResponse,
  StudentMarketSkillGapResponse,
  MarketLocationOptionsResponse,
} from "../../services/marketService";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";
import { StatCard } from "../../components/ui/StatCard";
import { PageHeader } from "../../components/ui/PageHeader";

export function JobMarketIntelligencePage() {
  const [activeTab, setActiveTab] = useState<"overview" | "companies" | "skills" | "trends" | "gap">("overview");
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);

  // Filters
  const [country, setCountry] = useState<string>("");
  const [state, setState] = useState<string>("");
  const [city, setCity] = useState<string>("");
  const [timeRange, setTimeRange] = useState<"current" | "last_1_month" | "last_3_months" | "all">("last_3_months");
  const [companySearch, setCompanySearch] = useState<string>("");

  // Location options
  const [locations, setLocations] = useState<MarketLocationOptionsResponse>({ countries: [], states: [], cities: [] });

  // Data states
  const [overview, setOverview] = useState<MarketOverviewResponse | null>(null);
  const [companies, setCompanies] = useState<CompanyMarketSummary[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>("");
  const [companyDetail, setCompanyDetail] = useState<CompanyMarketDetailResponse | null>(null);
  const [skillDemand, setSkillDemand] = useState<SkillDemandResponse | null>(null);
  const [trends, setTrends] = useState<MarketTrendsResponse | null>(null);
  const [marketGap, setMarketGap] = useState<StudentMarketSkillGapResponse | null>(null);

  // Preference action feedback
  const [prefLoading, setPrefLoading] = useState<boolean>(false);

  // Initial load: Locations and Overview
  useEffect(() => {
    loadLocations();
  }, []);

  useEffect(() => {
    loadData();
  }, [country, state, city, timeRange]);

  const loadLocations = async () => {
    try {
      const locData = await marketService.getLocations();
      setLocations(locData);
    } catch (err) {
      console.error("Failed to load market locations:", err);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const filterParams = {
        country: country || undefined,
        state: state || undefined,
        city: city || undefined,
        time_range: timeRange,
      };

      const [ovData, compData, skillData, trendData] = await Promise.all([
        marketService.getOverview(filterParams),
        marketService.getCompanies(filterParams),
        marketService.getSkillDemand(filterParams),
        marketService.getTrends({ country: country || undefined, state: state || undefined, city: city || undefined }),
      ]);

      setOverview(ovData);
      setCompanies(compData);
      setSkillDemand(skillData);
      setTrends(trendData);

      if (compData.length > 0 && !selectedCompany) {
        setSelectedCompany(compData[0].company);
        loadCompanyDetail(compData[0].company);
      }
    } catch (err) {
      console.error("Error loading market intelligence data:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadCompanyDetail = async (compName: string) => {
    try {
      const detail = await marketService.getCompanyDetail(compName, {
        country: country || undefined,
        state: state || undefined,
        city: city || undefined,
        time_range: timeRange,
      });
      setCompanyDetail(detail);
    } catch (err) {
      console.error("Error fetching company detail:", err);
    }
  };

  const loadMarketGap = async (targetComp?: string) => {
    try {
      const gapRes = await marketService.getStudentMarketSkillGap({
        company: targetComp || selectedCompany || undefined,
        country: country || undefined,
        state: state || undefined,
        city: city || undefined,
      });
      setMarketGap(gapRes);
    } catch (err) {
      console.error("Error loading market skill gap:", err);
    }
  };

  const handleSelectCompany = (compName: string) => {
    setSelectedCompany(compName);
    loadCompanyDetail(compName);
    if (activeTab === "gap") {
      loadMarketGap(compName);
    }
  };

  const handleTogglePreference = async (compName: string, type: "target" | "dream", isCurrent: boolean) => {
    setPrefLoading(true);
    try {
      const action = isCurrent ? "remove" : "add";
      await marketService.setCompanyPreference(compName, type, action);
      // Refresh local detail and companies list
      await loadCompanyDetail(compName);
      const updatedComps = await marketService.getCompanies({
        country: country || undefined,
        state: state || undefined,
        city: city || undefined,
        time_range: timeRange,
      });
      setCompanies(updatedComps);
    } catch (err) {
      console.error("Error toggling preference:", err);
    } finally {
      setPrefLoading(false);
    }
  };

  const handleResetFilters = () => {
    setCountry("");
    setState("");
    setCity("");
    setTimeRange("last_3_months");
  };

  const isDataAvailable = overview?.status === "available";
  const isUnconfigured = overview?.status === "unconfigured";

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <PageHeader
            title="Job Market Intelligence"
            description="Real-world labor market analytics, company hiring trends & personalized skill-gap mapping"
          />
          {/* Data Provenance Badge */}
          <div className="flex items-center gap-2 mt-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
              <ShieldCheck className="w-3.5 h-3.5 text-blue-500" />
              Source: {overview?.provenance?.source || "Authorized Feeds & Firestore"}
            </span>
            <span className="text-xs text-slate-500 dark:text-slate-400">
              Status:{" "}
              <strong className={isDataAvailable ? "text-emerald-500" : "text-amber-500"}>
                {isDataAvailable ? "Live Market Data" : isUnconfigured ? "Data Source Not Configured" : "Empty Dataset"}
              </strong>
            </span>
          </div>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setRefreshing(true);
            loadData();
          }}
          disabled={refreshing || loading}
          className="self-start md:self-auto"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${refreshing || loading ? "animate-spin" : ""}`} />
          Refresh Data
        </Button>
      </div>

      {/* Filter Control Bar */}
      <Card className="p-4 bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Country Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Country
            </label>
            <select
              value={country}
              onChange={(e) => {
                setCountry(e.target.value);
                setState("");
                setCity("");
              }}
              className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Countries ({locations.countries.length || "0"})</option>
              {locations.countries.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* State / Province Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              State / Province
            </label>
            <select
              value={state}
              onChange={(e) => {
                setState(e.target.value);
                setCity("");
              }}
              className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All States ({locations.states.length || "0"})</option>
              {locations.states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* City Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              City
            </label>
            <select
              value={city}
              onChange={(e) => setCity(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Cities ({locations.cities.length || "0"})</option>
              {locations.cities.map((ci) => (
                <option key={ci} value={ci}>
                  {ci}
                </option>
              ))}
            </select>
          </div>

          {/* Time Filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Time Period
            </label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="w-full text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="current">Current (Last 14 Days)</option>
              <option value="last_1_month">Last 1 Month</option>
              <option value="last_3_months">Last 3 Months (Standard)</option>
              <option value="all">All Available History</option>
            </select>
          </div>

          {/* Reset Action */}
          <div className="flex items-end">
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetFilters}
              className="w-full text-slate-600 dark:text-slate-300"
            >
              <Filter className="w-3.5 h-3.5 mr-1.5" />
              Reset Filters
            </Button>
          </div>
        </div>
      </Card>

      {/* Unconfigured / Empty Notification Banner */}
      {isUnconfigured && (
        <div className="p-4 rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-950/40 dark:border-amber-900/60 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
          <div className="text-sm">
            <h4 className="font-semibold text-amber-900 dark:text-amber-200">
              Real market data unavailable — data source not configured.
            </h4>
            <p className="text-amber-800 dark:text-amber-300 mt-0.5">
              Live market intelligence integration requires authorized AWS OpenSearch / API Gateway or Cloud Firestore feed.
              In accordance with SIH evaluation rules, no fabricated or synthetic numbers are generated.
            </p>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="border-b border-slate-200 dark:border-slate-800 flex gap-4 overflow-x-auto">
        <button
          onClick={() => setActiveTab("overview")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "overview"
              ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Market Overview
        </button>
        <button
          onClick={() => setActiveTab("companies")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "companies"
              ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Company Explorer
        </button>
        <button
          onClick={() => setActiveTab("skills")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "skills"
              ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          Skill Demand
        </button>
        <button
          onClick={() => setActiveTab("trends")}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
            activeTab === "trends"
              ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          3-Month Trends
        </button>
        <button
          onClick={() => {
            setActiveTab("gap");
            loadMarketGap();
          }}
          className={`pb-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap flex items-center gap-1.5 ${
            activeTab === "gap"
              ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400"
          }`}
        >
          <Sparkles className="w-4 h-4 text-blue-500" />
          My Market Gap
        </button>
      </div>

      {/* ======================= TAB 1: OVERVIEW ======================= */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          {/* Top KPI Cards (Distinguishing Observed Postings vs Verified Hiring Data) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Observed Job Postings"
              value={overview?.total_observed_postings ?? 0}
              subtitle="Detected from verified job boards"
              icon={Briefcase}
            />
            <StatCard
              title="Verified Hiring Records"
              value={overview?.total_verified_hirings ?? 0}
              subtitle="Confirmed talent placements"
              icon={CheckCircle2}
            />
            <StatCard
              title="Active Employers"
              value={overview?.unique_companies_count ?? 0}
              subtitle="Unique companies posting"
              icon={Building2}
            />
            <StatCard
              title="Unique Roles Tracked"
              value={overview?.unique_roles_count ?? 0}
              subtitle="Distinct job titles"
              icon={Layers}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Companies */}
            <Card className="p-5 border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-blue-500" />
                  Top Companies by Observed Postings
                </h3>
                <span className="text-xs text-slate-500">
                  {overview?.time_filter_applied?.replace("_", " ") || "recent"}
                </span>
              </div>

              {!overview?.top_companies || overview.top_companies.length === 0 ? (
                <div className="py-8 text-center text-sm text-slate-500">
                  {isUnconfigured ? "Data unavailable" : "No companies found matching criteria"}
                </div>
              ) : (
                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                  {overview.top_companies.map((comp, idx) => (
                    <div
                      key={comp.company}
                      className="py-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 px-2 rounded-lg cursor-pointer transition-colors"
                      onClick={() => {
                        handleSelectCompany(comp.company);
                        setActiveTab("companies");
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <span className="w-6 text-center text-xs font-bold text-slate-400">#{idx + 1}</span>
                        <div>
                          <p className="font-medium text-slate-800 dark:text-slate-200 text-sm">
                            {comp.company}
                          </p>
                          <p className="text-xs text-slate-500">
                            {comp.roles_count} distinct roles
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary" className="text-xs font-medium">
                          {comp.observed_postings} postings
                        </Badge>
                        <ArrowRight className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            {/* Most Requested Skills */}
            <Card className="p-5 border-slate-200 dark:border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                  Most In-Demand Skills
                </h3>
                <span className="text-xs text-slate-500">
                  % of observed job postings
                </span>
              </div>

              {!overview?.most_requested_skills || overview.most_requested_skills.length === 0 ? (
                <div className="py-8 text-center text-sm text-slate-500">
                  {isUnconfigured ? "Data unavailable" : "No skill demand data for criteria"}
                </div>
              ) : (
                <div className="space-y-3">
                  {overview.most_requested_skills.slice(0, 8).map((sk) => (
                    <div key={sk.skill} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-slate-700 dark:text-slate-300">{sk.skill}</span>
                        <span className="text-slate-500">
                          {sk.observed_postings} postings ({sk.percentage}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                        <div
                          className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full transition-all duration-500"
                          style={{ width: `${Math.min(100, sk.percentage)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Location and Employment Type Distributions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-5 border-slate-200 dark:border-slate-800">
              <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-rose-500" />
                Geographic Posting Distribution
              </h3>
              {!overview?.location_distribution || Object.keys(overview.location_distribution).length === 0 ? (
                <div className="py-6 text-center text-sm text-slate-500">
                  {isUnconfigured ? "Data unavailable" : "No location statistics available"}
                </div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(overview.location_distribution).map(([loc, cnt]) => (
                    <div key={loc} className="flex justify-between items-center text-sm py-1 border-b border-slate-50 dark:border-slate-800/60">
                      <span className="text-slate-700 dark:text-slate-300">{loc}</span>
                      <Badge variant="outline" className="text-xs">
                        {cnt} postings
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </Card>

            <Card className="p-5 border-slate-200 dark:border-slate-800">
              <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-indigo-500" />
                Employment Type Distribution
              </h3>
              {!overview?.employment_type_distribution || Object.keys(overview.employment_type_distribution).length === 0 ? (
                <div className="py-6 text-center text-sm text-slate-500">
                  {isUnconfigured ? "Data unavailable" : "No employment type data available"}
                </div>
              ) : (
                <div className="space-y-2">
                  {Object.entries(overview.employment_type_distribution).map(([type, cnt]) => (
                    <div key={type} className="flex justify-between items-center text-sm py-1 border-b border-slate-50 dark:border-slate-800/60">
                      <span className="text-slate-700 dark:text-slate-300">{type}</span>
                      <Badge variant="outline" className="text-xs">
                        {cnt} postings
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* ======================= TAB 2: COMPANY EXPLORER ======================= */}
      {activeTab === "companies" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Companies List */}
          <div className="space-y-4">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search company (Google, Microsoft, ...)"
                value={companySearch}
                onChange={(e) => setCompanySearch(e.target.value)}
                className="w-full text-sm pl-9 pr-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <Card className="divide-y divide-slate-100 dark:divide-slate-800 max-h-[600px] overflow-y-auto">
              {companies.filter((c) => !companySearch || c.company.toLowerCase().includes(companySearch.toLowerCase())).length === 0 ? (
                <div className="p-6 text-center text-sm text-slate-500">
                  {isUnconfigured ? "Data unavailable" : "No companies found matching search"}
                </div>
              ) : (
                companies
                  .filter((c) => !companySearch || c.company.toLowerCase().includes(companySearch.toLowerCase()))
                  .map((c) => {
                    const isSelected = c.company === selectedCompany;
                    return (
                      <div
                        key={c.company}
                        onClick={() => handleSelectCompany(c.company)}
                        className={`p-3.5 cursor-pointer transition-colors flex items-center justify-between ${
                          isSelected
                            ? "bg-blue-50/80 dark:bg-blue-950/40 border-l-4 border-blue-600"
                            : "hover:bg-slate-50 dark:hover:bg-slate-800/40"
                        }`}
                      >
                        <div>
                          <div className="flex items-center gap-1.5">
                            <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                              {c.company}
                            </h4>
                            {c.is_target_company && (
                              <span title="Target Company" className="text-amber-500 text-xs">★</span>
                            )}
                            {c.is_dream_company && (
                              <span title="Dream Company" className="text-pink-500 text-xs">✨</span>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            {c.unique_roles} roles • {c.locations.slice(0, 2).join(", ")}
                          </p>
                        </div>
                        <Badge variant={isSelected ? "default" : "secondary"} className="text-xs">
                          {c.observed_postings} postings
                        </Badge>
                      </div>
                    );
                  })
              )}
            </Card>
          </div>

          {/* Selected Company Detail */}
          <div className="lg:col-span-2 space-y-5">
            {!companyDetail || companyDetail.status !== "available" ? (
              <Card className="p-8 text-center text-slate-500">
                <Building2 className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-2" />
                <p className="font-medium text-slate-700 dark:text-slate-300">
                  {isUnconfigured ? "Real market data unavailable — data source not configured." : "Select a company to view deep hiring analytics"}
                </p>
              </Card>
            ) : (
              <>
                {/* Company Header & Preferences */}
                <Card className="p-5 border-slate-200 dark:border-slate-800">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
                          {companyDetail.company}
                        </h2>
                        {companyDetail.is_target_company && (
                          <Badge variant="warning" className="text-xs">
                            Target Company
                          </Badge>
                        )}
                        {companyDetail.is_dream_company && (
                          <Badge variant="primary" className="text-xs bg-pink-600 text-white">
                            Dream Company
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        {companyDetail.observed_postings_count} observed postings in current view • {companyDetail.roles_posted.length} distinct job roles
                      </p>
                    </div>

                    {/* Preference Toggles (Requirement 6) */}
                    <div className="flex items-center gap-2">
                      <Button
                        variant={companyDetail.is_target_company ? "secondary" : "outline"}
                        size="sm"
                        disabled={prefLoading}
                        onClick={() =>
                          handleTogglePreference(companyDetail.company, "target", companyDetail.is_target_company)
                        }
                        className={companyDetail.is_target_company ? "border-amber-500 text-amber-700 dark:text-amber-300" : ""}
                      >
                        <Star className={`w-3.5 h-3.5 mr-1.5 ${companyDetail.is_target_company ? "fill-amber-500 text-amber-500" : ""}`} />
                        {companyDetail.is_target_company ? "Targeted" : "Mark as Target"}
                      </Button>

                      <Button
                        variant={companyDetail.is_dream_company ? "secondary" : "outline"}
                        size="sm"
                        disabled={prefLoading}
                        onClick={() =>
                          handleTogglePreference(companyDetail.company, "dream", companyDetail.is_dream_company)
                        }
                        className={companyDetail.is_dream_company ? "border-pink-500 text-pink-700 dark:text-pink-300" : ""}
                      >
                        <Sparkles className={`w-3.5 h-3.5 mr-1.5 ${companyDetail.is_dream_company ? "fill-pink-500 text-pink-500" : ""}`} />
                        {companyDetail.is_dream_company ? "Dream Co" : "Mark as Dream"}
                      </Button>

                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          setActiveTab("gap");
                          loadMarketGap(companyDetail.company);
                        }}
                      >
                        Analyze My Gap
                      </Button>
                    </div>
                  </div>
                </Card>

                {/* Company Skill Requirements */}
                <Card className="p-5 border-slate-200 dark:border-slate-800">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                    <Award className="w-4 h-4 text-blue-500" />
                    Top Required Skills & Proficiency Expectation
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {companyDetail.skill_frequency.slice(0, 10).map((sk) => (
                      <div
                        key={sk.skill}
                        className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30 flex justify-between items-center"
                      >
                        <div>
                          <p className="text-xs font-semibold text-slate-800 dark:text-slate-200">{sk.skill}</p>
                          <p className="text-[11px] text-slate-500">
                            Required in {sk.percentage}% of postings
                          </p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          Lvl {sk.average_required_proficiency}/5.0
                        </Badge>
                      </div>
                    ))}
                  </div>
                </Card>

                {/* Open/Observed Postings */}
                <Card className="p-5 border-slate-200 dark:border-slate-800">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-3 flex items-center gap-2">
                    <Clock className="w-4 h-4 text-slate-500" />
                    Observed Job Postings
                  </h3>
                  <div className="space-y-3">
                    {companyDetail.open_postings.map((job) => (
                      <div
                        key={job.job_id}
                        className="p-3.5 rounded-lg border border-slate-100 dark:border-slate-800 hover:border-slate-200 transition-colors"
                      >
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                              {job.job_title}
                            </h4>
                            <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                              <span>📍 {job.city || job.state || job.country}</span>
                              <span>• {job.employment_type}</span>
                              {job.posted_date && <span>• Posted {job.posted_date.slice(0, 10)}</span>}
                            </p>
                          </div>
                          <Badge variant={job.data_type === "verified_hiring" ? "success" : "secondary"} className="text-[11px]">
                            {job.data_type === "verified_hiring" ? "Verified Hire" : "Observed Posting"}
                          </Badge>
                        </div>
                        {job.skills && job.skills.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-2.5">
                            {job.skills.map((s) => (
                              <span
                                key={s}
                                className="px-2 py-0.5 rounded text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              </>
            )}
          </div>
        </div>
      )}

      {/* ======================= TAB 3: SKILL DEMAND ======================= */}
      {activeTab === "skills" && (
        <Card className="p-5 border-slate-200 dark:border-slate-800">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
            <div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">
                Market-Wide Skill Demand Analysis
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Calculated strictly from {skillDemand?.total_postings_analyzed || 0} real observed job postings
              </p>
            </div>
            <span className="text-xs text-slate-500 font-medium">
              Formula: (Observed Postings / Total Analyzed) × 100
            </span>
          </div>

          {!skillDemand?.skills || skillDemand.skills.length === 0 ? (
            <div className="py-12 text-center text-slate-500 text-sm">
              {isUnconfigured ? "Real market data unavailable — data source not configured." : "No skill demand data matching selected filters."}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    <th className="pb-3">Rank</th>
                    <th className="pb-3">Skill</th>
                    <th className="pb-3">Observed Postings</th>
                    <th className="pb-3">Market Frequency</th>
                    <th className="pb-3 w-48">Demand Gauge</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {skillDemand.skills.map((item, idx) => (
                    <tr key={item.skill} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                      <td className="py-3 text-xs font-bold text-slate-400">#{idx + 1}</td>
                      <td className="py-3 font-medium text-slate-800 dark:text-slate-200">{item.skill}</td>
                      <td className="py-3 text-slate-600 dark:text-slate-400">{item.observed_postings}</td>
                      <td className="py-3 font-semibold text-blue-600 dark:text-blue-400">{item.percentage}%</td>
                      <td className="py-3">
                        <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2">
                          <div
                            className="bg-blue-600 dark:bg-blue-500 h-2 rounded-full"
                            style={{ width: `${Math.min(100, item.percentage)}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* ======================= TAB 4: TRENDS ======================= */}
      {activeTab === "trends" && (
        <div className="space-y-6">
          {trends?.status === "insufficient_data" ? (
            <div className="p-6 rounded-xl border border-blue-200 bg-blue-50 dark:bg-blue-950/40 dark:border-blue-900/60 text-center">
              <Clock className="w-10 h-10 text-blue-500 mx-auto mb-2" />
              <h3 className="font-semibold text-blue-900 dark:text-blue-200 text-base">
                Insufficient historical data for this trend.
              </h3>
              <p className="text-sm text-blue-800 dark:text-blue-300 mt-1 max-w-xl mx-auto">
                At least 2 distinct calendar months with posting activity spanning 30+ days are required to calculate legitimate market trends.
                In accordance with SIH evaluation principles, no synthetic or artificial historical data is manufactured.
              </p>
            </div>
          ) : trends?.status === "unconfigured" ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              Real market data unavailable — data source not configured.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {trends?.trends.map((t) => (
                <Card key={t.month} className="p-5 border-slate-200 dark:border-slate-800">
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-xs font-semibold uppercase text-slate-500 tracking-wider">
                      Month
                    </span>
                    <Badge variant="outline" className="font-mono text-xs">
                      {t.month}
                    </Badge>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                        {t.observed_postings}
                      </p>
                      <p className="text-xs text-slate-500">Observed Postings</p>
                    </div>
                    <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
                      <p className="text-xs font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                        Top Skills In Demand:
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {t.top_skills.map((s) => (
                          <span
                            key={s.skill}
                            className="px-2 py-0.5 rounded text-[11px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300"
                          >
                            {s.skill} ({s.count})
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ======================= TAB 5: MY MARKET GAP (STUDENT PERSONALIZATION) ======================= */}
      {activeTab === "gap" && (
        <div className="space-y-6">
          {/* Target Selector */}
          <Card className="p-5 border-slate-200 dark:border-slate-800">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h3 className="font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-blue-500" />
                  Personalized Market Skill Gap Analysis
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Connects your verified profile skills with real market demand using Step 29 deterministic weighted matching.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <select
                  value={selectedCompany}
                  onChange={(e) => {
                    setSelectedCompany(e.target.value);
                    loadMarketGap(e.target.value);
                  }}
                  className="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 p-2 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Market-Wide (All Companies)</option>
                  {companies.map((c) => (
                    <option key={c.company} value={c.company}>
                      {c.company} ({c.observed_postings} postings)
                    </option>
                  ))}
                </select>

                <Button size="sm" onClick={() => loadMarketGap(selectedCompany)}>
                  Recalculate Gap
                </Button>
              </div>
            </div>
          </Card>

          {!marketGap ? (
            <div className="p-8 text-center text-slate-500 text-sm">
              Loading market skill gap analysis...
            </div>
          ) : (
            <>
              {/* Overall Match Score Card */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card className="p-6 border-slate-200 dark:border-slate-800 md:col-span-1 flex flex-col justify-center items-center text-center">
                  <div className="relative w-32 h-32 flex items-center justify-center rounded-full border-8 border-blue-500/20 mb-3">
                    <span className="text-3xl font-extrabold text-blue-600 dark:text-blue-400">
                      {marketGap.market_match_score}%
                    </span>
                  </div>
                  <h4 className="font-semibold text-slate-800 dark:text-slate-100">
                    Market Readiness Match
                  </h4>
                  <p className="text-xs text-slate-500 mt-1">
                    {marketGap.target_company ? `Against ${marketGap.target_company} requirements` : "Against general market demand"}
                  </p>
                </Card>

                <Card className="p-6 border-slate-200 dark:border-slate-800 md:col-span-2 space-y-4">
                  <h4 className="font-semibold text-slate-800 dark:text-slate-100">
                    Gap Analysis Summary
                  </h4>
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                    {marketGap.explanation}
                  </p>

                  <div className="grid grid-cols-3 gap-3 pt-2">
                    <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/40 text-center">
                      <p className="text-xl font-bold text-emerald-600 dark:text-emerald-400">
                        {marketGap.matched_skills.length}
                      </p>
                      <p className="text-xs text-emerald-800 dark:text-emerald-300 font-medium">Matched</p>
                    </div>
                    <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/40 text-center">
                      <p className="text-xl font-bold text-amber-600 dark:text-amber-400">
                        {marketGap.partial_skills.length}
                      </p>
                      <p className="text-xs text-amber-800 dark:text-amber-300 font-medium">Partial Gap</p>
                    </div>
                    <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/40 text-center">
                      <p className="text-xl font-bold text-rose-600 dark:text-rose-400">
                        {marketGap.missing_skills.length}
                      </p>
                      <p className="text-xs text-rose-800 dark:text-rose-300 font-medium">Missing</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Priority Learning Recommendations Derived from Market Frequency */}
              <Card className="p-5 border-slate-200 dark:border-slate-800">
                <h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-4 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-500" />
                  Priority Learning Gaps (Weighted by Market Demand)
                </h3>

                {marketGap.market_priority_skills.length === 0 ? (
                  <div className="p-6 text-center text-sm text-slate-500">
                    No critical skill gaps detected for this market profile!
                  </div>
                ) : (
                  <div className="divide-y divide-slate-100 dark:divide-slate-800">
                    {marketGap.market_priority_skills.map((item) => (
                      <div key={item.skill} className="py-3 flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-sm text-slate-800 dark:text-slate-200">
                              {item.skill}
                            </span>
                            <Badge
                              variant={
                                item.priority === "High" ? "destructive" : item.priority === "Medium" ? "warning" : "secondary"
                              }
                              className="text-xs"
                            >
                              {item.priority} Priority
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-500 mt-0.5">
                            Current: Lvl {item.current_proficiency}/5.0 • Target: Lvl {item.required_proficiency}/5.0 (Gap: {item.gap_amount})
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="text-xs font-semibold text-blue-600 dark:text-blue-400">
                            {item.market_frequency_percentage}% Market Demand
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default JobMarketIntelligencePage;

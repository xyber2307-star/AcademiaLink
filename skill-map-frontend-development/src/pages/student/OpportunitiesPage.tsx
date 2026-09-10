import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Briefcase,
  Building2,
  MapPin,
  ArrowRight,
  Filter,
  Sparkles,
} from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { PageSkeleton } from "../../components/ui/Skeleton";
import { PageHeader } from "../../components/ui/PageHeader";
import { studentService } from "../../services/studentService";
import type { Opportunity } from "../../types";

export default function OpportunitiesPage() {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [filterType, setFilterType] = useState<string>("All");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOpportunities();
  }, []);

  const loadOpportunities = async () => {
    try {
      setLoading(true);
      const data = await studentService.getOpportunities();
      setOpportunities(data || []);
    } catch (err) {
      console.error("Failed to load opportunities", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <PageSkeleton />;

  const filtered = opportunities.filter((o) => {
    if (filterType === "All") return true;
    return o.type.toLowerCase() === filterType.toLowerCase();
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Opportunity Marketplace"
        description="Discover internships and full-time positions with deterministic skill matching and gap analysis tailored to your competencies."
      />

      {/* Filter bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-white p-3 shadow-sm ring-1 ring-slate-200">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-semibold text-slate-700">Filter by Type:</span>
          {["All", "Internship", "Full-time"].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`rounded-xl px-3 py-1.5 text-xs font-medium transition ${
                filterType === t
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-slate-50 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <span className="text-xs text-slate-500 font-medium">
          Showing {filtered.length} opportunities
        </span>
      </div>

      {/* Opportunities Grid */}
      <div className="grid gap-4 md:grid-cols-2">
        {filtered.map((opp) => {
          const matchScore = opp.matchScore || 70;
          return (
            <Card
              key={opp.id}
              className="flex flex-col justify-between transition hover:border-indigo-300 hover:shadow-md"
            >
              <CardBody className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white shadow">
                      {opp.logo || opp.company.slice(0, 2).toUpperCase()}
                    </span>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">{opp.title}</h3>
                      <p className="text-xs font-semibold text-indigo-600">{opp.company}</p>
                    </div>
                  </div>

                  <span
                    className={`rounded-xl px-2.5 py-1 text-xs font-bold ring-1 ring-inset ${
                      matchScore >= 80
                        ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                        : matchScore >= 60
                        ? "bg-amber-50 text-amber-700 ring-amber-200"
                        : "bg-rose-50 text-rose-700 ring-rose-200"
                    }`}
                  >
                    {matchScore}% Match
                  </span>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span className="inline-flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {opp.location} ({opp.mode})
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="h-3.5 w-3.5" />
                    {opp.type}
                  </span>
                  <span className="font-semibold text-slate-700">{opp.stipend}</span>
                </div>

                {opp.description && (
                  <p className="mt-3 line-clamp-2 text-xs text-slate-600 leading-relaxed">
                    {opp.description}
                  </p>
                )}

                <div className="mt-4">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    Required Skills
                  </p>
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {opp.skills.map((skill) => (
                      <span
                        key={skill}
                        className="rounded-lg bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </CardBody>

              <div className="border-t border-slate-100 bg-slate-50/50 px-5 py-3 flex items-center justify-between">
                <span className="text-[11px] text-slate-400 font-medium">
                  {opp.applicants || 0} applicants
                </span>
                <Link to={`/student/opportunities/${opp.id}`}>
                  <Button
                    size="sm"
                    variant="outline"
                    icon={<ArrowRight className="h-3.5 w-3.5" />}
                  >
                    View Match Analysis
                  </Button>
                </Link>
              </div>
            </Card>
          );
        })}
        {filtered.length === 0 && (
          <div className="col-span-2 py-12 text-center text-sm text-slate-500">
            No opportunities found matching the selected filter.
          </div>
        )}
      </div>
    </div>
  );
}

import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, PolarAngleAxis, PolarGrid,
  PolarRadiusAxis, Radar, RadarChart, RadialBar, RadialBarChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { Skill, SkillGap, Application } from "../../types";

export const CHART_COLORS = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

const tooltipStyle = { borderRadius: 12, border: "1px solid #e2e8f0", boxShadow: "0 10px 30px -10px rgba(15,23,42,.2)", fontSize: 12 };

/** Skill distribution radar — grouped by category average */
export function SkillDistributionChart({ skills }: { skills: Skill[] }) {
  const cats = ["Technical", "Domain", "Tools", "Soft"] as const;
  const data = cats.map((c) => {
    const s = skills.filter((k) => k.category === c);
    const avg = (key: "score" | "required") => Math.round(s.reduce((a, k) => a + k[key], 0) / Math.max(1, s.length));
    return { category: c, you: avg("score"), industry: avg("required") };
  });
  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={data} outerRadius="75%">
        <PolarGrid stroke="#e2e8f0" />
        <PolarAngleAxis dataKey="category" tick={{ fontSize: 12, fill: "#475569" }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
        <Radar name="Industry expected" dataKey="industry" stroke="#94a3b8" fill="#cbd5e1" fillOpacity={0.35} />
        <Radar name="Your score" dataKey="you" stroke="#4f46e5" fill="#6366f1" fillOpacity={0.45} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Tooltip contentStyle={tooltipStyle} />
      </RadarChart>
    </ResponsiveContainer>
  );
}

/** Skill gap horizontal bars — current vs required */
export function SkillGapChart({ gaps, height = 300 }: { gaps: SkillGap[]; height?: number }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={gaps} layout="vertical" margin={{ left: 8, right: 16 }} barGap={2}>
        <CartesianGrid horizontal={false} stroke="#f1f5f9" />
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="skill" width={110} tick={{ fontSize: 11, fill: "#334155" }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "#f8fafc" }} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar name="Current" dataKey="current" fill="#4f46e5" radius={[0, 6, 6, 0]} barSize={10} />
        <Bar name="Required" dataKey="required" fill="#cbd5e1" radius={[0, 6, 6, 0]} barSize={10} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/** Career readiness trend area */
export function ReadinessTrendChart({ data }: { data: { month: string; readiness: number; skillScore: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <AreaChart data={data} margin={{ left: -20, right: 8, top: 8 }}>
        <defs>
          <linearGradient id="gR" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4f46e5" stopOpacity={0.35} /><stop offset="100%" stopColor="#4f46e5" stopOpacity={0} /></linearGradient>
          <linearGradient id="gS" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#10b981" stopOpacity={0.3} /><stop offset="100%" stopColor="#10b981" stopOpacity={0} /></linearGradient>
        </defs>
        <CartesianGrid vertical={false} stroke="#f1f5f9" />
        <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
        <Tooltip contentStyle={tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Area name="Career readiness" type="monotone" dataKey="readiness" stroke="#4f46e5" strokeWidth={2.5} fill="url(#gR)" />
        <Area name="Skill score" type="monotone" dataKey="skillScore" stroke="#10b981" strokeWidth={2.5} fill="url(#gS)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/** Career readiness radial breakdown */
export function ReadinessRadialChart({ data }: { data: { name: string; value: number }[] }) {
  const d = data.map((x, i) => ({ ...x, fill: CHART_COLORS[i % CHART_COLORS.length] }));
  return (
    <ResponsiveContainer width="100%" height={240}>
      <RadialBarChart innerRadius="30%" outerRadius="100%" data={d} startAngle={90} endAngle={-270}>
        <RadialBar dataKey="value" background={{ fill: "#f1f5f9" }} cornerRadius={8} />
        <Tooltip contentStyle={tooltipStyle} />
      </RadialBarChart>
    </ResponsiveContainer>
  );
}

/** Application status donut */
export function ApplicationStatusChart({ applications }: { applications: Application[] }) {
  const statuses = ["Applied", "Shortlisted", "Interview", "Offered", "Rejected"] as const;
  const colors: Record<string, string> = { Applied: "#94a3b8", Shortlisted: "#0ea5e9", Interview: "#f59e0b", Offered: "#10b981", Rejected: "#ef4444" };
  const data = statuses.map((s) => ({ name: s, value: applications.filter((a) => a.status === s).length })).filter((x) => x.value > 0);
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={60} outerRadius={90} paddingAngle={3} cornerRadius={6}>
          {data.map((e) => <Cell key={e.name} fill={colors[e.name]} />)}
        </Pie>
        <Tooltip contentStyle={tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 12 }} iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  );
}

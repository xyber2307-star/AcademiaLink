import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  Award,
  BadgeCheck,
  CheckCircle2,
  ChevronRight,
  RotateCcw,
  Sparkles,
  ArrowRight,
  Code2,
  Layers,
  Cpu,
} from "lucide-react";
import { Card, CardBody, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { ProgressBar } from "../../components/ui/Progress";
import { studentService } from "../../services/studentService";
import { quizService, AssessmentHistoryItem } from "../../services/quizService";

interface Question {
  id: string;
  question: string;
  options: string[];
  difficulty: number;
}

interface AssessmentResult {
  skillName: string;
  category: string;
  proficiency: number;
  level: string;
  scorePercentage: number;
  totalQuestions: number;
  correctCount: number;
  explanation: string;
  skill: any;
}

const AVAILABLE_SKILLS = [
  {
    id: "python",
    name: "Python",
    category: "Technical" as const,
    icon: Code2,
    description: "Core syntax, data structures, GIL, memory model, and generators",
    questionsCount: 5,
  },
  {
    id: "react",
    name: "React",
    category: "Technical" as const,
    icon: Layers,
    description: "Virtual DOM reconciliation, hooks, memoization, and lifecycle",
    questionsCount: 5,
  },
  {
    id: "general",
    name: "Software Engineering",
    category: "Technical" as const,
    icon: Cpu,
    description: "RESTful architecture, Git, databases, indexing, and containerization",
    questionsCount: 5,
  },
];

export default function SkillAssessmentPage() {
  const [selectedSkillId, setSelectedSkillId] = useState<string>("python");
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [loadingQuestions, setLoadingQuestions] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<AssessmentHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const selectedSkill = AVAILABLE_SKILLS.find((s) => s.id === selectedSkillId) || AVAILABLE_SKILLS[0];

  const loadHistory = async () => {
    try {
      setLoadingHistory(true);
      const h = await quizService.getHistory();
      setHistory(h || []);
    } catch (e) {
      console.warn("Could not load assessment history:", e);
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  useEffect(() => {
    loadQuestions(selectedSkillId);
  }, [selectedSkillId]);

  const loadQuestions = async (skillId: string) => {
    try {
      setLoadingQuestions(true);
      setError(null);
      setResult(null);
      setAnswers({});
      setCurrentIdx(0);
      const data = await studentService.getAssessmentQuestions(skillId);
      setQuestions(data || []);
    } catch (err: any) {
      console.error("Failed to load questions", err);
      setError("Unable to load questions from assessment service.");
    } finally {
      setLoadingQuestions(false);
    }
  };

  const handleSelectOption = (questionId: string, optionIndex: number) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionIndex,
    }));
  };

  const handleSubmit = async () => {
    if (questions.length === 0) return;
    try {
      setSubmitting(true);
      setError(null);

      const submissionPayload = {
        skillName: selectedSkill.name,
        category: selectedSkill.category,
        answers: Object.entries(answers).map(([questionId, selectedOption]) => ({
          questionId,
          selectedOption,
        })),
      };

      const res = await studentService.submitAssessment(submissionPayload);
      setResult(res);
      loadHistory();
    } catch (err: any) {
      console.error("Assessment submission error:", err);
      setError(err?.message || "Failed to submit assessment.");
    } finally {
      setSubmitting(false);
    }
  };

  const answeredCount = Object.keys(answers).length;
  const currentQ = questions[currentIdx];
  const progressPercent = questions.length > 0 ? Math.round(((currentIdx + 1) / questions.length) * 100) : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Skill Assessment"
        description="Verify your skills with standardized, deterministic evaluations to boost your verified skill score and employer readiness."
        actions={
          <Link to="/student/profile">
            <Button variant="outline" size="sm">
              View Profile
            </Button>
          </Link>
        }
      />

      {/* Skill Track Picker */}
      <div className="grid gap-4 sm:grid-cols-3">
        {AVAILABLE_SKILLS.map((track) => {
          const isSelected = track.id === selectedSkillId;
          const Icon = track.icon;
          return (
            <button
              key={track.id}
              onClick={() => {
                if (selectedSkillId !== track.id) {
                  setSelectedSkillId(track.id);
                }
              }}
              className={`flex flex-col text-left p-4 rounded-2xl border transition ${
                isSelected
                  ? "border-indigo-600 bg-indigo-50/50 shadow-sm ring-2 ring-indigo-500/20"
                  : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                    isSelected ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                </span>
                {isSelected && (
                  <Badge tone="indigo">
                    Active Track
                  </Badge>
                )}
              </div>
              <p className="mt-3 font-semibold text-slate-900">{track.name}</p>
              <p className="mt-1 text-xs text-slate-500 line-clamp-2">{track.description}</p>
              <div className="mt-3 flex items-center gap-2 text-xs font-medium text-slate-500">
                <span>{track.questionsCount} Questions</span>
                <span>•</span>
                <span>Deterministic Scoring</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Result Card if submitted */}
      {result ? (
        <Card className="overflow-hidden border-emerald-200 bg-gradient-to-b from-emerald-50/40 to-white">
          <CardBody className="p-8 text-center sm:p-10">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-600 ring-8 ring-emerald-50">
              <Award className="h-8 w-8" />
            </div>

            <Badge tone="emerald" className="mt-4">
              <BadgeCheck className="h-3.5 w-3.5" /> Assessment Verified
            </Badge>

            <h2 className="mt-3 text-2xl font-bold text-slate-900">
              {result.skillName}: {result.level} (Level {result.proficiency}/5)
            </h2>

            <p className="mx-auto mt-2 max-w-lg text-sm text-slate-600">
              {result.explanation}
            </p>

            <div className="mx-auto mt-6 grid max-w-md grid-cols-3 gap-3">
              <div className="rounded-xl bg-white p-3 shadow-sm ring-1 ring-slate-200">
                <p className="text-[11px] font-medium text-slate-500">Score</p>
                <p className="text-xl font-bold text-slate-900">{result.scorePercentage}%</p>
              </div>
              <div className="rounded-xl bg-white p-3 shadow-sm ring-1 ring-slate-200">
                <p className="text-[11px] font-medium text-slate-500">Correct</p>
                <p className="text-xl font-bold text-emerald-600">
                  {result.correctCount}/{result.totalQuestions}
                </p>
              </div>
              <div className="rounded-xl bg-white p-3 shadow-sm ring-1 ring-slate-200">
                <p className="text-[11px] font-medium text-slate-500">Proficiency</p>
                <p className="text-xl font-bold text-indigo-600">Level {result.proficiency}</p>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Button
                variant="outline"
                icon={<RotateCcw className="h-4 w-4" />}
                onClick={() => loadQuestions(selectedSkillId)}
              >
                Retake Assessment
              </Button>
              <Link to="/student/profile">
                <Button icon={<ArrowRight className="h-4 w-4" />}>
                  View Updated Profile
                </Button>
              </Link>
            </div>
          </CardBody>
        </Card>
      ) : (
        /* Assessment Runner */
        <Card>
          <CardHeader
            title={`${selectedSkill.name} Competency Assessment`}
            subtitle={`Question ${currentIdx + 1} of ${questions.length} • Difficulty: Level ${currentQ?.difficulty || 1}`}
            action={
              <Badge tone="slate">
                {answeredCount}/{questions.length} Answered
              </Badge>
            }
          />
          <div className="px-6">
            <ProgressBar value={progressPercent} tone="indigo" />
          </div>

          <CardBody className="space-y-6 pt-6">
            {error && (
              <div className="rounded-xl bg-rose-50 p-3 text-xs text-rose-700">
                {error}
              </div>
            )}

            {loadingQuestions ? (
              <div className="py-12 text-center text-sm text-slate-500">
                Loading questions for {selectedSkill.name}...
              </div>
            ) : currentQ ? (
              <div className="space-y-5">
                <div className="rounded-2xl bg-slate-50 p-5 ring-1 ring-slate-200/60">
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                    Question {currentIdx + 1}
                  </span>
                  <h3 className="mt-1 text-base font-semibold text-slate-900 leading-relaxed">
                    {currentQ.question}
                  </h3>
                </div>

                <div className="space-y-2.5">
                  {currentQ.options.map((option, idx) => {
                    const isSelected = answers[currentQ.id] === idx;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleSelectOption(currentQ.id, idx)}
                        className={`flex w-full items-center justify-between rounded-xl border p-4 text-left text-sm transition ${
                          isSelected
                            ? "border-indigo-600 bg-indigo-50/70 font-medium text-indigo-950 ring-2 ring-indigo-500/20"
                            : "border-slate-200 bg-white text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold ${
                              isSelected
                                ? "bg-indigo-600 text-white"
                                : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {String.fromCharCode(65 + idx)}
                          </span>
                          <span>{option}</span>
                        </div>
                        {isSelected && <CheckCircle2 className="h-5 w-5 text-indigo-600 shrink-0" />}
                      </button>
                    );
                  })}
                </div>

                {/* Navigation Controls */}
                <div className="flex items-center justify-between border-t border-slate-100 pt-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    disabled={currentIdx === 0}
                    onClick={() => setCurrentIdx((i) => Math.max(0, i - 1))}
                  >
                    Previous
                  </Button>

                  <div className="flex gap-2">
                    {currentIdx < questions.length - 1 ? (
                      <Button
                        size="sm"
                        icon={<ChevronRight className="h-4 w-4" />}
                        onClick={() => setCurrentIdx((i) => Math.min(questions.length - 1, i + 1))}
                      >
                        Next Question
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="primary"
                        loading={submitting}
                        disabled={answeredCount < questions.length}
                        icon={<Sparkles className="h-4 w-4" />}
                        onClick={handleSubmit}
                      >
                        Submit Assessment
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-sm text-slate-500">
                No questions available.
              </div>
            )}
          </CardBody>
        </Card>
      )}

      {/* Assessment History Section */}
      <Card>
        <CardHeader
          title="My Assessment History"
          subtitle="Record of verified competency evaluations and deterministic scoring."
        />
        <CardBody>
          {loadingHistory ? (
            <div className="py-8 text-center text-xs text-slate-500">Loading history...</div>
          ) : history.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-500">
              No previous assessment records found. Complete a skill quiz above to record your score.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3">Skill</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Score %</th>
                    <th className="px-4 py-3">Assessed Proficiency</th>
                    <th className="px-4 py-3">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {history.map((h) => (
                    <tr key={h.assessment_id} className="hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-semibold text-slate-900">{h.skill_name}</td>
                      <td className="px-4 py-3">{h.category}</td>
                      <td className="px-4 py-3 font-bold text-indigo-600">{h.score_percentage}%</td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded-full font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          Level {h.assessed_proficiency} / 5
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-400">
                        {new Date(h.timestamp).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

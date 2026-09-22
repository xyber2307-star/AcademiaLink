import React, { useState, useEffect } from "react";
import {
  X,
  Award,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Clock,
  ShieldCheck,
  RotateCcw,
} from "lucide-react";
import { quizService, QuizDetail, QuizResult } from "../../services/quizService";

interface SkillQuizModalProps {
  skillName: string;
  category?: string;
  onClose: () => void;
  onAssessmentCompleted?: (result: QuizResult) => void;
}

export const SkillQuizModal: React.FC<SkillQuizModalProps> = ({
  skillName,
  category = "Technical",
  onClose,
  onAssessmentCompleted,
}) => {
  const [loading, setLoading] = useState(true);
  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    quizService
      .getQuiz(skillName)
      .then((data) => setQuiz(data))
      .catch((err) => setError(err.message || "Failed to load quiz."))
      .finally(() => setLoading(false));
  }, [skillName]);

  const handleSelectOption = (questionId: string, optionIndex: number) => {
    setAnswers((prev) => ({ ...prev, [questionId]: optionIndex }));
  };

  const handleSubmit = async () => {
    if (!quiz) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await quizService.submitQuiz(skillName, category, answers);
      setResult(res);
      if (onAssessmentCompleted) {
        onAssessmentCompleted(res);
      }
    } catch (err: any) {
      setError(err.message || "Error submitting quiz.");
    } finally {
      setSubmitting(false);
    }
  };

  const answeredCount = Object.keys(answers).length;
  const totalQuestions = quiz?.questions.length || 0;
  const canSubmit = answeredCount === totalQuestions && totalQuestions > 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-gray-100 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-800 text-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Award className="w-5 h-5 text-blue-200" />
            <div>
              <h2 className="text-lg font-bold">Skill Quiz: {skillName}</h2>
              <p className="text-xs text-blue-200">Deterministic Proficiency Evaluation (1–5 Scale)</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-white/10 text-white/80 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {loading && (
            <div className="py-16 text-center space-y-3">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-sm text-gray-500 font-medium">Loading question bank...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-sm text-rose-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Quiz Result View */}
          {!loading && result && (
            <div className="space-y-6 text-center py-4">
              <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
                <CheckCircle2 className="w-8 h-8" />
              </div>

              <div>
                <h3 className="text-2xl font-black text-gray-900">Assessment Complete</h3>
                <p className="text-sm text-gray-500 mt-1">
                  You scored {result.score_percentage}% ({result.correct_count}/{result.total_questions} correct)
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
                <div className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                  <span className="text-xs text-gray-500 block mb-1">Assessed Proficiency</span>
                  <span className="text-2xl font-bold text-blue-600">
                    Level {result.assessed_proficiency} / 5
                  </span>
                </div>
                <div className="bg-gray-50 p-4 rounded-xl border border-gray-100">
                  <span className="text-xs text-gray-500 block mb-1">Current Skill Level</span>
                  <span className="text-2xl font-bold text-emerald-600">
                    Level {result.current_proficiency} / 5
                  </span>
                </div>
              </div>

              {result.preserved_verified && (
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-center gap-2 text-left">
                  <ShieldCheck className="w-5 h-5 text-amber-600 flex-shrink-0" />
                  <span>
                    <strong>Proficiency Preserved:</strong> Your previous verified proficiency (Level {result.previous_proficiency}/5) was preserved to protect your faculty-approved portfolio status.
                  </span>
                </div>
              )}

              <p className="text-sm text-gray-600 max-w-lg mx-auto bg-gray-50 p-3 rounded-xl border border-gray-100">
                {result.explanation}
              </p>

              <button
                onClick={onClose}
                className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-sm transition shadow-sm"
              >
                Close & Update Profile
              </button>
            </div>
          )}

          {/* Quiz Taking View */}
          {!loading && !result && quiz && (
            <div className="space-y-6">
              {/* Progress bar */}
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-gray-500 font-medium">
                  <span>Questions Answered: {answeredCount} of {totalQuestions}</span>
                  <span>{Math.round((answeredCount / totalQuestions) * 100)}%</span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300"
                    style={{ width: `${(answeredCount / totalQuestions) * 100}%` }}
                  />
                </div>
              </div>

              {/* Questions List */}
              <div className="space-y-6">
                {quiz.questions.map((q, qIndex) => (
                  <div key={q.id} className="p-4 rounded-xl border border-gray-100 bg-gray-50/50 space-y-3">
                    <p className="text-sm font-semibold text-gray-900">
                      {qIndex + 1}. {q.question}
                    </p>

                    <div className="space-y-2">
                      {q.options.map((opt, optIdx) => {
                        const isSelected = answers[q.id] === optIdx;
                        return (
                          <label
                            key={optIdx}
                            onClick={() => handleSelectOption(q.id, optIdx)}
                            className={`flex items-center gap-3 p-3 rounded-xl border text-sm cursor-pointer transition ${
                              isSelected
                                ? "bg-blue-50 border-blue-500 text-blue-900 font-medium shadow-sm"
                                : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
                            }`}
                          >
                            <input
                              type="radio"
                              name={q.id}
                              checked={isSelected}
                              onChange={() => handleSelectOption(q.id, optIdx)}
                              className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                            />
                            <span>{opt}</span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {!result && (
          <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {canSubmit ? "All questions answered. Ready to submit." : "Please answer all questions to submit."}
            </span>
            <div className="flex gap-2">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-200 text-gray-700 hover:bg-gray-100 rounded-xl text-sm font-medium transition"
              >
                Cancel
              </button>
              <button
                disabled={!canSubmit || submitting}
                onClick={handleSubmit}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-semibold transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {submitting ? "Evaluating..." : "Submit Answers"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

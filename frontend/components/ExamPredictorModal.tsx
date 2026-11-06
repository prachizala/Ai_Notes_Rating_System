"use client";

import { useState, useEffect } from "react";
import {
  Target,
  Flame,
  X,
  BookOpen,
  CheckCircle,
  HelpCircle,
  Copy,
  Check,
  Award,
  ChevronDown,
  ChevronUp,
  Lightbulb,
} from "lucide-react";
import { api, ExamPredictionResponse, PredictedQuestion } from "@/lib/api";

interface ExamPredictorModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExamPredictorModal({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}: ExamPredictorModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [questions, setQuestions] = useState<PredictedQuestion[]>([]);
  const [examTips, setExamTips] = useState<string[]>([]);
  const [selectedFilter, setSelectedFilter] = useState<"all" | 2 | 5 | 10>("all");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getExamPredictions(documentId)
      .then((data: ExamPredictionResponse) => {
        if (mounted) {
          setQuestions(data.questions || []);
          setExamTips(data.exam_tips || []);
          setLoading(false);
          if (data.questions && data.questions.length > 0) {
            setExpandedId(data.questions[0].id);
          }
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || "Failed to load predicted exam questions.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [documentId, isOpen]);

  const handleCopyQuestion = (id: number, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredQuestions = questions.filter((q) => {
    if (selectedFilter === "all") return true;
    return q.marks === selectedFilter;
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-amber-50/70 via-rose-50/50 to-orange-50/60 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-amber-500 to-rose-500 text-white shadow-md">
              <Target className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-rose-600 flex items-center gap-1">
                  <Flame className="h-3.5 w-3.5" /> Exam Question Predictor
                </span>
                <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800">
                  Innovation 2
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 line-clamp-1">{documentTitle}</h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Filter Navigation */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-3 bg-slate-50/60 shrink-0 overflow-x-auto">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedFilter("all")}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                selectedFilter === "all"
                  ? "bg-slate-900 text-white shadow-sm"
                  : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              All Questions ({questions.length})
            </button>
            <button
              onClick={() => setSelectedFilter(2)}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                selectedFilter === 2
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-white text-blue-700 hover:bg-blue-50 border border-blue-200"
              }`}
            >
              ⚡ 2 Marks ({questions.filter((q) => q.marks === 2).length})
            </button>
            <button
              onClick={() => setSelectedFilter(5)}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                selectedFilter === 5
                  ? "bg-purple-600 text-white shadow-sm"
                  : "bg-white text-purple-700 hover:bg-purple-50 border border-purple-200"
              }`}
            >
              📘 5 Marks ({questions.filter((q) => q.marks === 5).length})
            </button>
            <button
              onClick={() => setSelectedFilter(10)}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                selectedFilter === 10
                  ? "bg-rose-600 text-white shadow-sm"
                  : "bg-white text-rose-700 hover:bg-rose-50 border border-rose-200"
              }`}
            >
              🏆 10 Marks ({questions.filter((q) => q.marks === 10).length})
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-rose-500 border-t-transparent" />
              <p className="text-xs font-semibold text-slate-600">
                Analyzing university question trends & syllabus weightage...
              </p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
              <p className="font-bold">Error loading predicted questions</p>
              <p className="mt-1">{error}</p>
            </div>
          ) : (
            <>
              {/* Examiner Tips */}
              {examTips.length > 0 && (
                <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4 text-xs">
                  <div className="flex items-center gap-1.5 font-bold text-amber-900 mb-2">
                    <Lightbulb className="h-4 w-4 text-amber-600" />
                    University Examiner Golden Tips:
                  </div>
                  <ul className="space-y-1.5 text-amber-800 list-disc list-inside">
                    {examTips.map((tip, idx) => (
                      <li key={idx} className="leading-relaxed">
                        {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Question List */}
              <div className="space-y-4">
                {filteredQuestions.map((q) => {
                  const isExpanded = expandedId === q.id;

                  const marksBadgeStyle =
                    q.marks === 2
                      ? "bg-blue-50 text-blue-700 border-blue-200"
                      : q.marks === 5
                      ? "bg-purple-50 text-purple-700 border-purple-200"
                      : "bg-rose-50 text-rose-700 border-rose-200";

                  const probBadgeStyle =
                    q.probability === "Very High"
                      ? "bg-rose-100 text-rose-800 font-bold"
                      : q.probability === "High"
                      ? "bg-amber-100 text-amber-800 font-semibold"
                      : "bg-slate-100 text-slate-700";

                  return (
                    <div
                      key={q.id}
                      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition duration-200"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                        <div className="flex items-center gap-2">
                          <span
                            className={`rounded-lg border px-2.5 py-0.5 text-[11px] font-extrabold uppercase tracking-wide ${marksBadgeStyle}`}
                          >
                            {q.marks} Marks
                          </span>
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[11px] flex items-center gap-1 ${probBadgeStyle}`}
                          >
                            {q.probability === "Very High" && <Flame className="h-3 w-3" />}
                            {q.probability} Probability
                          </span>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                            {q.location}
                          </span>
                          <button
                            onClick={() => handleCopyQuestion(q.id, q.question)}
                            className="flex items-center gap-1 rounded-lg border border-slate-200 px-2 py-1 text-[11px] font-medium text-slate-500 hover:bg-slate-50 hover:text-slate-700 transition"
                            title="Copy Question"
                          >
                            {copiedId === q.id ? (
                              <>
                                <Check className="h-3 w-3 text-emerald-600" /> Copied
                              </>
                            ) : (
                              <>
                                <Copy className="h-3 w-3" /> Copy
                              </>
                            )}
                          </button>
                        </div>
                      </div>

                      <h3 className="text-sm sm:text-base font-bold text-slate-900 leading-snug">
                        {q.question}
                      </h3>

                      {/* Accordion Toggle */}
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : q.id)}
                        className="mt-3 flex items-center gap-1 text-xs font-bold text-brand-600 hover:text-brand-700 transition"
                      >
                        {isExpanded ? (
                          <>
                            Hide Model Answer Outline <ChevronUp className="h-3.5 w-3.5" />
                          </>
                        ) : (
                          <>
                            View Expected Key Points <ChevronDown className="h-3.5 w-3.5" />
                          </>
                        )}
                      </button>

                      {/* Expanded Answer Key */}
                      {isExpanded && (
                        <div className="mt-3 rounded-xl border border-slate-100 bg-slate-50 p-4 text-xs animate-in fade-in duration-200 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-slate-700 flex items-center gap-1.5">
                              <CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
                              What Examiners Expect in Your Answer:
                            </span>
                            <span className="text-[10px] uppercase font-bold text-slate-400">
                              Cognitive Level: {q.bloom_level}
                            </span>
                          </div>

                          <ul className="space-y-1 text-slate-600 list-disc list-inside">
                            {q.expected_key_points.map((pt, pIdx) => (
                              <li key={pIdx} className="leading-relaxed">
                                {pt}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

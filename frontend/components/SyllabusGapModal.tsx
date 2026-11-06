"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Compass,
  X,
  AlertTriangle,
  CheckCircle2,
  Search,
  ExternalLink,
  BookOpen,
  Sparkles,
  Layers,
  ArrowRight,
  Info,
} from "lucide-react";
import { api, CoveredTopicItem, MissingTopicItem, SyllabusGapResponse } from "@/lib/api";

interface SyllabusGapModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function SyllabusGapModal({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}: SyllabusGapModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SyllabusGapResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"missing" | "covered">("missing");

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getSyllabusGaps(documentId)
      .then((res: SyllabusGapResponse) => {
        if (mounted) {
          setData(res);
          // If no missing topics, default to covered tab
          if (!res.missing_topics || res.missing_topics.length === 0) {
            setActiveTab("covered");
          } else {
            setActiveTab("missing");
          }
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || "Failed to audit syllabus gaps.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [documentId, isOpen]);

  if (!isOpen) return null;

  const pct = data?.completeness_percentage || 0;
  const isHighCoverage = pct >= 80;
  const isMediumCoverage = pct >= 60 && pct < 80;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden my-6 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-teal-50/80 via-cyan-50/60 to-sky-50/70 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-teal-600 to-cyan-600 text-white shadow-md">
              <Compass className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-teal-700 flex items-center gap-1">
                  <Compass className="h-3.5 w-3.5" /> Syllabus Gap Heatmap
                </span>
                <span className="rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-bold text-teal-800">
                  Innovation 5
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

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-teal-600 border-t-transparent" />
              <p className="text-xs font-semibold text-slate-600">
                Auditing document text against university syllabus units...
              </p>
            </div>
          ) : error || !data ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
              <p className="font-bold">Error auditing syllabus gaps</p>
              <p className="mt-1">{error || "Could not retrieve syllabus data."}</p>
            </div>
          ) : (
            <>
              {/* Completeness Overview Banner */}
              <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-50 via-white to-teal-50/30 p-6 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-6">
                <div className="space-y-2 text-center sm:text-left flex-1">
                  <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wide">
                      {data.subject_name}
                    </span>
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                        isHighCoverage
                          ? "bg-emerald-100 text-emerald-800"
                          : isMediumCoverage
                          ? "bg-amber-100 text-amber-800"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {data.coverage_tier}
                    </span>
                  </div>
                  <h3 className="text-xl sm:text-2xl font-extrabold text-slate-900">
                    {pct}% Syllabus Covered
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed max-w-xl">
                    {data.study_advice}
                  </p>
                </div>

                {/* Progress Visual */}
                <div className="flex flex-col items-center justify-center shrink-0">
                  <div className="relative flex h-20 w-20 items-center justify-center rounded-full border-4 border-slate-100 bg-white shadow-inner">
                    <span
                      className={`text-xl font-extrabold ${
                        isHighCoverage
                          ? "text-emerald-600"
                          : isMediumCoverage
                          ? "text-amber-600"
                          : "text-rose-600"
                      }`}
                    >
                      {pct}%
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-slate-400 mt-1.5">
                    {data.covered_topics.length} covered / {data.missing_topics.length} missing
                  </span>
                </div>
              </div>

              {/* Tabs Switcher */}
              <div className="flex border-b border-slate-100">
                <button
                  onClick={() => setActiveTab("missing")}
                  className={`flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-bold transition ${
                    activeTab === "missing"
                      ? "border-rose-500 text-rose-700 bg-rose-50/40 rounded-t-xl"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <AlertTriangle className="h-4 w-4 text-rose-500" />
                  Missing Topics Gap ({data.missing_topics.length})
                </button>
                <button
                  onClick={() => setActiveTab("covered")}
                  className={`flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-bold transition ${
                    activeTab === "covered"
                      ? "border-teal-600 text-teal-700 bg-teal-50/40 rounded-t-xl"
                      : "border-transparent text-slate-500 hover:text-slate-800"
                  }`}
                >
                  <CheckCircle2 className="h-4 w-4 text-teal-600" />
                  Covered in This Note ({data.covered_topics.length})
                </button>
              </div>

              {/* Tab 1: Missing Topics Warning */}
              {activeTab === "missing" && (
                <div className="space-y-3">
                  {data.missing_topics.length === 0 ? (
                    <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-8 text-center text-xs text-emerald-800 space-y-2">
                      <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto" />
                      <p className="font-bold text-sm">Zero Missing Topics!</p>
                      <p>This note covers all registered syllabus units for this subject.</p>
                    </div>
                  ) : (
                    data.missing_topics.map((t, idx) => (
                      <div
                        key={idx}
                        className="rounded-2xl border border-rose-100 bg-rose-50/30 p-4 sm:p-5 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                      >
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="rounded-md bg-rose-100 text-rose-800 px-2 py-0.5 text-[10px] font-extrabold uppercase">
                              {t.importance} Priority Gap
                            </span>
                            <h4 className="font-bold text-sm text-slate-900">{t.topic_name}</h4>
                          </div>
                          <p className="text-xs text-slate-600 leading-relaxed">{t.reason}</p>
                        </div>

                        <Link
                          href={`/notes?q=${encodeURIComponent(t.recommended_search_query)}`}
                          target="_blank"
                          className="flex items-center justify-center gap-1.5 rounded-xl bg-white border border-rose-200 px-3.5 py-2 text-xs font-bold text-rose-700 hover:bg-rose-50 hover:border-rose-300 transition shrink-0 shadow-2xs"
                        >
                          <Search className="h-3.5 w-3.5" /> Find Notes on this Topic
                        </Link>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* Tab 2: Covered Topics */}
              {activeTab === "covered" && (
                <div className="space-y-3">
                  {data.covered_topics.map((c, idx) => (
                    <div
                      key={idx}
                      className="rounded-2xl border border-slate-100 bg-white p-4 shadow-2xs flex items-center justify-between gap-4"
                    >
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                          <h4 className="font-bold text-xs sm:text-sm text-slate-900">{c.topic_name}</h4>
                        </div>
                        <div className="flex items-center gap-3 text-[11px] text-slate-500 pl-6">
                          <span>Location: {c.location}</span>
                          <span>•</span>
                          <span className="capitalize font-medium text-emerald-700">{c.status.replace("_", " ")}</span>
                        </div>
                      </div>

                      {/* Depth Bar */}
                      <div className="w-28 text-right shrink-0">
                        <span className="text-xs font-bold text-slate-700">{c.depth_percentage}% Depth</span>
                        <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1 overflow-hidden">
                          <div
                            className="bg-emerald-500 h-1.5 rounded-full"
                            style={{ width: `${c.depth_percentage}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

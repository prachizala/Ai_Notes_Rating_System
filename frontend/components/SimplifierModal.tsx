"use client";

import { useState, useEffect } from "react";
import {
  Lightbulb,
  X,
  Sparkles,
  Building2,
  Smile,
  Languages,
  BookOpen,
  Search,
  Copy,
  Check,
  ChevronRight,
  HelpCircle,
} from "lucide-react";
import { api, ConceptExplanation, SimplificationResponse } from "@/lib/api";

interface SimplifierModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function SimplifierModal({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}: SimplifierModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [concepts, setConcepts] = useState<ConceptExplanation[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [activeLens, setActiveLens] = useState<"eli5" | "industry" | "hinglish">("eli5");

  // Custom term search
  const [customTerm, setCustomTerm] = useState("");
  const [searchingCustom, setSearchingCustom] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getSimplifications(documentId)
      .then((data: SimplificationResponse) => {
        if (mounted) {
          setConcepts(data.concepts || []);
          setSelectedIdx(0);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || "Failed to load concept simplifications.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [documentId, isOpen]);

  const handleCustomSimplify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customTerm.trim()) return;

    setSearchingCustom(true);
    try {
      const data = await api.simplifyCustomConcept(documentId, customTerm.trim());
      if (data.concepts && data.concepts.length > 0) {
        setConcepts([data.concepts[0], ...concepts]);
        setSelectedIdx(0);
        setCustomTerm("");
      }
    } catch (err: any) {
      alert(err.message || "Failed to simplify custom concept.");
    } finally {
      setSearchingCustom(false);
    }
  };

  const handleCopy = (key: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  if (!isOpen) return null;

  const currentConcept = concepts[selectedIdx];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden my-6 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-amber-50/70 via-emerald-50/50 to-teal-50/60 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-amber-500 to-emerald-600 text-white shadow-md">
              <Lightbulb className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                  <Smile className="h-3.5 w-3.5" /> Explain Like I'm a Beginner
                </span>
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                  Innovation 4
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

        {/* Custom Term Search Bar */}
        <div className="border-b border-slate-100 px-6 py-3 bg-slate-50/60 shrink-0">
          <form onSubmit={handleCustomSimplify} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={customTerm}
                onChange={(e) => setCustomTerm(e.target.value)}
                placeholder="Type or paste any complex term from the notes (e.g. 'Dangling Pointer', 'Normalization')..."
                className="w-full rounded-xl border border-slate-200 bg-white pl-9 pr-4 py-2 text-xs focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={searchingCustom || !customTerm.trim()}
              className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-50 transition shrink-0"
            >
              {searchingCustom ? "Simplifying..." : "Simplify Term"}
            </button>
          </form>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-600 border-t-transparent" />
              <p className="text-xs font-semibold text-slate-600">
                Demystifying academic jargon into simple real-world metaphors...
              </p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
              <p className="font-bold">Error loading simplifications</p>
              <p className="mt-1">{error}</p>
            </div>
          ) : concepts.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500">
              No concepts available for simplification yet.
            </div>
          ) : (
            <div className="space-y-6">
              {/* Concept Tabs */}
              <div className="flex items-center gap-2 overflow-x-auto pb-1">
                {concepts.map((c, idx) => (
                  <button
                    key={idx}
                    onClick={() => setSelectedIdx(idx)}
                    className={`rounded-xl px-4 py-2 text-xs font-bold transition shrink-0 flex items-center gap-1.5 ${
                      selectedIdx === idx
                        ? "bg-slate-900 text-white shadow-md"
                        : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                    }`}
                  >
                    <span>{c.concept_name}</span>
                  </button>
                ))}
              </div>

              {/* 3 Lens Switcher */}
              <div className="grid grid-cols-3 gap-2 p-1.5 rounded-2xl bg-slate-100">
                <button
                  onClick={() => setActiveLens("eli5")}
                  className={`flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition ${
                    activeLens === "eli5"
                      ? "bg-white text-amber-900 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Smile className="h-4 w-4 text-amber-500" />
                  <span>🧸 ELI5 Metaphor</span>
                </button>
                <button
                  onClick={() => setActiveLens("industry")}
                  className={`flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition ${
                    activeLens === "industry"
                      ? "bg-white text-indigo-900 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Building2 className="h-4 w-4 text-indigo-600" />
                  <span>🏢 Industry Case Study</span>
                </button>
                <button
                  onClick={() => setActiveLens("hinglish")}
                  className={`flex items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-bold transition ${
                    activeLens === "hinglish"
                      ? "bg-white text-emerald-900 shadow-sm"
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  <Languages className="h-4 w-4 text-emerald-600" />
                  <span>🇮🇳 Hinglish Breakdown</span>
                </button>
              </div>

              {/* Lens Explanation Display Card */}
              {currentConcept && (
                <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-white to-slate-50/50 p-6 sm:p-8 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Concept: {currentConcept.concept_name}
                    </span>
                    <button
                      onClick={() =>
                        handleCopy(
                          activeLens,
                          activeLens === "eli5"
                            ? currentConcept.eli5_analogy
                            : activeLens === "industry"
                            ? currentConcept.industry_application
                            : currentConcept.hinglish_breakdown
                        )
                      }
                      className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-500 hover:bg-slate-50"
                    >
                      {copiedKey === activeLens ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-600" /> Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5" /> Copy Explanation
                        </>
                      )}
                    </button>
                  </div>

                  {activeLens === "eli5" && (
                    <div className="space-y-3 animate-in fade-in duration-200">
                      <div className="flex items-center gap-2 text-sm font-bold text-amber-800">
                        <Smile className="h-4 w-4 text-amber-500" /> Everyday Analogy (Explain Like I'm 5):
                      </div>
                      <p className="text-base sm:text-lg text-slate-800 font-medium leading-relaxed bg-amber-50/50 p-5 rounded-2xl border border-amber-100">
                        "{currentConcept.eli5_analogy}"
                      </p>
                    </div>
                  )}

                  {activeLens === "industry" && (
                    <div className="space-y-3 animate-in fade-in duration-200">
                      <div className="flex items-center gap-2 text-sm font-bold text-indigo-800">
                        <Building2 className="h-4 w-4 text-indigo-600" /> Real-World Tech & Corporate Application:
                      </div>
                      <p className="text-base sm:text-lg text-slate-800 font-medium leading-relaxed bg-indigo-50/50 p-5 rounded-2xl border border-indigo-100">
                        {currentConcept.industry_application}
                      </p>
                    </div>
                  )}

                  {activeLens === "hinglish" && (
                    <div className="space-y-3 animate-in fade-in duration-200">
                      <div className="flex items-center gap-2 text-sm font-bold text-emerald-800">
                        <Languages className="h-4 w-4 text-emerald-600" /> Conversational Hinglish Explanation:
                      </div>
                      <p className="text-base sm:text-lg text-slate-800 font-medium leading-relaxed bg-emerald-50/50 p-5 rounded-2xl border border-emerald-100">
                        "{currentConcept.hinglish_breakdown}"
                      </p>
                    </div>
                  )}

                  {/* Jargon Busters Table */}
                  {currentConcept.jargon_busters && currentConcept.jargon_busters.length > 0 && (
                    <div className="pt-4 border-t border-slate-100 mt-6">
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5 text-slate-500" /> Jargon Buster (Difficult Terms Demystified):
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {currentConcept.jargon_busters.map((j, jIdx) => (
                          <div
                            key={jIdx}
                            className="rounded-xl border border-slate-100 bg-white p-3.5 shadow-2xs space-y-1"
                          >
                            <span className="font-bold text-xs text-rose-700">{j.term}</span>
                            <p className="text-xs text-slate-600 leading-relaxed">{j.simple_meaning}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

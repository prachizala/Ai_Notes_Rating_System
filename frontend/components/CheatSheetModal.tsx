"use client";

import { useState, useEffect } from "react";
import {
  FileText,
  X,
  Printer,
  Copy,
  Check,
  AlertOctagon,
  Sparkles,
  BookOpen,
  Code2,
  TableProperties,
  Lightbulb,
} from "lucide-react";
import { api, CheatSheetResponse } from "@/lib/api";

interface CheatSheetModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function CheatSheetModal({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}: CheatSheetModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<CheatSheetResponse | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getCheatSheet(documentId)
      .then((res: CheatSheetResponse) => {
        if (mounted) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || "Failed to load exam cheat sheet.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [documentId, isOpen]);

  const handlePrint = () => {
    window.print();
  };

  const handleCopyMarkdown = () => {
    if (!data) return;
    const md = `
# 📄 NoteIQ Exam Cheat Sheet: ${data.document_title}
**Subject:** ${data.subject_name}

## ⚡ Core Capsule
${data.summary_capsule}

## 💻 Key Formulas & Syntax
${data.formulas_and_syntax.map((f) => `- **${f.title}**: \`${f.syntax_or_formula}\` (${f.note})`).join("\n")}

## 📖 Must-Know Definitions
${data.key_definitions.map((d) => `- **${d.term}**: ${d.definition}`).join("\n")}

## ⚖️ Key Distinctions
${data.distinctions_table.map((row) => `| ${row.parameter} | ${row.concept_a} | ${row.concept_b} |`).join("\n")}

## ⚠️ Common Exam Traps
${data.exam_traps.map((t) => `- ❌ ${t}`).join("\n")}

## 💡 Rapid Mnemonics
${data.rapid_mnemonics.map((m) => `- 🧠 ${m}`).join("\n")}
    `.trim();

    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto print:p-0 print:bg-white print:fixed print:inset-0">
      <div className="relative w-full max-w-4xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden my-6 max-h-[92vh] flex flex-col print:max-h-none print:my-0 print:border-none print:shadow-none print:rounded-none">
        {/* Header - Hidden on print */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-emerald-50/80 via-teal-50/60 to-cyan-50/70 px-6 py-4 shrink-0 print:hidden">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-600 text-white shadow-md">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                  1-Page Exam Formula & Revision Card
                </span>
                <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                  Print Ready
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 line-clamp-1">{documentTitle}</h2>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 rounded-xl bg-slate-900 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-slate-800 transition"
            >
              <Printer className="h-3.5 w-3.5" /> Print / Save PDF
            </button>
            <button
              onClick={handleCopyMarkdown}
              className="flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-600" /> Copied!
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" /> Copy Markdown
                </>
              )}
            </button>
            <button
              onClick={onClose}
              className="rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Cheat Sheet Body */}
        <div className="p-6 sm:p-8 overflow-y-auto flex-1 space-y-6 print:p-4 print:overflow-visible text-slate-900">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center print:hidden">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-emerald-600 border-t-transparent" />
              <p className="text-xs font-semibold text-slate-600">
                Condensing course note into 1-page high-yield exam cheat sheet...
              </p>
            </div>
          ) : error || !data ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
              <p className="font-bold">Error generating cheat sheet</p>
              <p className="mt-1">{error || "Could not retrieve cheat sheet."}</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Document Title & Watermark */}
              <div className="border-b-2 border-slate-900 pb-3 flex items-start justify-between">
                <div>
                  <span className="text-[11px] font-extrabold uppercase tracking-widest text-emerald-700">
                    NoteIQ • High-Yield Revision Capsule
                  </span>
                  <h1 className="text-xl sm:text-2xl font-black text-slate-900 mt-0.5">
                    {data.document_title}
                  </h1>
                  <span className="text-xs text-slate-500 font-semibold">{data.subject_name}</span>
                </div>
                <div className="text-right">
                  <span className="rounded-lg border border-slate-300 bg-slate-50 px-2.5 py-1 text-[11px] font-bold text-slate-700 uppercase">
                    A4 Exam Card
                  </span>
                </div>
              </div>

              {/* Core Capsule */}
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs">
                <span className="font-bold text-slate-900 flex items-center gap-1.5 uppercase tracking-wide mb-1">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-600" /> 2-Minute Executive Summary:
                </span>
                <p className="text-slate-700 leading-relaxed font-medium">{data.summary_capsule}</p>
              </div>

              {/* Grid: Formulas/Syntax & Definitions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Section 1: Formulas & Syntax */}
                <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3">
                  <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wide flex items-center gap-1.5 border-b pb-2">
                    <Code2 className="h-3.5 w-3.5 text-indigo-600" /> Key Formulas & Syntax Declarations
                  </h3>
                  <div className="space-y-2.5">
                    {data.formulas_and_syntax.map((f, idx) => (
                      <div key={idx} className="rounded-xl border border-slate-100 bg-slate-50/70 p-2.5 space-y-1">
                        <span className="font-bold text-xs text-slate-800">{f.title}</span>
                        <code className="block rounded-lg bg-slate-900 p-2 text-[11px] font-mono text-emerald-400 overflow-x-auto">
                          {f.syntax_or_formula}
                        </code>
                        <span className="text-[10px] text-slate-500 block leading-tight">{f.note}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 2: Definitions */}
                <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3">
                  <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wide flex items-center gap-1.5 border-b pb-2">
                    <BookOpen className="h-3.5 w-3.5 text-emerald-600" /> Must-Know Definitions (Full Marks)
                  </h3>
                  <div className="space-y-2.5">
                    {data.key_definitions.map((d, idx) => (
                      <div key={idx} className="rounded-xl border border-slate-100 bg-slate-50/70 p-2.5 space-y-1">
                        <span className="font-bold text-xs text-emerald-900 block">{d.term}</span>
                        <p className="text-[11px] text-slate-600 leading-relaxed">{d.definition}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Section 3: Key Distinctions Table */}
              <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3">
                <h3 className="text-xs font-extrabold text-slate-900 uppercase tracking-wide flex items-center gap-1.5 border-b pb-2">
                  <TableProperties className="h-3.5 w-3.5 text-cyan-600" /> Essential Distinctions & Comparisons Table
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-100 text-slate-700 font-bold border-b">
                        <th className="p-2.5 rounded-l-lg">Parameter</th>
                        <th className="p-2.5">Concept A</th>
                        <th className="p-2.5 rounded-r-lg">Concept B</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {data.distinctions_table.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/50">
                          <td className="p-2.5 font-bold text-slate-800">{row.parameter}</td>
                          <td className="p-2.5 text-slate-600">{row.concept_a}</td>
                          <td className="p-2.5 text-slate-600">{row.concept_b}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Grid: Exam Traps & Rapid Mnemonics */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Exam Traps */}
                <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-4 space-y-2">
                  <h4 className="text-xs font-bold text-rose-900 uppercase tracking-wide flex items-center gap-1.5">
                    <AlertOctagon className="h-3.5 w-3.5 text-rose-600" /> Common Exam Traps (Avoid These!)
                  </h4>
                  <ul className="space-y-1.5 text-xs text-rose-800">
                    {data.exam_traps.map((t, idx) => (
                      <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                        <span className="font-bold text-rose-600 shrink-0">❌</span>
                        <span>{t}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Mnemonics */}
                <div className="rounded-2xl border border-amber-200 bg-amber-50/50 p-4 space-y-2">
                  <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wide flex items-center gap-1.5">
                    <Lightbulb className="h-3.5 w-3.5 text-amber-600" /> Rapid Memory Mnemonics
                  </h4>
                  <ul className="space-y-1.5 text-xs text-amber-800">
                    {data.rapid_mnemonics.map((m, idx) => (
                      <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
                        <span className="font-bold text-amber-600 shrink-0">🧠</span>
                        <span>{m}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

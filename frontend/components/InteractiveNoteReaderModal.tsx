"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  api,
  DocumentReaderResponse,
  DocumentReaderChunk,
  InlineExplainResponse,
} from "@/lib/api";

interface InteractiveNoteReaderModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

interface SavedHighlight {
  id: string;
  text: string;
  location: string;
  explanation?: string;
  mode?: string;
}

export const InteractiveNoteReaderModal: React.FC<InteractiveNoteReaderModalProps> = ({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [readerData, setReaderData] = useState<DocumentReaderResponse | null>(null);
  const [currentChunkIndex, setCurrentChunkIndex] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [fontSize, setFontSize] = useState<"sm" | "base" | "lg">("base");

  // Selection & Floating Toolbar state
  const [selectedText, setSelectedText] = useState<string>("");
  const [floatingPos, setFloatingPos] = useState<{ top: number; left: number } | null>(null);
  const [explaining, setExplaining] = useState<boolean>(false);
  const [explanationData, setExplanationData] = useState<InlineExplainResponse | null>(null);
  const [activeExplainMode, setActiveExplainMode] = useState<string>("eli5");

  // Saved Highlights Sidebar
  const [showHighlightsDrawer, setShowHighlightsDrawer] = useState<boolean>(false);
  const [savedHighlights, setSavedHighlights] = useState<SavedHighlight[]>([]);

  const contentRef = useRef<HTMLDivElement>(null);

  // Fetch reader content
  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);
    setError(null);
    setSelectedText("");
    setFloatingPos(null);
    setExplanationData(null);

    // Load saved highlights from localStorage
    try {
      const saved = localStorage.getItem(`noteiq_highlights_${documentId}`);
      if (saved) {
        setSavedHighlights(JSON.parse(saved));
      }
    } catch {
      // ignore
    }

    api
      .getReaderContent(documentId)
      .then((res: DocumentReaderResponse) => {
        if (isMounted) {
          setReaderData(res);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || "Failed to load document text chunks.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, documentId]);

  // Handle text selection
  const handleMouseUp = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      if (!explanationData) {
        setFloatingPos(null);
        setSelectedText("");
      }
      return;
    }

    const text = selection.toString().trim();
    if (text.length < 3) {
      if (!explanationData) {
        setFloatingPos(null);
        setSelectedText("");
      }
      return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();

    setSelectedText(text);
    setExplanationData(null);
    setFloatingPos({
      top: Math.max(10, rect.top - 55),
      left: Math.max(20, rect.left + rect.width / 2),
    });
  };

  // Trigger inline explanation
  const handleExplain = async (mode: string) => {
    if (!selectedText) return;

    setActiveExplainMode(mode);
    setExplaining(true);

    const activeChunk = readerData?.chunks[currentChunkIndex];
    try {
      const res = await api.explainReaderSnippet(documentId, {
        selected_text: selectedText,
        context: activeChunk?.text,
        mode: mode,
      });
      setExplanationData(res);
    } catch (err: any) {
      alert(err.message || "Failed to explain selection.");
    } finally {
      setExplaining(false);
    }
  };

  // Save highlight snippet
  const handleSaveHighlight = () => {
    if (!selectedText) return;
    const activeChunk = readerData?.chunks[currentChunkIndex];
    const newHighlight: SavedHighlight = {
      id: Date.now().toString(),
      text: selectedText,
      location: activeChunk?.location || `Section ${currentChunkIndex + 1}`,
      explanation: explanationData?.explanation,
      mode: activeExplainMode,
    };

    const updated = [newHighlight, ...savedHighlights];
    setSavedHighlights(updated);
    try {
      localStorage.setItem(`noteiq_highlights_${documentId}`, JSON.stringify(updated));
    } catch {
      // ignore
    }
    alert("Snippet saved to your Reading Highlights!");
  };

  // Remove highlight
  const handleRemoveHighlight = (id: string) => {
    const updated = savedHighlights.filter((h) => h.id !== id);
    setSavedHighlights(updated);
    try {
      localStorage.setItem(`noteiq_highlights_${documentId}`, JSON.stringify(updated));
    } catch {
      // ignore
    }
  };

  // Export highlights
  const handleExportHighlights = () => {
    if (savedHighlights.length === 0) return;
    let text = `# Reading Highlights: ${documentTitle}\n\n`;
    savedHighlights.forEach((h, i) => {
      text += `### Highlight ${i + 1} (${h.location})\n`;
      text += `> "${h.text}"\n\n`;
      if (h.explanation) {
        text += `**Explanation (${h.mode || "ELI5"}):** ${h.explanation}\n\n`;
      }
      text += `---\n\n`;
    });

    const blob = new Blob([text], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${documentTitle.replace(/\s+/g, "_")}_Highlights.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  const currentChunk: DocumentReaderChunk | undefined =
    readerData?.chunks[currentChunkIndex];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-2 sm:p-4 overflow-hidden">
      <div className="relative w-full max-w-5xl h-[94vh] bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header with Navigation Controls */}
        <div className="flex items-center justify-between px-6 py-3.5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-slate-900/80">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-teal-500/20">
              📖
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-bold text-slate-900 dark:text-white truncate max-w-sm sm:max-w-md">
                  Interactive Note Reader
                </h2>
                <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-teal-100 dark:bg-teal-900/40 text-teal-800 dark:text-teal-300 border border-teal-200 dark:border-teal-800">
                  Highlight Assist
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-xs sm:max-w-sm">
                {documentTitle}
              </p>
            </div>
          </div>

          {/* Reader toolbar */}
          <div className="flex items-center gap-2">
            {/* Font size toggles */}
            <div className="hidden sm:flex items-center bg-slate-200/60 dark:bg-slate-800 rounded-lg p-0.5 text-xs font-semibold">
              <button
                onClick={() => setFontSize("sm")}
                className={`px-2 py-1 rounded-md transition ${
                  fontSize === "sm" ? "bg-white dark:bg-slate-750 shadow-sm text-teal-600" : "text-slate-500"
                }`}
              >
                A-
              </button>
              <button
                onClick={() => setFontSize("base")}
                className={`px-2 py-1 rounded-md transition ${
                  fontSize === "base" ? "bg-white dark:bg-slate-750 shadow-sm text-teal-600" : "text-slate-500"
                }`}
              >
                A
              </button>
              <button
                onClick={() => setFontSize("lg")}
                className={`px-2 py-1 rounded-md transition ${
                  fontSize === "lg" ? "bg-white dark:bg-slate-750 shadow-sm text-teal-600" : "text-slate-500"
                }`}
              >
                A+
              </button>
            </div>

            {/* Saved Highlights Toggle */}
            <button
              onClick={() => setShowHighlightsDrawer(!showHighlightsDrawer)}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 hover:bg-amber-100 transition flex items-center gap-1.5"
            >
              <span>🖍️</span>
              <span className="hidden sm:inline">Highlights</span>
              <span className="px-1.5 py-0.2 rounded-full bg-amber-200 dark:bg-amber-800 text-[10px]">
                {savedHighlights.length}
              </span>
            </button>

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 transition"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Floating AI Highlight Action Pill */}
        {floatingPos && selectedText && (
          <div
            style={{
              position: "fixed",
              top: `${floatingPos.top}px`,
              left: `${floatingPos.left}px`,
              transform: "translateX(-50%)",
            }}
            className="z-50 flex flex-col items-center animate-in fade-in zoom-in-95 duration-150"
          >
            {/* Action Bar */}
            <div className="flex items-center gap-1 p-1 bg-slate-900/95 text-white rounded-xl shadow-2xl border border-slate-700 backdrop-blur-md">
              <button
                onClick={() => handleExplain("eli5")}
                className="px-2.5 py-1 text-xs font-semibold rounded-lg hover:bg-slate-800 flex items-center gap-1 transition"
              >
                <span>💡</span>
                <span>ELI5</span>
              </button>
              <div className="w-px h-4 bg-slate-700" />
              <button
                onClick={() => handleExplain("hinglish")}
                className="px-2.5 py-1 text-xs font-semibold rounded-lg hover:bg-slate-800 flex items-center gap-1 transition"
              >
                <span>🇮🇳</span>
                <span>Hinglish</span>
              </button>
              <div className="w-px h-4 bg-slate-700" />
              <button
                onClick={() => handleExplain("exam_trap")}
                className="px-2.5 py-1 text-xs font-semibold rounded-lg hover:bg-slate-800 flex items-center gap-1 transition"
              >
                <span>⚠️</span>
                <span>Exam Trap</span>
              </button>
              <div className="w-px h-4 bg-slate-700" />
              <button
                onClick={handleSaveHighlight}
                className="px-2.5 py-1 text-xs font-semibold rounded-lg hover:bg-slate-800 text-amber-300 flex items-center gap-1 transition"
                title="Save snippet"
              >
                <span>💾</span>
                <span>Save</span>
              </button>
              <button
                onClick={() => {
                  setFloatingPos(null);
                  setSelectedText("");
                  setExplanationData(null);
                }}
                className="px-1.5 py-1 text-xs text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            {/* Down arrow triangle */}
            <div className="w-2.5 h-2.5 bg-slate-900 rotate-45 -mt-1 shadow-sm" />

            {/* Explanation Popover Card */}
            {(explaining || explanationData) && (
              <div className="mt-2 w-80 sm:w-96 bg-white dark:bg-slate-950 p-4 rounded-xl shadow-2xl border border-teal-500/40 dark:border-teal-500/30 text-left text-xs space-y-2.5 max-h-72 overflow-y-auto animate-in fade-in slide-in-from-top-2 duration-150">
                {explaining ? (
                  <div className="flex items-center gap-2 py-3 text-slate-600 dark:text-slate-300">
                    <div className="w-4 h-4 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
                    <span>AI Assistant is analyzing selection...</span>
                  </div>
                ) : explanationData ? (
                  <>
                    <div className="flex items-center justify-between pb-1.5 border-b border-slate-100 dark:border-slate-800">
                      <span className="font-bold text-teal-600 dark:text-teal-400 uppercase tracking-wider text-[10px]">
                        {explanationData.mode.toUpperCase()} Explanation
                      </span>
                      <button
                        onClick={handleSaveHighlight}
                        className="text-[11px] font-semibold text-amber-600 hover:underline"
                      >
                        + Save to Highlights
                      </button>
                    </div>
                    <p className="text-slate-800 dark:text-slate-200 leading-relaxed font-medium">
                      {explanationData.explanation}
                    </p>
                    {explanationData.mnemonic_or_analogy && (
                      <div className="p-2 rounded-lg bg-teal-50/70 dark:bg-teal-950/30 border border-teal-200/50 dark:border-teal-900/40 text-teal-900 dark:text-teal-300">
                        ⚡ <strong>Analogy / Memory Key:</strong> {explanationData.mnemonic_or_analogy}
                      </div>
                    )}
                    {explanationData.key_takeaways.length > 0 && (
                      <ul className="space-y-1 text-slate-600 dark:text-slate-400 pt-1">
                        {explanationData.key_takeaways.map((k, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-teal-500 font-bold">•</span>
                            <span>{k}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </>
                ) : null}
              </div>
            )}
          </div>
        )}

        {/* Body Container (Main text area + Highlights sidebar) */}
        <div className="flex-1 flex overflow-hidden relative">
          {/* Main Reading Area */}
          <div
            ref={contentRef}
            onMouseUp={handleMouseUp}
            className="flex-1 overflow-y-auto px-6 sm:px-12 py-8 bg-amber-50/20 dark:bg-slate-900 selection:bg-teal-200 dark:selection:bg-teal-900 selection:text-teal-950 dark:selection:text-teal-100"
          >
            {loading ? (
              <div className="flex flex-col items-center justify-center py-24 text-center">
                <div className="w-12 h-12 border-4 border-teal-600 border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-base font-semibold text-slate-800 dark:text-slate-200">
                  Opening Document Reader...
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Parsing pages and formatting academic sections for interactive study.
                </p>
              </div>
            ) : error ? (
              <div className="p-6 text-center py-20">
                <div className="inline-flex p-3 rounded-full bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 mb-3 text-2xl">
                  ⚠️
                </div>
                <p className="text-sm text-rose-600 dark:text-rose-400 font-medium mb-4">{error}</p>
                <button
                  onClick={() => {
                    setLoading(true);
                    api.getReaderContent(documentId).then((res) => {
                      setReaderData(res);
                      setLoading(false);
                    });
                  }}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-medium transition"
                >
                  Retry Loading
                </button>
              </div>
            ) : currentChunk ? (
              <div className="max-w-3xl mx-auto space-y-6">
                {/* Chunk Header / Breadcrumb */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
                  <span className="text-xs font-bold uppercase tracking-wider text-teal-600 dark:text-teal-400">
                    📍 {currentChunk.location}
                  </span>
                  <span className="text-xs text-slate-400">
                    Section {currentChunkIndex + 1} of {readerData?.total_chunks || 1}
                  </span>
                </div>

                {/* Highlight Instruction Hint */}
                <div className="p-2.5 rounded-xl bg-teal-50 dark:bg-teal-950/30 border border-teal-200/60 dark:border-teal-800/40 text-xs text-teal-800 dark:text-teal-300 flex items-center justify-between">
                  <span>
                    💡 <strong>Tip:</strong> Highlight any text or sentence with your cursor to trigger instant AI explanation & Hinglish breakdown!
                  </span>
                </div>

                {/* Note Content Text */}
                <div
                  className={`leading-relaxed font-serif text-slate-800 dark:text-slate-200 whitespace-pre-wrap ${
                    fontSize === "sm"
                      ? "text-sm leading-6"
                      : fontSize === "lg"
                      ? "text-lg leading-8"
                      : "text-base leading-7"
                  }`}
                >
                  {currentChunk.text}
                </div>
              </div>
            ) : (
              <p className="text-center py-20 text-sm text-slate-400">No content found in this document.</p>
            )}
          </div>

          {/* Saved Highlights Sidebar Drawer */}
          {showHighlightsDrawer && (
            <div className="w-80 border-l border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950 flex flex-col h-full shadow-xl animate-in slide-in-from-right-10 duration-200">
              <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    My Highlights
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    {savedHighlights.length} snippets saved
                  </p>
                </div>
                {savedHighlights.length > 0 && (
                  <button
                    onClick={handleExportHighlights}
                    className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-teal-50 text-teal-700 hover:bg-teal-100 dark:bg-teal-950 dark:text-teal-300 transition"
                  >
                    ⬇️ Export .md
                  </button>
                )}
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {savedHighlights.length === 0 ? (
                  <div className="text-center py-12 text-slate-400 text-xs">
                    <p className="text-2xl mb-2">🖍️</p>
                    <p>No highlights saved yet.</p>
                    <p className="mt-1 text-[11px]">
                      Select any text while reading and click &quot;Save&quot; to keep key revision snippets here.
                    </p>
                  </div>
                ) : (
                  savedHighlights.map((h) => (
                    <div
                      key={h.id}
                      className="p-3 rounded-xl bg-amber-50/50 dark:bg-slate-900 border border-amber-200/60 dark:border-slate-800 text-xs space-y-1.5 relative group"
                    >
                      <div className="flex items-center justify-between text-[10px] text-slate-400">
                        <span className="font-semibold text-amber-700 dark:text-amber-400">
                          {h.location}
                        </span>
                        <button
                          onClick={() => handleRemoveHighlight(h.id)}
                          className="opacity-0 group-hover:opacity-100 text-rose-500 hover:text-rose-700 transition"
                          title="Delete snippet"
                        >
                          ✕
                        </button>
                      </div>
                      <p className="text-slate-800 dark:text-slate-200 font-medium italic border-l-2 border-amber-400 pl-2">
                        &quot;{h.text}&quot;
                      </p>
                      {h.explanation && (
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 pt-1">
                          <strong>Note:</strong> {h.explanation}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer Page Navigation */}
        {readerData && readerData.total_chunks > 1 && (
          <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 flex items-center justify-between text-xs font-semibold">
            <button
              onClick={() => setCurrentChunkIndex((prev) => Math.max(0, prev - 1))}
              disabled={currentChunkIndex === 0}
              className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 transition"
            >
              ← Previous Section
            </button>
            <span className="text-slate-500 dark:text-slate-400">
              Section {currentChunkIndex + 1} of {readerData.total_chunks}
            </span>
            <button
              onClick={() =>
                setCurrentChunkIndex((prev) => Math.min(readerData.total_chunks - 1, prev + 1))
              }
              disabled={currentChunkIndex === readerData.total_chunks - 1}
              className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-100 transition"
            >
              Next Section →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

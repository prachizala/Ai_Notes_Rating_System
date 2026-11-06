"use client";

import { useState, useEffect, useRef } from "react";
import {
  GitFork,
  X,
  Copy,
  Check,
  Maximize2,
  Minimize2,
  Layers,
  Network,
  Code2,
  ChevronRight,
  Info,
  Sparkles,
} from "lucide-react";
import { api, MindMapNode, MindMapResponse } from "@/lib/api";

interface MindMapModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function MindMapModal({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}: MindMapModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mermaidCode, setMermaidCode] = useState<string>("");
  const [nodes, setNodes] = useState<MindMapNode[]>([]);
  const [summary, setSummary] = useState<string>("");
  const [viewMode, setViewMode] = useState<"visual" | "tree" | "code">("visual");
  const [selectedNode, setSelectedNode] = useState<MindMapNode | null>(null);
  const [copiedCode, setCopiedCode] = useState(false);
  const [svgHtml, setSvgHtml] = useState<string>("");

  const mermaidContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    setLoading(true);
    setError(null);
    setSvgHtml("");

    api
      .getMindMap(documentId)
      .then(async (data: MindMapResponse) => {
        if (!mounted) return;
        setMermaidCode(data.mermaid_code || "");
        setNodes(data.nodes || []);
        setSummary(data.summary || "");
        if (data.nodes && data.nodes.length > 0) {
          setSelectedNode(data.nodes[0]);
        }
        setLoading(false);

        // Dynamically load and render mermaid
        if (data.mermaid_code) {
          try {
            const mermaidModule = await import("mermaid");
            const mermaid = mermaidModule.default;
            mermaid.initialize({
              startOnLoad: false,
              theme: "default",
              securityLevel: "loose",
              flowchart: {
                useMaxWidth: true,
                htmlLabels: true,
                curve: "basis",
              },
            });
            const renderId = `mermaid-svg-${Date.now()}`;
            const { svg } = await mermaid.render(renderId, data.mermaid_code);
            if (mounted) {
              setSvgHtml(svg);
            }
          } catch (renderErr) {
            console.warn("Mermaid rendering warning:", renderErr);
          }
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || "Failed to generate mind map.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [documentId, isOpen]);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(mermaidCode);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden my-6 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-indigo-50/70 via-blue-50/50 to-cyan-50/60 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-cyan-600 text-white shadow-md">
              <Network className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-700 flex items-center gap-1">
                  <GitFork className="h-3.5 w-3.5" /> Concept Mind Map
                </span>
                <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-800">
                  Innovation 3
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

        {/* Mode Switcher */}
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-2.5 bg-slate-50/60 shrink-0">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode("visual")}
              className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                viewMode === "visual"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              <Network className="h-3.5 w-3.5" /> Visual Flow Diagram
            </button>
            <button
              onClick={() => setViewMode("tree")}
              className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                viewMode === "tree"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              <Layers className="h-3.5 w-3.5" /> Concept Nodes ({nodes.length})
            </button>
            <button
              onClick={() => setViewMode("code")}
              className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-bold transition ${
                viewMode === "code"
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "bg-white text-slate-600 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              <Code2 className="h-3.5 w-3.5" /> Mermaid Syntax
            </button>
          </div>

          {viewMode === "code" && (
            <button
              onClick={handleCopyCode}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            >
              {copiedCode ? (
                <>
                  <Check className="h-3.5 w-3.5 text-emerald-600" /> Copied!
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" /> Copy Code
                </>
              )}
            </button>
          )}
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
              <p className="text-xs font-semibold text-slate-600">
                AI is structuring knowledge hierarchy and generating visual diagram...
              </p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
              <p className="font-bold">Error loading mind map</p>
              <p className="mt-1">{error}</p>
            </div>
          ) : viewMode === "visual" ? (
            /* ================= VISUAL FLOW DIAGRAM ================= */
            <div className="space-y-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50/50 p-6 flex items-center justify-center min-h-[340px] overflow-x-auto">
                {svgHtml ? (
                  <div
                    className="w-full flex justify-center [&_svg]:max-w-full [&_svg]:h-auto shadow-sm p-2 rounded-xl bg-white"
                    dangerouslySetInnerHTML={{ __html: svgHtml }}
                  />
                ) : (
                  <div className="text-center space-y-3">
                    <Layers className="h-8 w-8 text-indigo-400 mx-auto" />
                    <p className="text-xs font-semibold text-slate-600">
                      Diagram code generated. You can inspect it in the Concept Nodes or Syntax tabs.
                    </p>
                    <button
                      onClick={() => setViewMode("tree")}
                      className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-sm"
                    >
                      View Concept Nodes →
                    </button>
                  </div>
                )}
              </div>

              {/* Synopsis */}
              {summary && (
                <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-3.5 text-xs text-indigo-900 flex items-start gap-2">
                  <Sparkles className="h-4 w-4 text-indigo-600 shrink-0 mt-0.5" />
                  <p className="leading-relaxed">{summary}</p>
                </div>
              )}
            </div>
          ) : viewMode === "tree" ? (
            /* ================= CONCEPT NODES HIERARCHY ================= */
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Node List */}
              <div className="md:col-span-1 rounded-2xl border border-slate-200 bg-slate-50/50 p-3 space-y-1.5 max-h-[400px] overflow-y-auto">
                <span className="text-[11px] font-bold text-slate-400 uppercase px-2 mb-1 block">
                  Concept Nodes
                </span>
                {nodes.map((node) => {
                  const isSelected = selectedNode?.id === node.id;
                  const catColor =
                    node.category === "core"
                      ? "bg-indigo-100 text-indigo-800"
                      : node.category === "subtopic"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-slate-100 text-slate-700";

                  return (
                    <button
                      key={node.id}
                      onClick={() => setSelectedNode(node)}
                      className={`w-full text-left rounded-xl p-2.5 text-xs transition flex items-center justify-between gap-2 ${
                        isSelected
                          ? "bg-white shadow-sm border border-indigo-200 font-bold text-indigo-900"
                          : "hover:bg-white text-slate-700"
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className={`rounded-md px-1.5 py-0.5 text-[9px] font-extrabold uppercase ${catColor}`}>
                          {node.category}
                        </span>
                        <span className="truncate">{node.label}</span>
                      </div>
                      <ChevronRight className="h-3 w-3 text-slate-400 shrink-0" />
                    </button>
                  );
                })}
              </div>

              {/* Node Detailed Preview */}
              <div className="md:col-span-2 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between">
                {selectedNode ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-indigo-50 border border-indigo-200 px-3 py-1 text-xs font-bold text-indigo-700 uppercase">
                        {selectedNode.category} Concept
                      </span>
                    </div>

                    <div>
                      <h3 className="text-xl font-bold text-slate-900">{selectedNode.label}</h3>
                      <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                        {selectedNode.description}
                      </p>
                    </div>

                    <div className="rounded-xl border border-slate-100 bg-slate-50 p-3.5 text-xs text-slate-500">
                      <p className="font-semibold text-slate-700 mb-1 flex items-center gap-1">
                        <Info className="h-3.5 w-3.5 text-indigo-600" />
                        Study Tip:
                      </p>
                      <p>
                        In semester examinations, connect <strong>{selectedNode.label}</strong> to its parent concept to secure structured marks.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12 text-center text-xs text-slate-400">
                    <Info className="h-8 w-8 mb-2" />
                    Select a node from the left to inspect its details.
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* ================= MERMAID CODE TAB ================= */
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Mermaid Graph Definition (Can be pasted into GitHub / Notion / Obsidian):</span>
              </div>
              <pre className="rounded-2xl border border-slate-200 bg-slate-900 p-5 text-xs text-emerald-400 font-mono overflow-x-auto leading-relaxed max-h-[380px]">
                {mermaidCode}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

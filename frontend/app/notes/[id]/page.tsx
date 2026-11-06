"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Download,
  Clock,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ArrowLeft,
  MessageSquare,
  Flag,
  FileText,
  Calendar,
  Layers,
  BookOpen,
  Share2,
  BrainCircuit,
  Target,
  Network,
  Lightbulb,
  Compass,
  Headphones,
} from "lucide-react";
import { api, DocumentAnalysis, DocumentItem, ReviewItem } from "@/lib/api";
import { RatingStars, RatingBar } from "@/components/RatingStars";
import { RoleBadge, StatusPill, AiBadge } from "@/components/StatusPill";
import { StudyToolsModal } from "@/components/StudyToolsModal";
import { ExamPredictorModal } from "@/components/ExamPredictorModal";
import { MindMapModal } from "@/components/MindMapModal";
import { SimplifierModal } from "@/components/SimplifierModal";
import { SyllabusGapModal } from "@/components/SyllabusGapModal";
import { AudioPodcastModal } from "@/components/AudioPodcastModal";
import { CheatSheetModal } from "@/components/CheatSheetModal";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const docId = params.id as string;

  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [analysis, setAnalysis] = useState<DocumentAnalysis | null>(null);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Review Form state
  const [stars, setStars] = useState(5);
  const [comment, setComment] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  // Flag Modal state
  const [showFlagModal, setShowFlagModal] = useState(false);
  const [flagReason, setFlagReason] = useState("");
  const [flagSubmitted, setFlagSubmitted] = useState(false);

  // Innovation 1: Study Tools (Flashcards & Quiz) Modal state
  const [showStudyTools, setShowStudyTools] = useState(false);

  // Innovation 2: Exam Question Predictor Modal state
  const [showExamPredictor, setShowExamPredictor] = useState(false);

  // Innovation 3: Concept Mind Map Modal state
  const [showMindMap, setShowMindMap] = useState(false);

  // Innovation 4: Concept Simplifier (ELI5) Modal state
  const [showSimplifier, setShowSimplifier] = useState(false);

  // Innovation 5: Syllabus Gap Heatmap Modal state
  const [showSyllabusGaps, setShowSyllabusGaps] = useState(false);

  // Innovation 6: Audio Study Podcast Modal state
  const [showPodcast, setShowPodcast] = useState(false);

  // New Innovation: 1-Page Exam Cheat Sheet Modal state
  const [showCheatSheet, setShowCheatSheet] = useState(false);

  const fetchDocumentData = async () => {
    try {
      const doc = await api.getDocument(docId);
      setDocument(doc);

      // If document is complete, fetch analysis and reviews
      if (doc.status === "complete") {
        try {
          const a = await api.getAnalysis(docId);
          setAnalysis(a);
        } catch {
          setAnalysis(null);
        }
      }

      try {
        const revs = await api.getReviews(docId);
        setReviews(revs);
      } catch {
        setReviews([]);
      }
    } catch (e: any) {
      setError(e.message || "Failed to load document.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocumentData();
  }, [docId]);

  // Real-time polling every 3 seconds while queued or processing
  useEffect(() => {
    if (!document || (document.status !== "queued" && document.status !== "processing")) {
      return;
    }

    const interval = setInterval(() => {
      fetchDocumentData();
    }, 3000);

    return () => clearInterval(interval);
  }, [document?.status]);

  const handleDownload = async () => {
    try {
      const { download_url, filename } = await api.downloadDocument(docId);
      const link = window.document.createElement("a");
      link.href = download_url;
      link.setAttribute("download", filename);
      window.document.body.appendChild(link);
      link.click();
      link.remove();
      // Increment local count
      if (document) {
        setDocument({ ...document, download_count: document.download_count + 1 });
      }
    } catch (e: any) {
      alert(e.message || "Please sign in to download this document.");
      router.push(`/login?redirect=/notes/${docId}`);
    }
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingReview(true);
    try {
      const newRev = await api.submitReview(docId, { stars, comment });
      setReviews([newRev, ...reviews.filter((r: any) => r.id !== newRev.id)]);
      setComment("");
      alert("Review submitted successfully!");
    } catch (e: any) {
      alert(e.message || "Please sign in to submit a review.");
      router.push(`/login?redirect=/notes/${docId}`);
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleFlagSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flagReason.trim()) return;
    try {
      await api.flagDocument(docId, flagReason);
      setFlagSubmitted(true);
      setTimeout(() => {
        setShowFlagModal(false);
        setFlagSubmitted(false);
        setFlagReason("");
      }, 2000);
    } catch (e: any) {
      alert(e.message || "Failed to flag note. Please sign in.");
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto max-w-5xl px-4 py-20 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent" />
        <p className="mt-4 text-sm font-medium text-slate-500">Loading document details...</p>
      </div>
    );
  }

  if (error || !document) {
    return (
      <div className="container mx-auto max-w-5xl px-4 py-20 text-center">
        <h2 className="text-xl font-bold text-slate-900">Document Not Found</h2>
        <p className="mt-2 text-sm text-slate-500">{error || "This document does not exist."}</p>
        <Link
          href="/notes"
          className="mt-6 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Notes Library
        </Link>
      </div>
    );
  }

  const isPending = document.status === "queued" || document.status === "processing";

  return (
    <div className="container mx-auto max-w-5xl px-4 sm:px-6 py-10">
      {/* Back button */}
      <Link
        href="/notes"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-brand-600 transition mb-6"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Notes Library
      </Link>

      {/* Header Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm mb-8">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="rounded-md bg-brand-50 px-2.5 py-1 text-xs font-bold text-brand-700 border border-brand-100">
                {document.stream_name || "Degree"} • Sem {document.semester_number || 1}
              </span>
              <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                {document.subject_name} • {document.topic_name}
              </span>
              <StatusPill status={document.status} />
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 leading-tight">
              {document.title}
            </h1>

            {document.description && (
              <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                {document.description}
              </p>
            )}

            <div className="mt-5 flex flex-wrap items-center gap-6 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Uploaded by:</span>
                <span className="font-semibold text-slate-700">{document.uploader_name}</span>
                <RoleBadge role={document.uploader_role} />
              </div>
              <div className="flex items-center gap-1">
                <FileText className="h-3.5 w-3.5 text-slate-400 uppercase" />
                <span>{document.file_type} ({(document.file_size / 1024).toFixed(0)} KB)</span>
              </div>
              <div className="flex items-center gap-1">
                <Download className="h-3.5 w-3.5 text-slate-400" />
                <span>{document.download_count} downloads</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2 shrink-0">
            <button
              onClick={() => setShowStudyTools(true)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-600 to-purple-600 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:from-brand-700 hover:to-purple-700 transition"
            >
              <BrainCircuit className="h-4 w-4" /> Flashcards & Quiz
            </button>
            <button
              onClick={() => setShowExamPredictor(true)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:from-amber-600 hover:to-rose-600 transition"
            >
              <Target className="h-4 w-4" /> Exam Questions (2/5/10M)
            </button>
            <button
              onClick={() => setShowMindMap(true)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:from-blue-700 hover:to-cyan-700 transition"
            >
              <Network className="h-4 w-4" /> Concept Mind Map
            </button>
            <button
              onClick={() => setShowSimplifier(true)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:from-emerald-700 hover:to-teal-700 transition"
            >
              <Lightbulb className="h-4 w-4" /> Simplify (ELI5)
            </button>
            <button
              onClick={() => setShowSyllabusGaps(true)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:from-teal-700 hover:to-cyan-700 transition"
            >
              <Compass className="h-4 w-4" /> Syllabus Gaps
            </button>
            <button
              onClick={() => setShowPodcast(true)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:from-violet-700 hover:to-purple-700 transition"
            >
              <Headphones className="h-4 w-4" /> Audio Podcast
            </button>
            <button
              onClick={() => setShowCheatSheet(true)}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-cyan-600 px-5 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md hover:from-emerald-700 hover:to-cyan-700 transition"
            >
              <FileText className="h-4 w-4" /> 1-Page Cheat Sheet
            </button>
            <button
              onClick={handleDownload}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-teal-600 px-5 py-2.5 text-xs sm:text-sm font-semibold text-white shadow-sm hover:bg-teal-700 transition"
            >
              <Download className="h-4 w-4" /> Download File
            </button>
            <button
              onClick={() => setShowFlagModal(true)}
              className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-rose-600 hover:border-rose-200 transition"
            >
              <Flag className="h-3.5 w-3.5" /> Report Issue
            </button>
          </div>
        </div>

        {/* Polling Status Banner */}
        {isPending && (
          <div className="mt-6 flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs font-medium text-amber-800">
            <Clock className="h-4 w-4 animate-spin text-amber-600 shrink-0" />
            <div>
              <p className="font-semibold">AI Academic Analysis in Progress</p>
              <p className="text-amber-700 mt-0.5">
                Our models are currently extracting, verifying, and scoring this document. This page updates automatically every 3 seconds.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* AI Evaluation Section */}
      {analysis && (
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <AiBadge />
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">AI Academic Evaluation Report</h2>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm space-y-8">
            {/* Overall Score Highlight */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 rounded-xl bg-gradient-to-r from-brand-50/80 to-teal-50/80 p-6 border border-brand-100">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-brand-700">
                  Overall Academic Score
                </span>
                <div className="flex items-baseline gap-3 mt-1">
                  <span className="text-4xl font-black text-slate-900">
                    {analysis.overall_score_display.toFixed(1)}
                  </span>
                  <span className="text-sm font-medium text-slate-500">out of 5.0</span>
                </div>
                <div className="mt-2">
                  <RatingStars score={analysis.overall_score_display} size="lg" />
                </div>
              </div>

              <div className="flex flex-col gap-2 sm:text-right">
                <div>
                  <span className="text-xs text-slate-400">Model: </span>
                  <span className="text-xs font-semibold text-slate-700">{analysis.model_name} ({analysis.rubric_version})</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Confidence: </span>
                  <span className="inline-block rounded-md bg-white px-2 py-0.5 text-xs font-bold capitalize text-slate-800 border">
                    {analysis.confidence} Confidence
                  </span>
                </div>
                {analysis.topic_coverage_pct !== null ? (
                  <div>
                    <span className="text-xs text-slate-400">Syllabus Coverage: </span>
                    <span className="text-xs font-bold text-teal-700">
                      {analysis.topic_coverage_pct.toFixed(0)}% Checklist Covered
                    </span>
                  </div>
                ) : (
                  <p className="text-[11px] text-slate-400 italic">
                    No official reference syllabus checklist exists for this subject.
                  </p>
                )}
              </div>
            </div>

            {/* Summary */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">Executive Summary</h3>
              <p className="text-sm text-slate-700 leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100">
                {analysis.summary}
              </p>
            </div>

            {/* 4 Score Dimensions Grid */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">Rubric Dimension Breakdown</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <RatingBar label="Content Accuracy" score={analysis.accuracy_score} />
                <RatingBar label="Explanation Quality" score={analysis.explanation_score} />
                <RatingBar label="Content Depth" score={analysis.depth_score} />
                <RatingBar label="Examples & Illustrations" score={analysis.examples_score} />
              </div>
            </div>

            {/* Topics Identified */}
            {analysis.topics && analysis.topics.length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3">
                  Identified Academic Topics ({analysis.total_topics})
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {analysis.topics.map((t: any, idx: number) => (
                    <div key={idx} className="rounded-xl border border-slate-100 bg-slate-50/50 p-3 text-xs">
                      <span className="font-bold text-slate-800">{t.topic_name}</span>
                      {t.note && <p className="mt-1 text-slate-500">{t.note}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Strengths & Improvements */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths */}
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/40 p-4">
                <div className="flex items-center gap-2 text-xs font-bold text-emerald-800 uppercase tracking-wider mb-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" /> Key Strengths
                </div>
                <ul className="space-y-1.5 text-xs text-slate-700">
                  {analysis.feedback
                    .filter((f: any) => f.kind === "strength")
                    .map((s: any, i: number) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-emerald-500 font-bold">•</span>
                        <span>{s.text}</span>
                      </li>
                    ))}
                </ul>
              </div>

              {/* Improvements */}
              <div className="rounded-xl border border-amber-100 bg-amber-50/40 p-4">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-800 uppercase tracking-wider mb-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600" /> Recommended Improvements
                </div>
                <ul className="space-y-1.5 text-xs text-slate-700">
                  {analysis.feedback
                    .filter((f: any) => f.kind === "improvement")
                    .map((imp: any, i: number) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{imp.text}</span>
                      </li>
                    ))}
                </ul>
              </div>
            </div>

            {/* Missing Concepts */}
            {analysis.feedback.some((f: any) => f.kind === "missing_concept") && (
              <div>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-2">Missing Concepts for Complete Treatment</h3>
                <div className="flex flex-wrap gap-2">
                  {analysis.feedback
                    .filter((f: any) => f.kind === "missing_concept")
                    .map((mc: any, idx: number) => (
                      <span key={idx} className="rounded-lg bg-slate-100 px-3 py-1 text-xs text-slate-700 border">
                        {mc.text}
                      </span>
                    ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Student Reviews Section */}
      <section className="mt-12">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Student Community Reviews</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Peer ratings from undergraduate students (strictly separate from AI evaluations)
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Review Submission Form */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm h-fit">
            <h3 className="text-sm font-bold text-slate-900 mb-4">Leave a Peer Review</h3>
            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Your Rating</label>
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((num) => (
                    <button
                      type="button"
                      key={num}
                      onClick={() => setStars(num)}
                      className={`h-8 w-8 rounded-lg font-bold text-sm transition ${
                        stars >= num
                          ? "bg-amber-400 text-white shadow-sm"
                          : "bg-slate-100 text-slate-400 hover:bg-slate-200"
                      }`}
                    >
                      ★
                    </button>
                  ))}
                  <span className="ml-2 text-xs font-bold text-slate-700">{stars} / 5</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Comment <span className="font-normal text-slate-400">(optional, max 500 chars)</span>
                </label>
                <textarea
                  rows={3}
                  maxLength={500}
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Share feedback on clarity, diagrams, and usefulness..."
                  className="w-full rounded-xl border border-slate-200 p-3 text-xs focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10"
                />
              </div>

              <button
                type="submit"
                disabled={submittingReview}
                className="w-full rounded-xl bg-slate-900 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition disabled:opacity-50"
              >
                {submittingReview ? "Submitting..." : "Submit Review"}
              </button>
            </form>
          </div>

          {/* Reviews List */}
          <div className="md:col-span-2 space-y-4">
            {reviews.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center text-xs text-slate-400">
                No student reviews yet. Be the first to share your thoughts on this note!
              </div>
            ) : (
              reviews.map((rev: any) => (
                <div key={rev.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-xs text-slate-900">{rev.user_name}</span>
                      <RoleBadge role={rev.user_role} />
                    </div>
                    <RatingStars score={rev.stars} size="sm" />
                  </div>
                  {rev.comment && <p className="text-xs text-slate-600 leading-relaxed">{rev.comment}</p>}
                  <span className="text-[10px] text-slate-400 block">
                    {new Date(rev.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </section>

      {/* Flag Modal */}
      {showFlagModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <h3 className="text-base font-bold text-slate-900 mb-2">Report Document</h3>
            <p className="text-xs text-slate-500 mb-4">
              Help us maintain high academic standards. Please describe why this document should be reviewed by moderators.
            </p>

            {flagSubmitted ? (
              <div className="rounded-xl bg-emerald-50 p-4 text-center text-xs font-bold text-emerald-800">
                Thank you. Your report has been submitted for moderation review.
              </div>
            ) : (
              <form onSubmit={handleFlagSubmit} className="space-y-4">
                <textarea
                  rows={4}
                  required
                  value={flagReason}
                  onChange={(e) => setFlagReason(e.target.value)}
                  placeholder="e.g., Copyright violation, incorrect technical formulas, corrupted text..."
                  className="w-full rounded-xl border border-slate-200 p-3 text-xs focus:border-brand-500 focus:outline-none"
                />
                <div className="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowFlagModal(false)}
                    className="rounded-lg px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="rounded-lg bg-rose-600 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-700"
                  >
                    Submit Report
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
      {/* Innovation 1: Interactive Flashcards & Quiz Modal */}
      <StudyToolsModal
        documentId={docId}
        documentTitle={document.title}
        isOpen={showStudyTools}
        onClose={() => setShowStudyTools(false)}
      />

      {/* Innovation 2: Exam Question Predictor Modal */}
      <ExamPredictorModal
        documentId={docId}
        documentTitle={document.title}
        isOpen={showExamPredictor}
        onClose={() => setShowExamPredictor(false)}
      />

      {/* Innovation 3: Concept Mind Map Modal */}
      <MindMapModal
        documentId={docId}
        documentTitle={document.title}
        isOpen={showMindMap}
        onClose={() => setShowMindMap(false)}
      />

      {/* Innovation 4: Concept Simplifier (ELI5) Modal */}
      <SimplifierModal
        documentId={docId}
        documentTitle={document.title}
        isOpen={showSimplifier}
        onClose={() => setShowSimplifier(false)}
      />

      {/* Innovation 5: Syllabus Gap Heatmap Modal */}
      <SyllabusGapModal
        documentId={docId}
        documentTitle={document.title}
        isOpen={showSyllabusGaps}
        onClose={() => setShowSyllabusGaps(false)}
      />

      {/* Innovation 6: Audio Study Podcast Modal */}
      <AudioPodcastModal
        documentId={docId}
        documentTitle={document.title}
        isOpen={showPodcast}
        onClose={() => setShowPodcast(false)}
      />

      {/* New Innovation: 1-Page Exam Cheat Sheet Modal */}
      <CheatSheetModal
        documentId={docId}
        documentTitle={document.title}
        isOpen={showCheatSheet}
        onClose={() => setShowCheatSheet(false)}
      />
    </div>
  );
}

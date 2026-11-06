"use client";

import { useState, useEffect } from "react";
import {
  BrainCircuit,
  Layers,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  CheckCircle2,
  XCircle,
  Award,
  Sparkles,
  X,
  Shuffle,
} from "lucide-react";
import { api, Flashcard, QuizQuestion, StudyPackResponse } from "@/lib/api";

interface StudyToolsModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function StudyToolsModal({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}: StudyToolsModalProps) {
  const [activeTab, setActiveTab] = useState<"flashcards" | "quiz">("flashcards");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flashcards, setFlashcards] = useState<Flashcard[]>([]);
  const [quiz, setQuiz] = useState<QuizQuestion[]>([]);

  // Flashcards state
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  // Quiz state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [isAnswerSubmitted, setIsAnswerSubmitted] = useState(false);
  const [userScore, setUserScore] = useState(0);
  const [quizCompleted, setQuizCompleted] = useState(false);

  useEffect(() => {
    if (!isOpen) return;

    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getStudyTools(documentId)
      .then((data: StudyPackResponse) => {
        if (mounted) {
          setFlashcards(data.flashcards || []);
          setQuiz(data.quiz || []);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || "Failed to load study tools.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [documentId, isOpen]);

  // Reset quiz
  const handleResetQuiz = () => {
    setCurrentQuestionIndex(0);
    setSelectedOption(null);
    setIsAnswerSubmitted(false);
    setUserScore(0);
    setQuizCompleted(false);
  };

  // Select quiz option
  const handleSelectOption = (idx: number) => {
    if (isAnswerSubmitted) return;
    setSelectedOption(idx);
    setIsAnswerSubmitted(true);
    if (quiz[currentQuestionIndex] && idx === quiz[currentQuestionIndex].correct_index) {
      setUserScore((prev) => prev + 1);
    }
  };

  // Next question
  const handleNextQuestion = () => {
    if (currentQuestionIndex < quiz.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
      setSelectedOption(null);
      setIsAnswerSubmitted(false);
    } else {
      setQuizCompleted(true);
    }
  };

  // Shuffle flashcards
  const handleShuffleCards = () => {
    setFlashcards((prev) => [...prev].sort(() => Math.random() - 0.5));
    setCurrentCardIndex(0);
    setIsFlipped(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-3xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-brand-50/60 to-purple-50/60 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand-600 text-white shadow-md">
              <BrainCircuit className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-brand-600">
                  AI Study Mode
                </span>
                <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-700">
                  Innovation 1
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

        {/* Tab Switcher */}
        <div className="flex border-b border-slate-100 px-6 bg-slate-50/50">
          <button
            onClick={() => setActiveTab("flashcards")}
            className={`flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-bold transition ${
              activeTab === "flashcards"
                ? "border-brand-600 text-brand-600 bg-white shadow-sm"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <Layers className="h-4 w-4" />
            Concept Flashcards ({flashcards.length})
          </button>
          <button
            onClick={() => setActiveTab("quiz")}
            className={`flex items-center gap-2 border-b-2 py-3 px-4 text-xs font-bold transition ${
              activeTab === "quiz"
                ? "border-brand-600 text-brand-600 bg-white shadow-sm"
                : "border-transparent text-slate-500 hover:text-slate-800"
            }`}
          >
            <HelpCircle className="h-4 w-4" />
            Self-Assessment Quiz ({quiz.length})
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
              <p className="text-xs font-semibold text-slate-600">
                AI is generating your grounded Flashcards and Quiz...
              </p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
              <p className="font-bold">Error loading study tools</p>
              <p className="mt-1">{error}</p>
            </div>
          ) : activeTab === "flashcards" ? (
            /* ================= FLASHCARDS TAB ================= */
            <div className="flex flex-col items-center">
              <div className="w-full flex items-center justify-between text-xs text-slate-500 mb-4 px-2">
                <span className="font-semibold">
                  Card {currentCardIndex + 1} of {flashcards.length}
                </span>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-semibold text-slate-600">
                    {flashcards[currentCardIndex]?.topic || "Concept"}
                  </span>
                  <button
                    onClick={handleShuffleCards}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 px-2.5 py-1 text-[11px] font-semibold text-slate-600 hover:bg-slate-50 transition"
                  >
                    <Shuffle className="h-3 w-3" /> Shuffle
                  </button>
                </div>
              </div>

              {/* Flashcard container */}
              <div
                onClick={() => setIsFlipped(!isFlipped)}
                className="cursor-pointer group relative w-full min-h-[260px] rounded-2xl border-2 border-dashed border-brand-200 bg-gradient-to-br from-white to-slate-50 p-8 shadow-md hover:shadow-lg transition-all duration-300 flex flex-col items-center justify-center text-center"
              >
                <div className="absolute top-4 right-4 text-[10px] font-bold text-slate-400 group-hover:text-brand-600 transition">
                  {isFlipped ? "CLICK TO SEE PROMPT" : "CLICK TO REVEAL ANSWER"}
                </div>

                {!isFlipped ? (
                  <div className="space-y-3">
                    <span className="inline-block rounded-full bg-brand-50 px-3 py-1 text-xs font-bold text-brand-700">
                      Question / Concept
                    </span>
                    <h3 className="text-lg sm:text-xl font-bold text-slate-900 leading-relaxed max-w-lg">
                      {flashcards[currentCardIndex]?.front}
                    </h3>
                    <p className="text-xs text-slate-400 mt-4">
                      Tap card to flip and verify your understanding
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 animate-in fade-in zoom-in-95 duration-200">
                    <span className="inline-block rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                      Definition & Key Takeaway
                    </span>
                    <p className="text-sm sm:text-base font-semibold text-slate-800 leading-relaxed max-w-lg">
                      {flashcards[currentCardIndex]?.back}
                    </p>
                  </div>
                )}
              </div>

              {/* Navigation controls */}
              <div className="flex items-center gap-4 mt-6">
                <button
                  disabled={currentCardIndex === 0}
                  onClick={() => {
                    setCurrentCardIndex((prev) => prev - 1);
                    setIsFlipped(false);
                  }}
                  className="flex items-center gap-1 rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 disabled:opacity-40 transition"
                >
                  <ChevronLeft className="h-4 w-4" /> Previous
                </button>
                <button
                  onClick={() => setIsFlipped(!isFlipped)}
                  className="rounded-xl bg-brand-50 px-4 py-2 text-xs font-bold text-brand-700 hover:bg-brand-100 transition"
                >
                  {isFlipped ? "Show Prompt" : "Flip Card"}
                </button>
                <button
                  disabled={currentCardIndex === flashcards.length - 1}
                  onClick={() => {
                    setCurrentCardIndex((prev) => prev + 1);
                    setIsFlipped(false);
                  }}
                  className="flex items-center gap-1 rounded-xl bg-brand-600 px-4 py-2 text-xs font-bold text-white hover:bg-brand-700 disabled:opacity-40 transition"
                >
                  Next <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          ) : (
            /* ================= QUIZ TAB ================= */
            <div>
              {!quizCompleted ? (
                <div>
                  <div className="flex items-center justify-between text-xs text-slate-500 mb-3">
                    <span className="font-semibold">
                      Question {currentQuestionIndex + 1} of {quiz.length}
                    </span>
                    <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-bold uppercase text-slate-600">
                      {quiz[currentQuestionIndex]?.difficulty}
                    </span>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full bg-slate-100 rounded-full h-1.5 mb-6 overflow-hidden">
                    <div
                      className="bg-brand-600 h-1.5 rounded-full transition-all duration-300"
                      style={{
                        width: `${((currentQuestionIndex + 1) / quiz.length) * 100}%`,
                      }}
                    />
                  </div>

                  {/* Question */}
                  <h3 className="text-base sm:text-lg font-bold text-slate-900 mb-4 leading-snug">
                    {quiz[currentQuestionIndex]?.question}
                  </h3>

                  {/* Options */}
                  <div className="space-y-3">
                    {quiz[currentQuestionIndex]?.options.map((opt, idx) => {
                      const isSelected = selectedOption === idx;
                      const isCorrect = idx === quiz[currentQuestionIndex]?.correct_index;

                      let btnStyle = "border-slate-200 bg-white hover:border-brand-300 text-slate-800";
                      if (isAnswerSubmitted) {
                        if (isCorrect) {
                          btnStyle = "border-emerald-500 bg-emerald-50 text-emerald-900 font-bold shadow-sm";
                        } else if (isSelected) {
                          btnStyle = "border-rose-400 bg-rose-50 text-rose-900";
                        } else {
                          btnStyle = "border-slate-200 bg-slate-50 text-slate-400 opacity-60";
                        }
                      }

                      return (
                        <button
                          key={idx}
                          disabled={isAnswerSubmitted}
                          onClick={() => handleSelectOption(idx)}
                          className={`w-full text-left rounded-2xl border p-3.5 text-xs sm:text-sm transition flex items-start gap-3 ${btnStyle}`}
                        >
                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-xs font-bold text-slate-700">
                            {String.fromCharCode(65 + idx)}
                          </span>
                          <span className="mt-0.5 flex-1">{opt}</span>
                          {isAnswerSubmitted && isCorrect && (
                            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
                          )}
                          {isAnswerSubmitted && isSelected && !isCorrect && (
                            <XCircle className="h-5 w-5 text-rose-500 shrink-0" />
                          )}
                        </button>
                      );
                    })}
                  </div>

                  {/* Explanation after answering */}
                  {isAnswerSubmitted && (
                    <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 text-xs animate-in fade-in duration-200">
                      <p className="font-bold text-slate-900 mb-1 flex items-center gap-1.5">
                        <Sparkles className="h-3.5 w-3.5 text-brand-600" />
                        Explanation & Grounded Evidence:
                      </p>
                      <p className="text-slate-600 leading-relaxed">
                        {quiz[currentQuestionIndex]?.explanation}
                      </p>
                      <div className="mt-4 flex justify-end">
                        <button
                          onClick={handleNextQuestion}
                          className="rounded-xl bg-brand-600 px-5 py-2 text-xs font-bold text-white shadow-md hover:bg-brand-700 transition"
                        >
                          {currentQuestionIndex < quiz.length - 1
                            ? "Next Question →"
                            : "View Scorecard"}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* ================= SCORECARD ================= */
                <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
                  <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-amber-50 text-amber-500 shadow-md">
                    <Award className="h-8 w-8" />
                  </div>
                  <div>
                    <h3 className="text-xl font-extrabold text-slate-900">Quiz Completed!</h3>
                    <p className="text-xs text-slate-500 mt-1">Here is your active recall score</p>
                  </div>

                  <div className="rounded-2xl border border-slate-100 bg-slate-50 px-8 py-4">
                    <span className="text-3xl font-extrabold text-brand-600">
                      {userScore} / {quiz.length}
                    </span>
                    <span className="block text-xs font-semibold text-slate-500 mt-1">
                      {Math.round((userScore / quiz.length) * 100)}% Accuracy
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 max-w-sm leading-relaxed">
                    {userScore === quiz.length
                      ? "🎉 Perfect score! You have thoroughly mastered the concepts in this note."
                      : userScore >= Math.ceil(quiz.length / 2)
                      ? "👍 Solid understanding! Flip through the flashcards once to solidify the remaining points."
                      : "📖 Good practice effort. Review the flashcards and re-read the core concepts before re-attempting."}
                  </p>

                  <div className="flex items-center gap-3 mt-4">
                    <button
                      onClick={handleResetQuiz}
                      className="flex items-center gap-1.5 rounded-xl border border-slate-200 px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 transition"
                    >
                      <RotateCcw className="h-3.5 w-3.5" /> Retake Quiz
                    </button>
                    <button
                      onClick={() => setActiveTab("flashcards")}
                      className="rounded-xl bg-brand-600 px-5 py-2.5 text-xs font-bold text-white shadow-md hover:bg-brand-700 transition"
                    >
                      Review Flashcards
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

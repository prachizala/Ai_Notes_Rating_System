"use client";

import React, { useState, useEffect, useRef } from "react";
import { api, VivaQuestion, VivaSessionResponse, VivaEvaluationResponse } from "@/lib/api";

interface VivaVoceModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

interface QuestionResult {
  question: VivaQuestion;
  studentAnswer: string;
  evaluation: VivaEvaluationResponse;
}

export const VivaVoceModal: React.FC<VivaVoceModalProps> = ({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [vivaData, setVivaData] = useState<VivaSessionResponse | null>(null);
  
  // Session progression
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [studentAnswer, setStudentAnswer] = useState<string>("");
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [currentEvaluation, setCurrentEvaluation] = useState<VivaEvaluationResponse | null>(null);
  const [sessionResults, setSessionResults] = useState<QuestionResult[]>([]);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);

  // Audio / Speech State
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const recognitionRef = useRef<any>(null);

  // Load questions when modal opens
  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);
    setError(null);
    setIsCompleted(false);
    setSessionResults([]);
    setCurrentIndex(0);
    setStudentAnswer("");
    setCurrentEvaluation(null);

    api
      .getVivaQuestions(documentId)
      .then((res: VivaSessionResponse) => {
        if (isMounted) {
          setVivaData(res);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || "Failed to initialize viva session.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // ignore
        }
      }
    };
  }, [isOpen, documentId]);

  // Read question out loud
  const handleSpeakQuestion = () => {
    if (!("speechSynthesis" in window) || !vivaData) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const currentQ = vivaData.questions[currentIndex];
    if (!currentQ) return;

    const utterance = new SpeechSynthesisUtterance(currentQ.question);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  // Toggle voice recognition
  const handleToggleVoiceRecording = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser. Please type your answer.");
      return;
    }

    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: any) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setStudentAnswer((prev) => (prev ? `${prev} ${transcript}` : transcript));
      };

      recognition.onerror = () => {
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Speech recognition error:", err);
      setIsRecording(false);
    }
  };

  // Evaluate current answer
  const handleSubmitAnswer = async () => {
    if (!studentAnswer.trim() || !vivaData) return;

    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
    if (isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsRecording(false);
    }

    setEvaluating(true);
    const currentQ = vivaData.questions[currentIndex];

    try {
      const evaluation = await api.evaluateVivaAnswer(documentId, {
        question: currentQ.question,
        student_answer: studentAnswer,
        ideal_answer_key: currentQ.ideal_answer_key,
        difficulty: currentQ.difficulty,
      });

      setCurrentEvaluation(evaluation);
      setSessionResults((prev) => [
        ...prev,
        {
          question: currentQ,
          studentAnswer,
          evaluation,
        },
      ]);
    } catch (err: any) {
      alert(err.message || "Failed to evaluate answer. Please try again.");
    } finally {
      setEvaluating(false);
    }
  };

  // Move to next question or complete
  const handleNextQuestion = () => {
    if (!vivaData) return;

    if (currentIndex + 1 < vivaData.questions.length) {
      setCurrentIndex((prev) => prev + 1);
      setStudentAnswer("");
      setCurrentEvaluation(null);
    } else {
      setIsCompleted(true);
    }
  };

  // Restart session
  const handleRestart = () => {
    setCurrentIndex(0);
    setStudentAnswer("");
    setCurrentEvaluation(null);
    setSessionResults([]);
    setIsCompleted(false);
  };

  if (!isOpen) return null;

  const currentQ = vivaData?.questions[currentIndex];
  const totalScore = sessionResults.reduce((acc, curr) => acc + curr.evaluation.score, 0);
  const maxPossibleScore = (vivaData?.questions.length || 4) * 10;
  const percentage = maxPossibleScore > 0 ? Math.round((totalScore / maxPossibleScore) * 100) : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col max-h-[92vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-indigo-500/10 dark:from-amber-950/20 dark:via-orange-950/20 dark:to-indigo-950/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center font-bold text-xl shadow-md shadow-amber-500/20">
              🎓
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  AI Viva Voce & Oral Exam Simulator
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-700/50">
                  External Examiner Panel
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-md">
                Testing conceptual understanding on: <span className="font-medium text-slate-700 dark:text-slate-300">{documentTitle}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Body content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-base font-semibold text-slate-800 dark:text-slate-200">
                Professor is reviewing the document...
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Formulating oral exam questions, examiner tips, and model answers.
              </p>
            </div>
          ) : error ? (
            <div className="p-6 text-center">
              <div className="inline-flex p-3 rounded-full bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 mb-3 text-2xl">
                ⚠️
              </div>
              <p className="text-sm text-rose-600 dark:text-rose-400 font-medium mb-4">{error}</p>
              <button
                onClick={() => {
                  setLoading(true);
                  setError(null);
                  api
                    .getVivaQuestions(documentId)
                    .then((res: VivaSessionResponse) => {
                      setVivaData(res);
                      setLoading(false);
                    })
                    .catch((err: any) => {
                      setError(err.message || "Retry failed.");
                      setLoading(false);
                    });
                }}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium transition"
              >
                Retry Viva Generation
              </button>
            </div>
          ) : isCompleted ? (
            /* Final Viva Marksheet */
            <div className="max-w-2xl mx-auto py-4 text-center">
              <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-tr from-amber-500 to-indigo-600 text-white flex items-center justify-center text-3xl shadow-xl shadow-amber-500/20 mb-4 animate-bounce">
                📜
              </div>
              <h3 className="text-2xl font-extrabold text-slate-900 dark:text-white">
                Viva Voce Assessment Complete!
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                Official grading results from the University Viva Voce Panel
              </p>

              {/* Score Card */}
              <div className="mt-6 p-6 rounded-2xl bg-gradient-to-br from-slate-50 to-amber-50/50 dark:from-slate-800/80 dark:to-amber-950/20 border border-amber-200/60 dark:border-amber-800/40 shadow-sm">
                <div className="flex items-center justify-around">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Total Viva Score
                    </p>
                    <p className="text-4xl font-black text-amber-600 dark:text-amber-400 mt-1">
                      {totalScore} <span className="text-lg font-medium text-slate-400">/ {maxPossibleScore}</span>
                    </p>
                  </div>
                  <div className="h-12 w-px bg-slate-200 dark:bg-slate-700" />
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                      Examiner Grade
                    </p>
                    <p className="text-lg font-bold mt-1 text-slate-800 dark:text-slate-200">
                      {percentage >= 80 ? (
                        <span className="text-emerald-600 dark:text-emerald-400">Distinction (10/10)</span>
                      ) : percentage >= 60 ? (
                        <span className="text-indigo-600 dark:text-indigo-400">First Class</span>
                      ) : (
                        <span className="text-amber-600 dark:text-amber-400">Pass / Needs Revision</span>
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* Questions Recap */}
              <div className="mt-6 text-left space-y-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Question Breakdown
                </h4>
                {sessionResults.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-800 flex items-start justify-between gap-4"
                  >
                    <div className="flex-1">
                      <p className="text-xs font-bold text-amber-600 dark:text-amber-400">
                        Q{idx + 1} ({item.question.difficulty})
                      </p>
                      <p className="text-sm font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                        {item.question.question}
                      </p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 italic">
                        &quot;{item.evaluation.feedback}&quot;
                      </p>
                    </div>
                    <div className="text-right">
                      <span className="px-2.5 py-1 text-xs font-bold rounded-lg bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                        {item.evaluation.score}/10
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="mt-8 flex justify-center gap-4">
                <button
                  onClick={handleRestart}
                  className="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-sm font-semibold shadow-md transition"
                >
                  🔄 Retake Viva Voce
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-2.5 bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 rounded-xl text-sm font-semibold transition"
                >
                  Done
                </button>
              </div>
            </div>
          ) : currentQ ? (
            /* Active Question Stage */
            <div className="space-y-6">
              {/* Progress & Indicator */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="px-2.5 py-1 text-xs font-bold rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                    Question {currentIndex + 1} of {vivaData.questions.length}
                  </span>
                  <span
                    className={`px-2 py-0.5 text-xs font-semibold rounded-md border ${
                      currentQ.difficulty === "Easy"
                        ? "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800"
                        : currentQ.difficulty === "Medium"
                        ? "bg-indigo-50 dark:bg-indigo-950/30 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800"
                        : "bg-rose-50 dark:bg-rose-950/30 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800"
                    }`}
                  >
                    {currentQ.difficulty}
                  </span>
                </div>

                {/* Audio Readout */}
                <button
                  onClick={handleSpeakQuestion}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                    isSpeaking
                      ? "bg-amber-500 text-white border-amber-600 animate-pulse"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700"
                  }`}
                  title="Listen to the question"
                >
                  {isSpeaking ? "⏹️ Stop Voice" : "🔊 Read Out Loud"}
                </button>
              </div>

              {/* Examiner Question Box */}
              <div className="p-5 rounded-2xl bg-gradient-to-r from-amber-50/60 via-slate-50 to-indigo-50/60 dark:from-slate-800/90 dark:via-slate-800/70 dark:to-indigo-950/30 border border-slate-200/80 dark:border-slate-700/80 shadow-sm relative">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-2xl bg-amber-500 text-white flex-shrink-0 flex items-center justify-center text-xl shadow-md">
                    👨‍🏫
                  </div>
                  <div className="flex-1">
                    <p className="text-xs font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400">
                      Examiner Asks:
                    </p>
                    <p className="text-base font-semibold text-slate-900 dark:text-white mt-1 leading-relaxed">
                      &quot;{currentQ.question}&quot;
                    </p>
                    <div className="mt-3 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400 bg-white/70 dark:bg-slate-900/60 px-3 py-2 rounded-lg border border-slate-200/60 dark:border-slate-800">
                      <span>💡 <strong>Examiner Tip:</strong> {currentQ.examiner_tip}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Answer Input Area (Only when not evaluated yet) */}
              {!currentEvaluation ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      Your Spoken / Written Response:
                    </label>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={handleToggleVoiceRecording}
                        className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition border ${
                          isRecording
                            ? "bg-rose-500 text-white border-rose-600 animate-pulse shadow-md shadow-rose-500/20"
                            : "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800 hover:bg-indigo-100"
                        }`}
                      >
                        {isRecording ? "🔴 Listening... (Click to stop)" : "🎙️ Speak to Answer"}
                      </button>
                    </div>
                  </div>

                  <textarea
                    value={studentAnswer}
                    onChange={(e) => setStudentAnswer(e.target.value)}
                    placeholder="Speak into your microphone or type your answer clearly as you would in an oral exam..."
                    rows={5}
                    className="w-full p-4 text-sm rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition resize-none leading-relaxed"
                  />

                  <div className="flex items-center justify-between pt-1">
                    <p className="text-xs text-slate-400">
                      Words: {studentAnswer.trim() ? studentAnswer.trim().split(/\s+/).length : 0}
                    </p>
                    <button
                      onClick={handleSubmitAnswer}
                      disabled={evaluating || !studentAnswer.trim()}
                      className="px-6 py-2.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-700 hover:to-orange-700 disabled:opacity-50 text-white text-sm font-semibold rounded-xl shadow-md transition flex items-center gap-2"
                    >
                      {evaluating ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                          <span>Examiner is Evaluating...</span>
                        </>
                      ) : (
                        <>
                          <span>Submit for Viva Grading</span>
                          <span>→</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                /* Evaluation & Feedback Card */
                <div className="space-y-5 animate-in fade-in slide-in-from-bottom-3 duration-200">
                  <div className="p-5 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-md">
                    {/* Score header */}
                    <div className="flex items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-700">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                            Examiner Verdict:
                          </span>
                          <span className="text-sm font-extrabold text-slate-900 dark:text-white">
                            {currentEvaluation.examiner_verdict}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {currentEvaluation.feedback}
                        </p>
                      </div>
                      <div className="text-center pl-4">
                        <div
                          className={`text-2xl font-black px-3.5 py-1.5 rounded-xl border ${
                            currentEvaluation.score >= 8
                              ? "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800"
                              : currentEvaluation.score >= 5
                              ? "bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 border-amber-200 dark:border-amber-800"
                              : "bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border-rose-200 dark:border-rose-800"
                          }`}
                        >
                          {currentEvaluation.score} <span className="text-xs font-medium text-slate-400">/ 10</span>
                        </div>
                      </div>
                    </div>

                    {/* Breakdown */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 text-xs">
                      {/* Strengths */}
                      <div className="p-3.5 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-900/40">
                        <p className="font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5 mb-2">
                          <span>✅</span> What You Nailed
                        </p>
                        <ul className="space-y-1 text-slate-700 dark:text-slate-300">
                          {currentEvaluation.strengths.map((s, i) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="text-emerald-500">•</span>
                              <span>{s}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Missing Points */}
                      <div className="p-3.5 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
                        <p className="font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1.5 mb-2">
                          <span>⚠️</span> Examiner Was Looking For
                        </p>
                        <ul className="space-y-1 text-slate-700 dark:text-slate-300">
                          {currentEvaluation.missing_key_points.map((m, i) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="text-amber-500">•</span>
                              <span>{m}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>

                    {/* Model Answer */}
                    <div className="mt-4 p-3.5 rounded-xl bg-indigo-50/50 dark:bg-indigo-950/20 border border-indigo-200/60 dark:border-indigo-900/40">
                      <p className="text-xs font-bold text-indigo-900 dark:text-indigo-300 flex items-center gap-1.5 mb-1">
                        <span>🌟</span> Model 10/10 Viva Answer:
                      </p>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed italic">
                        &quot;{currentEvaluation.improved_answer}&quot;
                      </p>
                    </div>

                    {/* Follow-up teaser */}
                    {currentQ.follow_up_hint && (
                      <div className="mt-3 px-3 py-2 rounded-lg bg-slate-50 dark:bg-slate-900 text-xs text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800">
                        🎯 <strong>Examiner Follow-Up Probing Tip:</strong> {currentQ.follow_up_hint}
                      </div>
                    )}
                  </div>

                  {/* Next Step Controls */}
                  <div className="flex justify-end gap-3">
                    <button
                      onClick={handleNextQuestion}
                      className="px-6 py-2.5 bg-gradient-to-r from-amber-600 to-indigo-600 hover:from-amber-700 hover:to-indigo-700 text-white rounded-xl text-sm font-semibold shadow-md transition flex items-center gap-2"
                    >
                      <span>
                        {currentIndex + 1 < vivaData.questions.length
                          ? "Proceed to Next Viva Question"
                          : "View Final Viva Marksheet"}
                      </span>
                      <span>→</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

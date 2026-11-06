"use client";

import React, { useState, useEffect } from "react";
import { api, DayPlan, StudyPlannerResponse } from "@/lib/api";

interface StudyPlannerModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
  onOpenTool?: (toolName: string) => void;
}

export const StudyPlannerModal: React.FC<StudyPlannerModalProps> = ({
  documentId,
  documentTitle,
  isOpen,
  onClose,
  onOpenTool,
}) => {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<StudyPlannerResponse | null>(null);
  const [selectedDayIndex, setSelectedDayIndex] = useState<number>(0);
  const [completedTasks, setCompletedTasks] = useState<{ [key: string]: boolean }>({});

  useEffect(() => {
    if (!isOpen) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    // Load persisted tasks from localStorage
    try {
      const saved = localStorage.getItem(`noteiq_planner_${documentId}`);
      if (saved) {
        setCompletedTasks(JSON.parse(saved));
      }
    } catch {
      // ignore
    }

    api
      .getStudyPlanner(documentId)
      .then((res: StudyPlannerResponse) => {
        if (isMounted) {
          setPlan(res);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (isMounted) {
          setError(err.message || "Failed to generate 7-day study planner.");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, documentId]);

  const toggleTask = (taskKey: string) => {
    setCompletedTasks((prev) => {
      const updated = { ...prev, [taskKey]: !prev[taskKey] };
      try {
        localStorage.setItem(`noteiq_planner_${documentId}`, JSON.stringify(updated));
      } catch {
        // ignore
      }
      return updated;
    });
  };

  const handlePrint = () => {
    window.print();
  };

  if (!isOpen) return null;

  const currentDay: DayPlan | undefined = plan?.days[selectedDayIndex];

  // Calculate overall task completion percentage
  let totalTasksCount = 0;
  let doneTasksCount = 0;
  if (plan) {
    plan.days.forEach((d) => {
      d.tasks.forEach((_, tIdx) => {
        totalTasksCount++;
        const key = `d${d.day_number}_t${tIdx}`;
        if (completedTasks[key]) {
          doneTasksCount++;
        }
      });
    });
  }
  const completionPercentage =
    totalTasksCount > 0 ? Math.round((doneTasksCount / totalTasksCount) * 100) : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 flex flex-col max-h-[92vh] overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800 bg-gradient-to-r from-blue-500/10 via-indigo-500/10 to-teal-500/10 dark:from-blue-950/20 dark:via-indigo-950/20 dark:to-teal-950/20">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-xl shadow-md shadow-blue-500/20">
              📅
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900 dark:text-white">
                  7-Day Spaced Repetition Exam Study Planner
                </h2>
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 border border-blue-200 dark:border-blue-800">
                  Ebbinghaus Curve
                </span>
              </div>
              <p className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-md">
                Course: <span className="font-medium text-slate-700 dark:text-slate-300">{plan?.subject_name || "Academic Subject"}</span> • Note: <span className="font-medium text-slate-700 dark:text-slate-300">{documentTitle}</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrint}
              className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 transition flex items-center gap-1.5"
            >
              <span>🖨️</span>
              <span>Print Schedule</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
              aria-label="Close"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-base font-semibold text-slate-800 dark:text-slate-200">
                Synthesizing Spaced Repetition Timetable...
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                Aligning daily intervals, active recall challenges, and exam question weightages.
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
                  api
                    .getStudyPlanner(documentId)
                    .then((res: StudyPlannerResponse) => {
                      setPlan(res);
                      setLoading(false);
                    })
                    .catch((err: any) => {
                      setError(err.message || "Retry failed.");
                      setLoading(false);
                    });
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition"
              >
                Retry Generation
              </button>
            </div>
          ) : plan ? (
            <>
              {/* Progress & Overview Summary Bar */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-blue-50/70 via-indigo-50/50 to-teal-50/70 dark:from-slate-800/80 dark:via-slate-800/60 dark:to-teal-950/20 border border-blue-200/60 dark:border-blue-900/40">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-700 dark:text-blue-400">
                        Cognitive Strategy
                      </span>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300">
                        {plan.total_estimated_hours} Hours Total
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed max-w-xl">
                      {plan.planner_strategy}
                    </p>
                  </div>
                  <div className="sm:text-right shrink-0">
                    <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                      Revision Progress
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="w-28 h-2.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
                        <div
                          className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                          style={{ width: `${completionPercentage}%` }}
                        />
                      </div>
                      <span className="text-xs font-black text-blue-600 dark:text-blue-400">
                        {completionPercentage}%
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {doneTasksCount} of {totalTasksCount} tasks completed
                    </p>
                  </div>
                </div>
              </div>

              {/* Day Selector Pills (Day 1 to 7) */}
              <div className="grid grid-cols-7 gap-2">
                {plan.days.map((d, idx) => {
                  const isSelected = selectedDayIndex === idx;
                  const allDayTasksDone = d.tasks.every(
                    (_, tIdx) => completedTasks[`d${d.day_number}_t${tIdx}`]
                  );

                  return (
                    <button
                      key={d.day_number}
                      onClick={() => setSelectedDayIndex(idx)}
                      className={`p-2.5 rounded-xl text-center border transition relative flex flex-col items-center ${
                        isSelected
                          ? "bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-500/20 font-bold"
                          : allDayTasksDone
                          ? "bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800 hover:bg-emerald-100"
                          : "bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-750"
                      }`}
                    >
                      <span className="text-xs font-extrabold uppercase">Day {d.day_number}</span>
                      <span className="text-[10px] opacity-80 mt-0.5">{d.estimated_minutes}m</span>
                      {allDayTasksDone && (
                        <span className="absolute -top-1.5 -right-1.5 w-4 h-4 rounded-full bg-emerald-500 text-white text-[10px] flex items-center justify-center font-bold shadow">
                          ✓
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Selected Day Details Card */}
              {currentDay && (
                <div className="p-6 rounded-2xl bg-white dark:bg-slate-800/90 border border-slate-200 dark:border-slate-700 shadow-sm space-y-5 animate-in fade-in duration-150">
                  {/* Day Header */}
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 dark:border-slate-700 gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-extrabold uppercase tracking-wider text-blue-600 dark:text-blue-400">
                          Day {currentDay.day_number} Focus
                        </span>
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">
                          ⏱️ {currentDay.estimated_minutes} Minutes
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
                        {currentDay.theme}
                      </h3>
                    </div>

                    {/* Tool Recommendation */}
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-slate-400 font-medium">Recommended Tool:</span>
                      <span className="px-3 py-1 rounded-lg text-xs font-bold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                        ⚡ {currentDay.recommended_tool}
                      </span>
                    </div>
                  </div>

                  {/* Focus Topics Chips */}
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                      Target Concepts for Today:
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {currentDay.focus_topics.map((topic, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 text-xs font-medium rounded-md bg-blue-50 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-900/40"
                        >
                          📌 {topic}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Actionable Learning Tasks */}
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                      Action Checklist:
                    </p>
                    <div className="space-y-2.5">
                      {currentDay.tasks.map((task, tIdx) => {
                        const key = `d${currentDay.day_number}_t${tIdx}`;
                        const isDone = !!completedTasks[key];

                        return (
                          <div
                            key={tIdx}
                            onClick={() => toggleTask(key)}
                            className={`p-3 rounded-xl border flex items-start gap-3 cursor-pointer transition ${
                              isDone
                                ? "bg-emerald-50/50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800 text-slate-500 dark:text-slate-400 line-through"
                                : "bg-slate-50/70 dark:bg-slate-850 border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-750"
                            }`}
                          >
                            <input
                              type="checkbox"
                              checked={isDone}
                              onChange={() => toggleTask(key)}
                              className="mt-0.5 h-4 w-4 rounded text-blue-600 focus:ring-blue-500 cursor-pointer"
                            />
                            <span className="text-sm font-medium leading-relaxed">{task}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Active Recall Challenge Card */}
                  <div className="p-4 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
                    <p className="text-xs font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1.5 mb-1">
                      <span>🧠</span> Evening Active Recall Self-Test
                    </p>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                      &quot;{currentDay.recall_challenge}&quot;
                    </p>
                  </div>
                </div>
              )}

              {/* General Exam Day Scoring Tips */}
              <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1.5">
                  <span>💡</span> University Exam Hall Writing Tips
                </p>
                <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-300">
                  {plan.general_exam_tips.map((tip, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-blue-500 font-bold">•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};

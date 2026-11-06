"use client";

import { useState, useEffect, useRef } from "react";
import {
  Headphones,
  X,
  Play,
  Pause,
  RotateCcw,
  Volume2,
  VolumeX,
  FastForward,
  Copy,
  Check,
  Sparkles,
  BookOpen,
  User,
  Radio,
} from "lucide-react";
import { api, AudioPodcastResponse, PodcastTurn } from "@/lib/api";

interface AudioPodcastModalProps {
  documentId: string;
  documentTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

export function AudioPodcastModal({
  documentId,
  documentTitle,
  isOpen,
  onClose,
}: AudioPodcastModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [podcastData, setPodcastData] = useState<AudioPodcastResponse | null>(null);

  // Playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTurnIdx, setCurrentTurnIdx] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [copiedTranscript, setCopiedTranscript] = useState(false);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (!isOpen) {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setIsPlaying(false);
      return;
    }

    let mounted = true;
    setLoading(true);
    setError(null);

    api
      .getAudioPodcast(documentId)
      .then((res: AudioPodcastResponse) => {
        if (mounted) {
          setPodcastData(res);
          setCurrentTurnIdx(0);
          setLoading(false);
        }
      })
      .catch((err: any) => {
        if (mounted) {
          setError(err.message || "Failed to load study podcast.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [documentId, isOpen]);

  // Play current turn using Web Speech API
  const speakTurn = (turnIndex: number, turnsList: PodcastTurn[]) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;

    window.speechSynthesis.cancel();

    if (turnIndex >= turnsList.length) {
      setIsPlaying(false);
      setCurrentTurnIdx(0);
      return;
    }

    const currentTurn = turnsList[turnIndex];
    const utterance = new SpeechSynthesisUtterance(currentTurn.text);
    utteranceRef.current = utterance;

    utterance.rate = playbackSpeed;

    // Pitch & Voice styling: Alex (higher/host) vs Sam (grounded specialist)
    if (currentTurn.speaker.toLowerCase().includes("alex")) {
      utterance.pitch = 1.15;
    } else {
      utterance.pitch = 0.9;
    }

    // Attempt to pick matching gender voices if browser supports it
    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
      const englishVoices = voices.filter((v) => v.lang.startsWith("en"));
      if (englishVoices.length >= 2) {
        utterance.voice =
          currentTurn.speaker.toLowerCase().includes("alex")
            ? englishVoices[0]
            : englishVoices[1];
      }
    }

    utterance.onend = () => {
      if (turnIndex + 1 < turnsList.length) {
        setCurrentTurnIdx(turnIndex + 1);
        speakTurn(turnIndex + 1, turnsList);
      } else {
        setIsPlaying(false);
        setCurrentTurnIdx(0);
      }
    };

    utterance.onerror = () => {
      setIsPlaying(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  const handleTogglePlay = () => {
    if (!podcastData || !podcastData.turns.length) return;

    if (isPlaying) {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      speakTurn(currentTurnIdx, podcastData.turns);
    }
  };

  const handleRestart = () => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setCurrentTurnIdx(0);
    if (podcastData) {
      setIsPlaying(true);
      speakTurn(0, podcastData.turns);
    }
  };

  const handleJumpToTurn = (idx: number) => {
    setCurrentTurnIdx(idx);
    if (podcastData) {
      setIsPlaying(true);
      speakTurn(idx, podcastData.turns);
    }
  };

  const handleCopyTranscript = () => {
    if (!podcastData) return;
    const text = podcastData.turns
      .map((t) => `${t.speaker} [${t.role.toUpperCase()}]:\n${t.text}\n`)
      .join("\n");
    navigator.clipboard.writeText(text);
    setCopiedTranscript(true);
    setTimeout(() => setCopiedTranscript(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="relative w-full max-w-4xl rounded-3xl border border-slate-200 bg-white shadow-2xl overflow-hidden my-6 max-h-[92vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-violet-50/80 via-purple-50/60 to-pink-50/70 px-6 py-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-violet-600 to-purple-600 text-white shadow-md">
              <Headphones className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-violet-700 flex items-center gap-1">
                  <Radio className="h-3.5 w-3.5" /> AI Audio Study Podcast
                </span>
                <span className="rounded-full bg-violet-100 px-2 py-0.5 text-[10px] font-bold text-violet-800">
                  Innovation 6
                </span>
              </div>
              <h2 className="text-base font-bold text-slate-900 line-clamp-1">{documentTitle}</h2>
            </div>
          </div>

          <button
            onClick={() => {
              if (typeof window !== "undefined" && window.speechSynthesis) {
                window.speechSynthesis.cancel();
              }
              onClose();
            }}
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
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-violet-600 border-t-transparent" />
              <p className="text-xs font-semibold text-slate-600">
                Generating NotebookLM-style 2-host conversational audio overview...
              </p>
            </div>
          ) : error || !podcastData ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-xs text-rose-700">
              <p className="font-bold">Error generating study podcast</p>
              <p className="mt-1">{error || "Could not generate audio."}</p>
            </div>
          ) : (
            <>
              {/* Studio Audio Player Card */}
              <div className="rounded-3xl border border-slate-200 bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-950 p-6 sm:p-7 text-white shadow-xl space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-violet-300">
                      NoteIQ Audio Deep Dive • ~{podcastData.estimated_duration_minutes} Mins
                    </span>
                    <h3 className="text-lg sm:text-xl font-extrabold text-white mt-1">
                      {podcastData.episode_title}
                    </h3>
                  </div>

                  <button
                    onClick={handleCopyTranscript}
                    className="flex items-center gap-1.5 rounded-xl border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-semibold text-white hover:bg-white/20 transition"
                  >
                    {copiedTranscript ? (
                      <>
                        <Check className="h-3.5 w-3.5 text-emerald-400" /> Copied Script!
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5" /> Copy Script
                      </>
                    )}
                  </button>
                </div>

                {/* Soundwave animation */}
                <div className="flex items-center justify-center gap-1.5 h-12 py-2">
                  {[40, 70, 95, 60, 85, 100, 75, 50, 90, 65, 80, 45, 95, 60, 85].map(
                    (height, idx) => (
                      <div
                        key={idx}
                        className={`w-1 rounded-full bg-gradient-to-t from-violet-500 to-pink-400 transition-all duration-300 ${
                          isPlaying ? "animate-pulse" : "opacity-30"
                        }`}
                        style={{
                          height: isPlaying ? `${height}%` : "20%",
                          animationDelay: `${idx * 0.08}s`,
                        }}
                      />
                    )
                  )}
                </div>

                {/* Player Controls Bar */}
                <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-white/10">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={handleTogglePlay}
                      className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500 text-white shadow-lg hover:bg-violet-400 hover:scale-105 active:scale-95 transition"
                    >
                      {isPlaying ? (
                        <Pause className="h-6 w-6 fill-current" />
                      ) : (
                        <Play className="h-6 w-6 fill-current ml-0.5" />
                      )}
                    </button>
                    <button
                      onClick={handleRestart}
                      className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/10 text-white/80 hover:bg-white/20 transition"
                      title="Restart Podcast"
                    >
                      <RotateCcw className="h-4 w-4" />
                    </button>
                    <div className="text-xs text-white/70">
                      Turn <span className="text-white font-bold">{currentTurnIdx + 1}</span> of{" "}
                      {podcastData.turns.length}
                    </div>
                  </div>

                  {/* Speed Selector */}
                  <div className="flex items-center gap-1.5 bg-white/10 p-1 rounded-xl">
                    {[1.0, 1.25, 1.5].map((s) => (
                      <button
                        key={s}
                        onClick={() => {
                          setPlaybackSpeed(s);
                          if (isPlaying && utteranceRef.current) {
                            utteranceRef.current.rate = s;
                          }
                        }}
                        className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${
                          playbackSpeed === s
                            ? "bg-violet-500 text-white shadow-xs"
                            : "text-white/60 hover:text-white"
                        }`}
                      >
                        {s}x
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Key Takeaways Chips */}
              {podcastData.key_takeaways && podcastData.key_takeaways.length > 0 && (
                <div className="rounded-2xl border border-violet-100 bg-violet-50/50 p-4 text-xs space-y-2">
                  <span className="font-bold text-violet-900 flex items-center gap-1.5 uppercase tracking-wide">
                    <Sparkles className="h-3.5 w-3.5 text-violet-600" /> Executive Audio Takeaways:
                  </span>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-violet-800">
                    {podcastData.key_takeaways.map((tk, tkIdx) => (
                      <li key={tkIdx} className="flex items-start gap-1.5">
                        <span className="font-bold">•</span>
                        <span>{tk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Dialogue Transcript Stream */}
              <div className="space-y-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block px-1">
                  Interactive Episode Transcript (Click any line to play from there):
                </span>

                <div className="space-y-3">
                  {podcastData.turns.map((turn, idx) => {
                    const isCurrentlySpeaking = isPlaying && currentTurnIdx === idx;
                    const isHost = turn.speaker.toLowerCase().includes("alex");

                    return (
                      <div
                        key={idx}
                        onClick={() => handleJumpToTurn(idx)}
                        className={`cursor-pointer rounded-2xl border p-4 sm:p-5 transition-all duration-200 ${
                          isCurrentlySpeaking
                            ? "border-violet-500 bg-violet-50/80 shadow-md ring-2 ring-violet-400/30 scale-[1.01]"
                            : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50 shadow-2xs"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div
                              className={`flex h-7 w-7 items-center justify-center rounded-xl text-xs font-bold text-white shadow-xs ${
                                isHost ? "bg-indigo-600" : "bg-emerald-600"
                              }`}
                            >
                              {turn.speaker.charAt(0)}
                            </div>
                            <span className="font-extrabold text-xs text-slate-900">
                              {turn.speaker}
                            </span>
                            <span
                              className={`rounded-md px-1.5 py-0.5 text-[9px] font-bold uppercase ${
                                isHost
                                  ? "bg-indigo-50 text-indigo-700"
                                  : "bg-emerald-50 text-emerald-700"
                              }`}
                            >
                              {turn.role}
                            </span>
                          </div>

                          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">
                            {turn.topic_tag}
                          </span>
                        </div>

                        <p className="text-xs sm:text-sm text-slate-700 leading-relaxed pl-9">
                          "{turn.text}"
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

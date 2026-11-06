"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Bot, Send, User as UserIcon, Sparkles, BookOpen, ExternalLink, ArrowRight } from "lucide-react";
import { api, ChatMessage, ChatSource } from "@/lib/api";

const SUGGESTED_CHIPS = [
  "How many notes are available?",
  "Show all BCA Semester 1 notes",
  "Which subjects have notes?",
  "Are Array notes available?",
  "Highest rated notes",
  "Best notes for C Programming",
  "Topics with no notes",
];

export default function AssistantPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Check authentication
    api.me().catch(() => {
      router.push("/login?redirect=/assistant");
    });
  }, [router]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    setInput("");
    const tempUserMsg: ChatMessage = {
      id: "temp-" + Date.now(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await api.sendChatMessage({
        session_id: sessionId,
        message: text,
      });

      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev.filter((m: any) => m.id !== tempUserMsg.id),
        { ...tempUserMsg, id: "u-" + Date.now() },
        res.message,
      ]);
    } catch (e: any) {
      alert(e.message || "Failed to reach AI Assistant.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto max-w-4xl px-4 sm:px-6 py-8 flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b mb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 text-white shadow-md shadow-brand-500/20">
            <Bot className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900 leading-tight">NoteIQ Academic Assistant</h1>
            <p className="text-xs text-slate-500">Strictly grounded in platform notes • Zero hallucinations</p>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center p-6">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-50 text-teal-600 mb-4 border border-teal-100">
              <Sparkles className="h-7 w-7" />
            </div>
            <h2 className="text-lg font-bold text-slate-900">What would you like to explore?</h2>
            <p className="text-xs text-slate-500 max-w-md mt-1">
              I can check topic availability, list notes by semester, find top-rated materials, and explain concepts directly from uploaded note pages.
            </p>

            {/* Suggested Chips */}
            <div className="mt-8 flex flex-wrap justify-center gap-2 max-w-lg">
              {SUGGESTED_CHIPS.map((chip, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(chip)}
                  className="rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700 transition shadow-sm"
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m: any) => (
            <div
              key={m.id}
              className={`flex gap-3 ${m.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {m.role === "assistant" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white shadow-sm mt-1">
                  <Bot className="h-4 w-4" />
                </div>
              )}

              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed shadow-sm ${
                  m.role === "user"
                    ? "bg-brand-600 text-white rounded-tr-none"
                    : "bg-white border border-slate-200 text-slate-800 rounded-tl-none"
                }`}
              >
                <div className="whitespace-pre-wrap">{m.content}</div>

                {/* Sources Cards */}
                {m.sources && m.sources.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-100 space-y-2">
                    <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                      Cited Sources
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {m.sources.map((src: any, i: number) => (
                        <Link
                          key={i}
                          href={`/notes/${src.document_id}`}
                          className="flex flex-col justify-between rounded-lg border border-slate-200 bg-slate-50 p-2.5 hover:bg-white hover:border-brand-200 transition text-left"
                        >
                          <div>
                            <span className="font-bold text-xs text-slate-900 block truncate">
                              {src.title}
                            </span>
                            {src.location && (
                              <span className="text-[10px] text-teal-600 font-semibold block mt-0.5">
                                Location: {src.location}
                              </span>
                            )}
                          </div>
                          <div className="mt-2 flex items-center justify-between text-[10px] text-slate-400">
                            <span>by {src.uploader_name}</span>
                            <ExternalLink className="h-3 w-3" />
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {m.role === "user" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-700 shadow-sm mt-1">
                  <UserIcon className="h-4 w-4" />
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-teal-600 text-white shadow-sm">
              <Bot className="h-4 w-4 animate-spin" />
            </div>
            <div className="rounded-2xl rounded-tl-none border border-slate-200 bg-white p-3.5 text-xs text-slate-500 shadow-sm flex items-center gap-1.5">
              <span>Searching notes database and synthesizing verified answer...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <div className="pt-4 border-t mt-2">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask about syllabus, topics, ratings, or note contents..."
            className="w-full rounded-2xl border border-slate-300 bg-white py-3.5 pl-4 pr-14 text-xs sm:text-sm shadow-sm focus:border-teal-500 focus:outline-none focus:ring-4 focus:ring-teal-500/10"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2.5 flex h-9 w-9 items-center justify-center rounded-xl bg-teal-600 text-white shadow-sm hover:bg-teal-700 transition disabled:opacity-40"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </div>
    </div>
  );
}

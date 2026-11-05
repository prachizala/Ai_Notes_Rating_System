import Link from "next/link";
import { Search, Sparkles, BookOpen, Bot, ShieldCheck, ArrowRight, Award, Layers } from "lucide-react";
import { api, DocumentItem, PlatformStats, Stream } from "@/lib/api";
import { StreamCard } from "@/components/StreamCard";
import { NoteCard } from "@/components/NoteCard";

async function getHomeData() {
  try {
    const [streams, stats, topDocs] = await Promise.all([
      api.getStreams().catch(() => [
        { id: "1", name: "Bachelor of Business Administration", slug: "bba" },
        { id: "2", name: "Bachelor of Computer Applications", slug: "bca" },
        { id: "3", name: "Bachelor of Vocation", slug: "bvoc" },
      ] as Stream[]),
      api.getStats().catch(() => ({
        total_notes: 0,
        total_subjects: 0,
        total_topics: 0,
        total_contributors: 0,
        analysed_notes: 0,
      } as PlatformStats)),
      api.getDocuments({ limit: 4, sort: "rating" }).catch(() => ({
        items: [] as DocumentItem[],
        total: 0,
        page: 1,
        pages: 1,
      })),
    ]);
    return { streams, stats, topDocs: topDocs.items };
  } catch {
    return { streams: [], stats: { total_notes: 0, total_subjects: 0, total_topics: 0, total_contributors: 0, analysed_notes: 0 }, topDocs: [] };
  }
}

export default async function HomePage() {
  const { streams, stats, topDocs } = await getHomeData();

  return (
    <div className="flex flex-col gap-16 pb-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-50/50 via-white to-slate-50 pt-16 pb-20 border-b">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3.5 py-1 text-xs font-semibold text-brand-700 mb-6 shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-brand-500" />
            AI-Evaluated Academic Notes Platform
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-6xl font-extrabold tracking-tight text-slate-900 max-w-4xl mx-auto leading-tight">
            Academic Notes You Can Trust,{" "}
            <span className="bg-gradient-to-r from-brand-600 to-teal-500 bg-clip-text text-transparent">
              Verified by AI
            </span>
          </h1>

          <p className="mt-5 text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Upload notes in PDF, DOCX, or PPTX. Every document is evaluated across content accuracy, depth, explanation quality, and worked examples with explicit evidence citations.
          </p>

          {/* Prominent Search Bar */}
          <div className="mt-8 max-w-2xl mx-auto">
            <form action="/notes" method="GET" className="relative flex items-center">
              <Search className="absolute left-4 h-5 w-5 text-slate-400" />
              <input
                type="text"
                name="q"
                placeholder="Search notes, subjects, or topics (e.g. Data Structures, Pointers, Marketing)..."
                className="w-full rounded-2xl border border-slate-300 bg-white py-4 pl-12 pr-32 text-sm shadow-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-4 focus:ring-brand-500/10 transition"
              />
              <button
                type="submit"
                className="absolute right-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-brand-700"
              >
                Search
              </button>
            </form>
          </div>

          {/* Live Platform Stats Strip */}
          <div className="mt-12 grid grid-cols-2 gap-4 sm:grid-cols-4 max-w-4xl mx-auto">
            <div className="rounded-xl border border-slate-200 bg-white/80 p-4 backdrop-blur shadow-sm">
              <div className="text-2xl font-black text-brand-600">{stats.total_notes}</div>
              <div className="text-xs font-medium text-slate-500 mt-0.5">Total Notes</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white/80 p-4 backdrop-blur shadow-sm">
              <div className="text-2xl font-black text-teal-600">{stats.total_subjects}</div>
              <div className="text-xs font-medium text-slate-500 mt-0.5">Active Subjects</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white/80 p-4 backdrop-blur shadow-sm">
              <div className="text-2xl font-black text-purple-600">{stats.total_topics}</div>
              <div className="text-xs font-medium text-slate-500 mt-0.5">Dynamic Topics</div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white/80 p-4 backdrop-blur shadow-sm">
              <div className="text-2xl font-black text-amber-600">{stats.total_contributors}</div>
              <div className="text-xs font-medium text-slate-500 mt-0.5">Contributors</div>
            </div>
          </div>
        </div>
      </section>

      {/* Streams Grid */}
      <section className="container mx-auto max-w-7xl px-4 sm:px-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Academic Streams</h2>
            <p className="text-sm text-slate-500 mt-1">Select your undergraduate degree program</p>
          </div>
          <Link href="/streams" className="text-sm font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1">
            View All Streams <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {streams.map((stream) => (
            <StreamCard key={stream.id} stream={stream} />
          ))}
        </div>
      </section>

      {/* Top Rated Notes */}
      {topDocs && topDocs.length > 0 && (
        <section className="container mx-auto max-w-7xl px-4 sm:px-6">
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="flex items-center gap-2">
                <Award className="h-5 w-5 text-amber-500" />
                <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Top-Rated Notes</h2>
              </div>
              <p className="text-sm text-slate-500 mt-1">Highest scoring notes evaluated by academic rubrics</p>
            </div>
            <Link href="/notes?sort=rating" className="text-sm font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1">
              Browse All <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {topDocs.map((note) => (
              <NoteCard key={note.id} note={note} />
            ))}
          </div>
        </section>
      )}

      {/* How it Works Strip */}
      <section className="container mx-auto max-w-7xl px-4 sm:px-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-8 sm:p-12 shadow-sm">
          <h2 className="text-center text-2xl font-bold text-slate-900 mb-10 tracking-tight">
            How NoteIQ Works
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="flex flex-col items-center text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-50 text-brand-600 font-bold text-lg mb-4">
                1
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Upload Academic Notes</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Students and faculty upload course materials (PDF, DOCX, PPTX). Subjects and topics appear dynamically once uploaded.
              </p>
            </div>

            <div className="flex flex-col items-center text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-teal-50 text-teal-600 font-bold text-lg mb-4">
                2
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Multi-Dimensional AI Rating</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                AI extracts readable text and evaluates accuracy, depth, clarity, and examples with page/slide citations.
              </p>
            </div>

            <div className="flex flex-col items-center text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-purple-600 font-bold text-lg mb-4">
                3
              </div>
              <h3 className="text-base font-bold text-slate-900 mb-2">Grounded AI Assistant</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ask questions to an AI assistant answering solely from verified notes—zero hallucinations, zero invented documents.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

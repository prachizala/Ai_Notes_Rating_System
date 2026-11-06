import Link from "next/link";
import { Search, Filter, SlidersHorizontal, Upload } from "lucide-react";
import { api, DocumentItem } from "@/lib/api";
import { NoteCard } from "@/components/NoteCard";
import { EmptyState } from "@/components/StreamCard";

interface NotesPageProps {
  searchParams: {
    stream?: string;
    semester?: string;
    subject?: string;
    topic?: string;
    q?: string;
    sort?: "rating" | "newest" | "downloads";
    role?: "student" | "faculty";
    page?: string;
  };
}

export default async function NotesPage({ searchParams }: NotesPageProps) {
  const pageNum = parseInt(searchParams.page || "1", 10);
  let notes: DocumentItem[] = [];
  let total = 0;
  let pages = 1;

  try {
    const res = await api.getDocuments({
      stream: searchParams.stream,
      semester: searchParams.semester,
      subject: searchParams.subject,
      topic: searchParams.topic,
      q: searchParams.q,
      sort: searchParams.sort || "newest",
      role: searchParams.role,
      page: pageNum,
      limit: 12,
    });
    notes = res.items;
    total = res.total;
    pages = res.pages;
  } catch {
    notes = [];
    total = 0;
    pages = 1;
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-6 py-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Notes Library</h1>
          <p className="mt-1 text-sm text-slate-500">
            {total} {total === 1 ? "document" : "documents"} evaluated and categorized
          </p>
        </div>

        <Link
          href="/upload"
          className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-700 transition"
        >
          <Upload className="h-4 w-4" /> Upload Notes
        </Link>
      </div>

      {/* Filter and Search Controls Bar */}
      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm mb-8">
        <form method="GET" action="/notes" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Keyword Search */}
          <div className="lg:col-span-2 relative">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              name="q"
              defaultValue={searchParams.q || ""}
              placeholder="Filter by keyword or title..."
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-4 text-xs shadow-sm placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/10"
            />
          </div>

          {/* Stream Filter */}
          <select
            name="stream"
            defaultValue={searchParams.stream || ""}
            className="rounded-xl border border-slate-200 py-2.5 px-3 text-xs text-slate-700 focus:border-brand-500 focus:outline-none bg-white"
          >
            <option value="">All Streams</option>
            <option value="bca">BCA</option>
            <option value="bba">BBA</option>
            <option value="bvoc">B.Voc</option>
          </select>

          {/* Semester Filter */}
          <select
            name="semester"
            defaultValue={searchParams.semester || ""}
            className="rounded-xl border border-slate-200 py-2.5 px-3 text-xs text-slate-700 focus:border-brand-500 focus:outline-none bg-white"
          >
            <option value="">All Semesters</option>
            <option value="1">Semester 1</option>
            <option value="2">Semester 2</option>
            <option value="3">Semester 3</option>
            <option value="4">Semester 4</option>
            <option value="5">Semester 5</option>
          </select>

          {/* Sort Option */}
          <div className="flex gap-2">
            <select
              name="sort"
              defaultValue={searchParams.sort || "newest"}
              className="w-full rounded-xl border border-slate-200 py-2.5 px-3 text-xs text-slate-700 focus:border-brand-500 focus:outline-none bg-white"
            >
              <option value="newest">Newest First</option>
              <option value="rating">Highest AI Rating</option>
              <option value="downloads">Most Downloaded</option>
            </select>
            <button
              type="submit"
              className="rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition"
            >
              Filter
            </button>
          </div>
        </form>
      </div>

      {/* Notes Grid */}
      {notes.length === 0 ? (
        <EmptyState
          title="No matching notes found"
          description="Try adjusting your search criteria or stream filters, or contribute new notes."
          actionHref="/upload"
          actionLabel="Upload Notes"
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {notes.map((note: any) => (
            <NoteCard key={note.id} note={note} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div className="mt-12 flex items-center justify-center gap-2">
          {Array.from({ length: pages }, (_, i) => i + 1).map((p) => {
            const isCurrent = p === pageNum;
            const queryParams = new URLSearchParams(searchParams as Record<string, string>);
            queryParams.set("page", String(p));
            return (
              <Link
                key={p}
                href={`/notes?${queryParams.toString()}`}
                className={`flex h-9 w-9 items-center justify-center rounded-lg text-xs font-semibold transition ${
                  isCurrent
                    ? "bg-brand-600 text-white shadow-sm"
                    : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                {p}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}

import Link from "next/link";
import { BookOpen, GraduationCap, ChevronRight, Layers, FileText } from "lucide-react";
import { Stream, Subject } from "@/lib/api";

export function StreamCard({ stream }: { stream: Stream }) {
  const icon =
    stream.slug === "bca" ? (
      <Layers className="h-8 w-8 text-brand-600" />
    ) : stream.slug === "bba" ? (
      <BookOpen className="h-8 w-8 text-teal-600" />
    ) : (
      <GraduationCap className="h-8 w-8 text-purple-600" />
    );

  return (
    <Link
      href={`/streams/${stream.slug}`}
      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:border-brand-300 hover:shadow-md"
    >
      <div>
        <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-slate-50 border border-slate-100 group-hover:scale-105 transition-transform duration-200">
          {icon}
        </div>
        <h3 className="mt-5 text-lg font-bold text-slate-900 group-hover:text-brand-600 transition">
          {stream.name}
        </h3>
        <p className="mt-1 text-sm font-semibold uppercase tracking-wider text-slate-400">
          {stream.slug.toUpperCase()}
        </p>
      </div>

      <div className="mt-6 flex items-center justify-between text-sm font-semibold text-brand-600">
        <span>Explore Semesters</span>
        <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  );
}

export function SemesterCard({
  streamSlug,
  semesterNumber,
  status,
}: {
  streamSlug: string;
  semesterNumber: number;
  status: "active" | "coming_soon" | string;
}) {
  const isComingSoon = status === "coming_soon" || semesterNumber === 6;

  if (isComingSoon) {
    return (
      <div className="relative flex flex-col justify-between rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-6 opacity-75 cursor-not-allowed">
        <div>
          <div className="flex items-center justify-between">
            <span className="text-2xl font-black text-slate-400">0{semesterNumber}</span>
            <span className="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-semibold text-slate-600">
              Coming Soon
            </span>
          </div>
          <h4 className="mt-3 text-base font-bold text-slate-500">Semester {semesterNumber}</h4>
          <p className="mt-1 text-xs text-slate-400">Available in upcoming term.</p>
        </div>
      </div>
    );
  }

  return (
    <Link
      href={`/streams/${streamSlug}/semesters/${semesterNumber}`}
      className="group relative flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition hover:border-brand-300 hover:shadow-md"
    >
      <div>
        <div className="flex items-center justify-between">
          <span className="text-2xl font-black text-brand-600">0{semesterNumber}</span>
          <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-100">
            Active
          </span>
        </div>
        <h4 className="mt-3 text-base font-bold text-slate-900 group-hover:text-brand-600 transition">
          Semester {semesterNumber}
        </h4>
        <p className="mt-1 text-xs text-slate-500">View notes, subjects & syllabus</p>
      </div>

      <div className="mt-4 flex items-center justify-between text-xs font-semibold text-brand-600">
        <span>Browse Subjects</span>
        <ChevronRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  );
}

export function SubjectCard({
  subject,
  streamSlug,
  semesterNumber,
}: {
  subject: Subject;
  streamSlug: string;
  semesterNumber: number;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-base font-bold text-slate-900 leading-snug">{subject.name}</h3>
        <span className="shrink-0 rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-bold text-brand-700 border border-brand-100">
          {subject.document_count} {subject.document_count === 1 ? "note" : "notes"}
        </span>
      </div>

      {subject.topics && subject.topics.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {subject.topics.map((t: any) => (
            <Link
              key={t.id}
              href={`/notes?stream=${streamSlug}&semester=${semesterNumber}&subject=${encodeURIComponent(
                subject.name
              )}&topic=${encodeURIComponent(t.name)}`}
              className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-700 hover:bg-slate-200 transition"
            >
              #{t.name}
            </Link>
          ))}
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
        <Link
          href={`/notes?stream=${streamSlug}&semester=${semesterNumber}&subject=${encodeURIComponent(
            subject.name
          )}`}
          className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1"
        >
          View all notes
          <ChevronRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}

export function EmptyState({
  title = "No notes found",
  description = "No notes have been contributed for this selection yet.",
  actionHref = "/upload",
  actionLabel = "Upload Notes",
}: {
  title?: string;
  description?: string;
  actionHref?: string;
  actionLabel?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-white py-12 px-6 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-50 text-brand-600 mb-4">
        <FileText className="h-7 w-7" />
      </div>
      <h3 className="text-lg font-bold text-slate-900">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
      {actionHref && (
        <Link
          href={actionHref}
          className="mt-5 inline-flex items-center rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-teal-700"
        >
          {actionLabel}
        </Link>
      )}
    </div>
  );
}

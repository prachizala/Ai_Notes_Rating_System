import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Upload } from "lucide-react";
import { api, Subject } from "@/lib/api";
import { SubjectCard, EmptyState } from "@/components/StreamCard";

interface SemesterSubjectsPageProps {
  params: {
    stream: string;
    sem: string;
  };
}

export default async function SemesterSubjectsPage({ params }: SemesterSubjectsPageProps) {
  const streamSlug = params.stream.toLowerCase();
  const semesterNum = parseInt(params.sem, 10);

  if (isNaN(semesterNum) || semesterNum < 1 || semesterNum > 6) {
    notFound();
  }

  if (semesterNum === 6) {
    return (
      <div className="container mx-auto max-w-7xl px-4 sm:px-6 py-12">
        <Link
          href={`/streams/${streamSlug}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-brand-600 transition mb-4"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Semesters
        </Link>
        <div className="rounded-2xl border-2 border-dashed border-slate-300 bg-white p-12 text-center">
          <h2 className="text-2xl font-bold text-slate-900">Semester 6 is Coming Soon</h2>
          <p className="mt-2 text-sm text-slate-500">
            Notes and subjects for Semester 6 will become available in the upcoming semester.
          </p>
        </div>
      </div>
    );
  }

  let subjects: Subject[] = [];
  try {
    subjects = await api.getSubjects({ stream: streamSlug, semester: String(semesterNum) });
  } catch {
    subjects = [];
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-6 py-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <Link
            href={`/streams/${streamSlug}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-brand-600 transition mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Semesters
          </Link>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {streamSlug.toUpperCase()} • Semester {semesterNum}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Dynamically discovered subjects with available verified notes
          </p>
        </div>

        <Link
          href={`/upload?stream=${streamSlug}&semester=${semesterNum}`}
          className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-700 transition"
        >
          <Upload className="h-4 w-4" />
          Upload Note for Sem {semesterNum}
        </Link>
      </div>

      {subjects.length === 0 ? (
        <EmptyState
          title={`No subjects found for Semester ${semesterNum}`}
          description="Subjects appear dynamically when the first note is uploaded for this semester. Be the first contributor!"
          actionHref={`/upload?stream=${streamSlug}&semester=${semesterNum}`}
          actionLabel="Upload the First Note"
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {subjects.map((subj: any) => (
            <SubjectCard
              key={subj.id}
              subject={subj}
              streamSlug={streamSlug}
              semesterNumber={semesterNum}
            />
          ))}
        </div>
      )}
    </div>
  );
}

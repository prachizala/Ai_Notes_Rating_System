import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { api, Semester } from "@/lib/api";
import { SemesterCard } from "@/components/StreamCard";

interface StreamDetailPageProps {
  params: {
    stream: string;
  };
}

export default async function StreamDetailPage({ params }: StreamDetailPageProps) {
  const streamSlug = params.stream.toLowerCase();
  const validStreams: Record<string, string> = {
    bca: "Bachelor of Computer Applications",
    bba: "Bachelor of Business Administration",
    bvoc: "Bachelor of Vocation",
  };

  const streamName = validStreams[streamSlug];
  if (!streamName) {
    notFound();
  }

  // Semesters 1 to 5 active, Semester 6 coming_soon
  const semesters: { number: number; status: "active" | "coming_soon" }[] = [
    { number: 1, status: "active" },
    { number: 2, status: "active" },
    { number: 3, status: "active" },
    { number: 4, status: "active" },
    { number: 5, status: "active" },
    { number: 6, status: "coming_soon" },
  ];

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-6 py-12">
      <div className="mb-8">
        <Link
          href="/streams"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-brand-600 transition mb-4"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Streams
        </Link>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">{streamName}</h1>
        <p className="mt-1 text-sm font-semibold uppercase tracking-wider text-slate-400">
          {streamSlug.toUpperCase()} • Select Semester
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {semesters.map((sem: any) => (
          <SemesterCard
            key={sem.number}
            streamSlug={streamSlug}
            semesterNumber={sem.number}
            status={sem.status}
          />
        ))}
      </div>
    </div>
  );
}

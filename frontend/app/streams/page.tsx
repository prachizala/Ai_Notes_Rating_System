import { api, Stream } from "@/lib/api";
import { StreamCard } from "@/components/StreamCard";

export default async function StreamsPage() {
  let streams: Stream[] = [];
  try {
    streams = await api.getStreams();
  } catch {
    streams = [
      { id: "1", name: "Bachelor of Business Administration", slug: "bba" },
      { id: "2", name: "Bachelor of Computer Applications", slug: "bca" },
      { id: "3", name: "Bachelor of Vocation", slug: "bvoc" },
    ];
  }

  return (
    <div className="container mx-auto max-w-7xl px-4 sm:px-6 py-12">
      <div className="max-w-2xl mb-10">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Academic Streams</h1>
        <p className="mt-2 text-sm text-slate-500">
          Choose your undergraduate stream to browse active semesters, subjects, and AI-rated notes.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {streams.map((stream) => (
          <StreamCard key={stream.id} stream={stream} />
        ))}
      </div>
    </div>
  );
}

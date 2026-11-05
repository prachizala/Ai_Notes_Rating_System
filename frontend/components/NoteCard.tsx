import Link from "next/link";
import { Download, FileText, Calendar, Sparkles, Users } from "lucide-react";
import { DocumentItem } from "@/lib/api";
import { RatingStars } from "./RatingStars";
import { RoleBadge, StatusPill } from "./StatusPill";

interface NoteCardProps {
  note: DocumentItem;
}

export function NoteCard({ note }: NoteCardProps) {
  const formattedDate = new Date(note.created_at).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="group flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md hover:border-brand-200">
      <div>
        {/* Category & Status */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="inline-block rounded-md bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700 truncate max-w-[65%]">
            {note.subject_name || "General"} • {note.topic_name || "Notes"}
          </span>
          <StatusPill status={note.status} />
        </div>

        {/* Title */}
        <Link href={`/notes/${note.id}`} className="block">
          <h3 className="text-base font-bold text-slate-900 group-hover:text-brand-600 transition line-clamp-2 leading-snug">
            {note.title}
          </h3>
        </Link>

        {note.description && (
          <p className="mt-2 text-xs text-slate-500 line-clamp-2 leading-relaxed">
            {note.description}
          </p>
        )}

        {/* Ratings Comparison: AI Score vs Student Reviews */}
        <div className="mt-4 grid grid-cols-2 gap-2 rounded-lg bg-slate-50/80 p-3 border border-slate-100">
          <div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-brand-700 uppercase tracking-wider mb-1">
              <Sparkles className="h-3 w-3 text-brand-500" />
              AI Rating
            </div>
            <RatingStars score={note.overall_rating} size="sm" />
          </div>

          <div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-slate-600 uppercase tracking-wider mb-1">
              <Users className="h-3 w-3 text-slate-500" />
              Student ({note.student_rating_count})
            </div>
            <RatingStars score={note.student_rating_avg} size="sm" />
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <div className="flex items-center gap-2">
          <span className="font-medium text-slate-700 truncate max-w-[120px]">
            {note.uploader_name}
          </span>
          <RoleBadge role={note.uploader_role} />
        </div>

        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1" title="Downloads">
            <Download className="h-3.5 w-3.5 text-slate-400" />
            {note.download_count}
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <FileText className="h-3.5 w-3.5 uppercase" />
            {note.file_type}
          </span>
        </div>
      </div>
    </div>
  );
}

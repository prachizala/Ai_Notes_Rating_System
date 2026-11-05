import { CheckCircle2, Clock, AlertTriangle, XCircle, Sparkles, GraduationCap } from "lucide-react";

interface StatusPillProps {
  status: "queued" | "processing" | "complete" | "failed" | string;
}

export function StatusPill({ status }: StatusPillProps) {
  switch (status) {
    case "complete":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 border border-emerald-200">
          <CheckCircle2 className="h-3 w-3" />
          Complete
        </span>
      );
    case "processing":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 border border-amber-200 animate-pulse">
          <Clock className="h-3 w-3 animate-spin" />
          Analyzing...
        </span>
      );
    case "queued":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 border border-blue-200">
          <Clock className="h-3 w-3" />
          Queued
        </span>
      );
    case "failed":
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-medium text-rose-700 border border-rose-200">
          <XCircle className="h-3 w-3" />
          Failed
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
          {status}
        </span>
      );
  }
}

interface RoleBadgeProps {
  role: "student" | "faculty" | string;
}

export function RoleBadge({ role }: RoleBadgeProps) {
  if (role === "faculty") {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-purple-100 px-2 py-0.5 text-[11px] font-semibold text-purple-800" title="Faculty Contributor">
        <GraduationCap className="h-3 w-3" />
        Faculty
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700" title="Student Contributor">
      Student
    </span>
  );
}

export function AiBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-brand-50 border border-brand-200 px-2 py-0.5 text-xs font-semibold text-brand-700">
      <Sparkles className="h-3 w-3 text-brand-600" />
      AI Evaluation
    </span>
  );
}

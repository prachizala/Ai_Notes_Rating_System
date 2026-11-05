import { Star, StarHalf } from "lucide-react";

interface RatingStarsProps {
  score: number | null;
  max?: number;
  size?: "sm" | "md" | "lg";
}

export function RatingStars({ score, max = 5, size = "md" }: RatingStarsProps) {
  if (score === null || score === undefined) {
    return <span className="text-xs text-slate-400 font-medium italic">Pending</span>;
  }

  const iconSize = size === "sm" ? "h-3.5 w-3.5" : size === "lg" ? "h-6 w-6" : "h-4 w-4";
  const stars = [];

  for (let i = 1; i <= max; i++) {
    if (score >= i) {
      stars.push(<Star key={i} className={`${iconSize} fill-amber-400 text-amber-400`} />);
    } else if (score >= i - 0.5) {
      stars.push(<StarHalf key={i} className={`${iconSize} fill-amber-400 text-amber-400`} />);
    } else {
      stars.push(<Star key={i} className={`${iconSize} text-slate-200 fill-slate-100`} />);
    }
  }

  return (
    <div className="flex items-center gap-0.5" title={`Score: ${score} / ${max}`}>
      {stars}
      <span className="ml-1.5 font-bold text-slate-800 text-sm">{score.toFixed(1)}</span>
    </div>
  );
}

interface RatingBarProps {
  label: string;
  score: number;
  max?: number;
  justification?: string;
}

export function RatingBar({ label, score, max = 5, justification }: RatingBarProps) {
  const percentage = Math.min(100, Math.max(0, (score / max) * 100));

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="font-medium text-slate-700 capitalize">{label.replace("_", " ")}</span>
        <span className="font-semibold text-slate-900">{score.toFixed(1)} / {max}</span>
      </div>
      <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-teal-500 transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
      {justification && (
        <p className="text-xs text-slate-500 leading-relaxed">{justification}</p>
      )}
    </div>
  );
}

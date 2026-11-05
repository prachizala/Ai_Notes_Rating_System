import Link from "next/link";

export function Footer() {
  return (
    <footer className="mt-auto border-t bg-white py-8 text-slate-500">
      <div className="container mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-900">NoteIQ</span>
          <span className="text-xs">© {new Date().getFullYear()} AI-Evaluated Academic Notes Platform</span>
        </div>
        <div className="flex items-center gap-6 text-sm">
          <Link href="/streams" className="transition hover:text-brand-600">
            Streams
          </Link>
          <Link href="/notes" className="transition hover:text-brand-600">
            Notes
          </Link>
          <Link href="/assistant" className="transition hover:text-brand-600">
            Assistant
          </Link>
          <Link href="/upload" className="transition hover:text-brand-600">
            Upload
          </Link>
        </div>
      </div>
    </footer>
  );
}

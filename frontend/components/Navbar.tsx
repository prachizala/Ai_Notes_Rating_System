"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { BookOpen, Upload, Bot, LogIn, User as UserIcon, LogOut } from "lucide-react";
import { api, User } from "@/lib/api";

export function Navbar() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api.me().then((res) => setUser(res.user)).catch(() => setUser(null));
  }, []);

  const handleLogout = async () => {
    try {
      await api.logout();
      setUser(null);
      window.location.href = "/";
    } catch (e) {
      console.error("Logout failed:", e);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/90 backdrop-blur-md">
      <div className="container mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-brand-600 to-teal-500 text-white font-bold text-xl shadow-md shadow-brand-500/20">
              N
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">
              Note<span className="text-brand-600">IQ</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
            <Link href="/streams" className="transition hover:text-brand-600">
              Browse Streams
            </Link>
            <Link href="/notes" className="transition hover:text-brand-600">
              Notes Library
            </Link>
            <Link href="/assistant" className="flex items-center gap-1.5 transition hover:text-teal-600">
              <Bot className="h-4 w-4 text-teal-600" />
              AI Assistant
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <Link
            href="/upload"
            className="hidden sm:inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-teal-700"
          >
            <Upload className="h-4 w-4" />
            Upload Notes
          </Link>

          {user ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 py-1 px-3 text-xs font-medium text-slate-700">
                <UserIcon className="h-3.5 w-3.5 text-brand-600" />
                <span className="font-semibold">{user.name}</span>
                <span className="rounded bg-brand-100 px-1.5 py-0.5 text-[10px] uppercase text-brand-700">
                  {user.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="text-slate-500 transition hover:text-red-600"
                title="Log out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3.5 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              >
                <LogIn className="h-4 w-4 text-slate-500" />
                Sign In
              </Link>
              <Link
                href="/register"
                className="inline-flex items-center rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-medium text-white transition hover:bg-brand-700 shadow-sm shadow-brand-600/20"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

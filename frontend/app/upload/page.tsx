"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Upload, FileUp, AlertCircle, CheckCircle2, ArrowRight } from "lucide-react";
import { api, User } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loadingUser, setLoadingUser] = useState(true);

  // Form states
  const [stream, setStream] = useState(searchParams.get("stream") || "bca");
  const [semester, setSemester] = useState(searchParams.get("semester") || "1");
  const [subject, setSubject] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [topic, setTopic] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);

  // UI state
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.me()
      .then((res) => {
        setCurrentUser(res.user);
        setLoadingUser(false);
      })
      .catch(() => {
        router.push("/login?redirect=/upload");
      });
  }, [router]);

  // Subject autocomplete fetch
  useEffect(() => {
    if (subject.length >= 2) {
      api.suggestSubjects(subject)
        .then((s) => {
          setSuggestions(s);
          setShowSuggestions(true);
        })
        .catch(() => setSuggestions([]));
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [subject]);

  const handleFileChange = (selectedFile: File) => {
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (!ext || !["pdf", "docx", "pptx"].includes(ext)) {
      setError("Please select a PDF, Word (DOCX), or PowerPoint (PPTX) document.");
      return;
    }
    if (selectedFile.size > 25 * 1024 * 1024) {
      setError("File exceeds maximum upload limit of 25 MB.");
      return;
    }
    setError(null);
    setFile(selectedFile);
    if (!title) {
      // Auto-populate title from clean filename
      const cleanName = selectedFile.name.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ");
      setTitle(cleanName);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (semester === "6") {
      setError("Semester 6 is Coming Soon and is not open for uploads.");
      return;
    }

    if (!file) {
      setError("Please choose a file to upload.");
      return;
    }

    setUploading(true);
    setProgress(20);

    const formData = new FormData();
    formData.append("stream", stream);
    formData.append("semester", semester);
    formData.append("subject", subject.trim());
    formData.append("topic", topic.trim());
    formData.append("title", title.trim());
    if (description.trim()) {
      formData.append("description", description.trim());
    }
    formData.append("file", file);

    try {
      setProgress(60);
      const doc = await api.uploadDocument(formData);
      setProgress(100);
      setTimeout(() => {
        router.push(`/notes/${doc.id}`);
      }, 500);
    } catch (err: any) {
      setError(err.message || "Failed to upload document. Please check fields and try again.");
      setUploading(false);
    }
  };

  if (loadingUser) {
    return (
      <div className="container mx-auto max-w-xl px-4 py-20 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-brand-600 border-r-transparent" />
        <p className="mt-4 text-xs font-semibold text-slate-500">Checking credentials...</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-3xl px-4 sm:px-6 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Upload Course Notes</h1>
        <p className="mt-1 text-sm text-slate-500">
          Upload PDF, DOCX, or PPTX. Our automated academic reviewer will evaluate content accuracy and depth.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-sm">
        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800">
            <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
            <span className="font-medium">{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Stream & Semester */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Academic Stream *
              </label>
              <select
                value={stream}
                onChange={(e) => setStream(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-brand-500 focus:outline-none bg-white"
              >
                <option value="bca">Bachelor of Computer Applications (BCA)</option>
                <option value="bba">Bachelor of Business Administration (BBA)</option>
                <option value="bvoc">Bachelor of Vocation (B.Voc)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Semester *
              </label>
              <select
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                required
                className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-brand-500 focus:outline-none bg-white"
              >
                <option value="1">Semester 1</option>
                <option value="2">Semester 2</option>
                <option value="3">Semester 3</option>
                <option value="4">Semester 4</option>
                <option value="5">Semester 5</option>
                <option value="6" disabled className="text-slate-400 bg-slate-50">
                  Semester 6 (Coming Soon)
                </option>
              </select>
            </div>
          </div>

          {/* Dynamic Subject with Autocomplete */}
          <div className="relative">
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Subject Name *
            </label>
            <input
              type="text"
              required
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
              placeholder="e.g. Data Structures & Algorithms, Financial Management..."
              className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-brand-500 focus:outline-none"
            />
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute z-20 left-0 right-0 mt-1 max-h-48 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1 shadow-lg text-xs">
                {suggestions.map((sug, i) => (
                  <button
                    type="button"
                    key={i}
                    onClick={() => {
                      setSubject(sug);
                      setShowSuggestions(false);
                    }}
                    className="w-full text-left rounded-lg px-3 py-2 text-slate-700 hover:bg-slate-100 transition"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            )}
            <p className="mt-1 text-[11px] text-slate-400">
              New subjects are created automatically if they do not yet exist.
            </p>
          </div>

          {/* Topic */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Topic / Unit *
            </label>
            <input
              type="text"
              required
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Binary Search Trees, Capital Budgeting, Normalization..."
              className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Document Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Complete Lecture Slides on BST Traversal & Code"
              className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Description <span className="font-normal text-slate-400">(optional)</span>
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of what this document covers..."
              className="w-full rounded-xl border border-slate-200 p-3 text-sm focus:border-brand-500 focus:outline-none"
            />
          </div>

          {/* Drag & Drop File Zone */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              File Attachment *
            </label>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer transition ${
                file
                  ? "border-emerald-300 bg-emerald-50/30"
                  : "border-slate-300 hover:border-brand-400 hover:bg-slate-50"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.pptx"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
              />

              {file ? (
                <div className="flex flex-col items-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 mb-2">
                    <CheckCircle2 className="h-6 w-6" />
                  </div>
                  <span className="font-bold text-sm text-slate-900">{file.name}</span>
                  <span className="text-xs text-slate-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</span>
                  <span className="text-[11px] text-teal-600 font-semibold mt-2">Click to replace</span>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-50 text-brand-600 mb-2">
                    <FileUp className="h-6 w-6" />
                  </div>
                  <span className="font-bold text-sm text-slate-800">
                    Click to browse or drag and drop your document
                  </span>
                  <span className="text-xs text-slate-400 mt-1">
                    Supports PDF, Word (.docx), PowerPoint (.pptx) up to 25 MB
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Progress bar */}
          {uploading && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-slate-600">
                <span>Uploading and initializing analysis...</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                <div
                  className="h-full bg-teal-500 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={uploading}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-teal-600 py-3.5 text-sm font-bold text-white shadow-md hover:bg-teal-700 transition disabled:opacity-50"
          >
            <Upload className="h-4 w-4" />
            {uploading ? "Processing Document..." : "Upload and Analyze Notes"}
          </button>
        </form>
      </div>
    </div>
  );
}

/**
 * NoteIQ Frontend API Client
 * Built to communicate with FastAPI backend with credentials (cookies) and CSRF token handling.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  code?: string;
  details?: any;
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: "student" | "faculty";
  is_moderator: boolean;
  created_at?: string;
}

export interface Stream {
  id: string;
  name: string;
  slug: string;
}

export interface Semester {
  id: string;
  number: number;
  status: "active" | "coming_soon";
}

export interface Topic {
  id: string;
  name: string;
  normalized_name: string;
  document_count?: number;
}

export interface Subject {
  id: string;
  stream_id: string;
  semester_id: string;
  name: string;
  normalized_name: string;
  topics: Topic[];
  document_count: number;
}

export interface DocumentAnalysisScore {
  score: number;
  justification: string;
  evidence: string[];
}

export interface DocumentAnalysisFeedback {
  kind: "strength" | "improvement" | "missing_concept" | "error_found";
  text: string;
  evidence_ref?: string;
}

export interface DocumentAnalysisTopic {
  topic_name: string;
  note?: string;
}

export interface DocumentAnalysis {
  id: string;
  document_id: string;
  version: number;
  rubric_version: string;
  model_name: string;
  topic_coverage_pct: number | null;
  accuracy_score: number;
  explanation_score: number;
  depth_score: number;
  examples_score: number;
  overall_score_raw: number;
  overall_score_display: number;
  confidence: "low" | "medium" | "high";
  confidence_reason?: string;
  summary: string;
  total_topics: number;
  topics: DocumentAnalysisTopic[];
  feedback: DocumentAnalysisFeedback[];
  created_at: string;
}

export interface DocumentItem {
  id: string;
  subject_id: string;
  topic_id: string;
  uploader_id: string;
  uploader_name: string;
  uploader_role: "student" | "faculty";
  stream_name?: string;
  semester_number?: number;
  subject_name?: string;
  topic_name?: string;
  title: string;
  description?: string;
  file_type: string;
  file_size: number;
  status: "queued" | "processing" | "complete" | "failed";
  failure_reason?: string;
  download_count: number;
  overall_rating: number | null;
  student_rating_avg: number | null;
  student_rating_count: number;
  created_at: string;
}

export interface ReviewItem {
  id: string;
  document_id: string;
  user_id: string;
  user_name: string;
  user_role: "student" | "faculty";
  stars: number;
  comment?: string;
  created_at: string;
  updated_at: string;
}

export interface PlatformStats {
  total_notes: number;
  total_subjects: number;
  total_topics: number;
  total_contributors: number;
  analysed_notes: number;
}

export interface ChatSource {
  document_id: string;
  title: string;
  uploader_name: string;
  overall_rating: number | null;
  location?: string;
  snippet?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ChatSource[];
  created_at: string;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  difficulty: "easy" | "medium" | "hard";
}

export interface Flashcard {
  id: number;
  front: string;
  back: string;
  topic: string;
}

export interface StudyPackResponse {
  document_id: string;
  document_title: string;
  quiz: QuizQuestion[];
  flashcards: Flashcard[];
}

export interface PredictedQuestion {
  id: number;
  marks: number;
  category: string;
  question: string;
  probability: "Very High" | "High" | "Medium";
  expected_key_points: string[];
  location: string;
  bloom_level: string;
}

export interface ExamPredictionResponse {
  document_id: string;
  document_title: string;
  total_predicted: number;
  questions: PredictedQuestion[];
  exam_tips: string[];
}

// Function to retrieve stored CSRF cookie or token
function getCsrfToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )XSRF-TOKEN=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

export async function apiFetch<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith("http")
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Include CSRF token for mutating requests if available
  const method = (options.method || "GET").toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // send/receive httpOnly cookies
  });

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: response.statusText };
    }
    const error: any = new Error(errorData.message || errorData.detail || "API request failed");
    error.status = response.status;
    error.code = errorData.code || `HTTP_${response.status}`;
    error.details = errorData.details;
    throw error;
  }

  return response.json();
}

// API methods
export const api = {
  // Auth
  register: (payload: { name: string; email: string; password: string; role: "student" | "faculty" }) =>
    apiFetch<{ user: User; message: string }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  login: (payload: { email: string; password: string }) =>
    apiFetch<{ user: User; message: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  logout: () =>
    apiFetch<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    }),

  me: () => apiFetch<{ user: User }>("/api/v1/auth/me"),

  refresh: () =>
    apiFetch<{ message: string }>("/api/v1/auth/refresh", {
      method: "POST",
    }),

  // Catalogue
  getStreams: () => apiFetch<Stream[]>("/api/v1/streams"),

  getSemesters: (streamId: string) => apiFetch<Semester[]>(`/api/v1/streams/${streamId}/semesters`),

  getSubjects: (params?: { stream?: string; semester?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.stream) searchParams.set("stream", params.stream);
    if (params?.semester) searchParams.set("semester", params.semester);
    return apiFetch<Subject[]>(`/api/v1/subjects?${searchParams.toString()}`);
  },

  suggestSubjects: (query: string) =>
    apiFetch<string[]>(`/api/v1/subjects/suggest?q=${encodeURIComponent(query)}`),

  // Documents
  getDocuments: (params?: {
    stream?: string;
    semester?: string;
    subject?: string;
    topic?: string;
    q?: string;
    sort?: "rating" | "newest" | "downloads";
    role?: "student" | "faculty";
    page?: number;
    limit?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== "") {
          searchParams.set(key, String(val));
        }
      });
    }
    return apiFetch<{ items: DocumentItem[]; total: number; page: number; pages: number }>(
      `/api/v1/documents?${searchParams.toString()}`
    );
  },

  getDocument: (id: string) => apiFetch<DocumentItem>(`/api/v1/documents/${id}`),

  uploadDocument: (formData: FormData) =>
    apiFetch<DocumentItem>("/api/v1/documents", {
      method: "POST",
      body: formData,
    }),

  deleteDocument: (id: string) =>
    apiFetch<{ message: string }>(`/api/v1/documents/${id}`, {
      method: "DELETE",
    }),

  downloadDocument: (id: string) =>
    apiFetch<{ download_url: string; filename: string }>(`/api/v1/documents/${id}/download`),

  getStudyTools: (documentId: string) =>
    apiFetch<StudyPackResponse>(`/api/v1/documents/${documentId}/study-tools`),

  getExamPredictions: (documentId: string) =>
    apiFetch<ExamPredictionResponse>(`/api/v1/documents/${documentId}/exam-predictions`),

  // Analysis
  getAnalysis: (documentId: string) =>
    apiFetch<DocumentAnalysis>(`/api/v1/documents/${documentId}/analysis`),

  reanalyseDocument: (documentId: string) =>
    apiFetch<{ message: string }>(`/api/v1/documents/${documentId}/reanalyse`, {
      method: "POST",
    }),

  // Reviews
  getReviews: (documentId: string) =>
    apiFetch<ReviewItem[]>(`/api/v1/documents/${documentId}/reviews`),

  submitReview: (documentId: string, payload: { stars: number; comment?: string }) =>
    apiFetch<ReviewItem>(`/api/v1/documents/${documentId}/reviews`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  // Search
  search: (query: string) =>
    apiFetch<{
      documents: DocumentItem[];
      subjects: Subject[];
      topics: { id: string; name: string; subject_name: string }[];
    }>(`/api/v1/search?q=${encodeURIComponent(query)}`),

  // Syllabus
  getSyllabus: (subjectId: string) =>
    apiFetch<{ subject_id: string; topics: string[] }>(`/api/v1/subjects/${subjectId}/syllabus`),

  updateSyllabus: (subjectId: string, topics: string[]) =>
    apiFetch<{ subject_id: string; topics: string[] }>(`/api/v1/subjects/${subjectId}/syllabus`, {
      method: "PUT",
      body: JSON.stringify({ topics }),
    }),

  // Chat / Assistant
  sendChatMessage: (payload: { session_id?: string; message: string }) =>
    apiFetch<{
      session_id: string;
      message: ChatMessage;
    }>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getChatSession: (sessionId: string) =>
    apiFetch<{ session_id: string; messages: ChatMessage[] }>(`/api/v1/chat/sessions/${sessionId}`),

  // Stats
  getStats: () => apiFetch<PlatformStats>("/api/v1/stats"),

  // Moderation
  flagDocument: (documentId: string, reason: string) =>
    apiFetch<{ message: string }>(`/api/v1/documents/${documentId}/flag`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    }),

  getFlags: () =>
    apiFetch<{
      items: { id: string; document_id: string; document_title: string; reason: string; status: string; reporter_name: string; created_at: string }[];
    }>("/api/v1/moderation/flags"),

  resolveFlag: (flagId: string, action: "dismiss" | "delete_document") =>
    apiFetch<{ message: string }>(`/api/v1/moderation/flags/${flagId}`, {
      method: "POST",
      body: JSON.stringify({ action }),
    }),
};

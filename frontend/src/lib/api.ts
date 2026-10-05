export function getApiBase(): string {
  // If explicitly configured with a remote URL (e.g. Render/Railway backend)
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
  }
  // At runtime in the browser:
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    // On local machine, use direct port 8000
    if (host === "localhost" || host === "127.0.0.1") {
      return "http://localhost:8000";
    }
    // On any deployed cloud domain (Vercel, Render, custom domain), use same-origin relative URL
    return "";
  }
  // Server-side build default
  return "";
}

function transformNetworkError(err: any): Error {
  if (
    err instanceof TypeError &&
    (err.message === "Failed to fetch" || err.message.includes("NetworkError") || err.message.includes("fetch"))
  ) {
    return new Error(
      "Unable to connect to the WealthGuard backend API. Please verify the backend service is deployed and running, and that NEXT_PUBLIC_API_URL is configured in your project settings."
    );
  }
  return err instanceof Error ? err : new Error(String(err));
}

export const API_BASE = {
  toString: () => getApiBase(),
  valueOf: () => getApiBase(),
  [Symbol.toPrimitive]: () => getApiBase(),
} as unknown as string;

export interface Citation {
  document_name: string;
  version: string;
  clause_id: string;
  page_number: number;
  excerpt: string;
  score?: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  isRefusal?: boolean;
}

export interface UserProfile {
  id: string;
  account_id: string;
  email: string;
  full_name: string;
  role: "RM" | "ComplianceAdmin";
  is_active: boolean;
  account?: {
    id: string;
    branch_name: string;
    branch_code: string;
  };
}

export interface DocumentItem {
  id: string;
  account_id: string;
  filename: string;
  version: string;
  doc_type: string;
  effective_date: string;
  is_discontinued: boolean;
  total_pages: number;
  total_chunks: number;
  status: string;
  created_at: string;
}

export interface AuditLogItem {
  id: string;
  account_id: string;
  user_id: string;
  query: string;
  rewritten_query?: string;
  similarity_score: number;
  response: string;
  is_refusal: boolean;
  latency_ms: number;
  created_at: string;
}

export async function loginUser(email: string, password: string) {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(err.detail || "Authentication error");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function signupUser(fullName: string, email: string, password: string) {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: fullName, email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Registration failed" }));
      throw new Error(err.detail || "Registration error");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function requestPasswordReset(email: string) {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(err.detail || "Error requesting password reset");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function submitPasswordReset(token: string, new_password: string) {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Reset failed" }));
      throw new Error(err.detail || "Error resetting password");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function fetchCurrentUser(token: string): Promise<UserProfile> {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      throw new Error("Failed to load user profile");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function fetchDocuments(
  token: string,
  docType?: string,
  isDiscontinued?: boolean
): Promise<{ total: number; documents: DocumentItem[] }> {
  const base = getApiBase();
  const params = new URLSearchParams();
  if (docType) params.append("doc_type", docType);
  if (isDiscontinued !== undefined) params.append("is_discontinued", String(isDiscontinued));

  try {
    const res = await fetch(`${base}/api/v1/documents?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      throw new Error("Failed to fetch documents");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function uploadDocumentFile(token: string, formData: FormData) {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/documents/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(err.detail || "Failed to upload document");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function deleteDocumentFile(token: string, documentId: string) {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/documents/${documentId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Delete failed" }));
      throw new Error(err.detail || "Failed to delete document");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

export async function fetchAuditLogs(
  token: string,
  limit = 50,
  offset = 0,
  isRefusal?: boolean
): Promise<{ total: number; logs: AuditLogItem[] }> {
  const base = getApiBase();
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (isRefusal !== undefined) params.append("is_refusal", String(isRefusal));

  try {
    const res = await fetch(`${base}/api/v1/audit/logs?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      throw new Error("Failed to fetch audit logs");
    }
    return res.json();
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

/**
 * Consumes the Server-Sent Events (SSE) streaming chat endpoint.
 * Emits incremental tokens and final structured citations.
 */
export async function streamChatResponse(
  token: string,
  query: string,
  chatHistory: { role: string; content: string }[],
  onToken: (token: string) => void,
  onCitations: (citations: Citation[]) => void,
  onDone: () => void,
  onError: (err: Error) => void
) {
  try {
    const base = getApiBase();
    const response = await fetch(`${base}/api/v1/chat/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        query,
        chat_history: chatHistory,
      }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: "Chat query error" }));
      throw new Error(err.detail || "Failed to get chat response");
    }

    if (!response.body) {
      throw new Error("ReadableStream not supported by browser.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split("\n\n");
      buffer = events.pop() || "";

      for (const eventBlock of events) {
        if (!eventBlock.trim()) continue;

        let eventType = "message";
        let eventData = "";

        const lines = eventBlock.split("\n");
        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventType = line.replace("event:", "").trim();
          } else if (line.startsWith("data:")) {
            eventData = line.replace("data:", "").trim();
          }
        }

        if (eventType === "token") {
          try {
            const parsed = JSON.parse(eventData);
            if (parsed.token) onToken(parsed.token);
          } catch {
            onToken(eventData);
          }
        } else if (eventType === "citations") {
          try {
            const citations = JSON.parse(eventData);
            onCitations(citations);
          } catch {
            onCitations([]);
          }
        } else if (eventType === "error") {
          let errorMsg = "Stream generation error occurred";
          try {
            const parsed = JSON.parse(eventData);
            if (parsed.error) errorMsg = parsed.error;
          } catch {
            if (eventData) errorMsg = eventData;
          }
          onError(new Error(errorMsg));
          return;
        } else if (eventType === "done") {
          onDone();
        }
      }
    }

    onDone();
  } catch (err: any) {
    onError(transformNetworkError(err));
  }
}

export async function downloadDocumentPdf(token: string, documentId: string, filename: string) {
  const base = getApiBase();
  try {
    const res = await fetch(`${base}/api/v1/documents/${documentId}/export-pdf`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed to download PDF summary");
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `GAA_Summary_${filename.replace(/\.pdf$/i, "")}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err: any) {
    throw transformNetworkError(err);
  }
}

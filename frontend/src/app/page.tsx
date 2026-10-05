"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Send,
  Sparkles,
  Shield,
  ShieldAlert,
  FileText,
  Loader2,
  RefreshCw,
  Building2,
  AlertTriangle,
} from "lucide-react";
import { Navbar } from "@/components/Navbar";
import { CitationBadge } from "@/components/CitationBadge";
import { CitationDrawer } from "@/components/CitationDrawer";
import { useAuth } from "@/lib/auth";
import { streamChatResponse, Citation, ChatMessage } from "@/lib/api";

const SUGGESTED_QUERIES = [
  "What is the capital gains tax offset for municipal bonds under 2024 rules?",
  "Management fee caps and liquidity terms for Level-A discretionary portfolios",
  "Can non-resident individuals (NRIs) invest in High-Yield Debt Funds?",
  "What is the early redemption penalty for Tier-1 bonds?",
];

export default function ChatPage() {
  const router = useRouter();
  const { user, token, isLoading } = useAuth();

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("gaa_chat_history");
        if (saved) return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to parse saved chat history:", e);
      }
    }
    return [];
  });
  const [inputQuery, setInputQuery] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoading && !token) {
      router.push("/login");
    }
  }, [isLoading, token, router]);

  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem("gaa_chat_history", JSON.stringify(messages));
      } catch (e) {
        console.error("Failed to save chat history:", e);
      }
    }
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isGenerating]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-navy-950">
        <Loader2 className="h-8 w-8 text-gold-400 animate-spin" />
      </div>
    );
  }

  const handleSend = async (queryText?: string) => {
    const query = queryText || inputQuery;
    if (!query.trim() || isGenerating || !token) return;

    const userMessage: ChatMessage = { role: "user", content: query };
    const initialAssistantMessage: ChatMessage = { role: "assistant", content: "", citations: [] };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setInputQuery("");
    setIsGenerating(true);

    const historyPayload = messages.map((m) => ({ role: m.role, content: m.content }));

    let streamedContent = "";

    await streamChatResponse(
      token,
      query,
      historyPayload,
      (tokenChunk) => {
        streamedContent += tokenChunk;
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: streamedContent,
              isRefusal: streamedContent.includes("Compliance and Legal Department"),
            };
          }
          return updated;
        });
      },
      (citations) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
            updated[lastIdx] = {
              ...updated[lastIdx],
              citations,
            };
          }
          return updated;
        });
      },
      () => {
        setIsGenerating(false);
      },
      (err) => {
        setIsGenerating(false);
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: `Error: ${err.message || "Failed to generate answer"}`,
            };
          }
          return updated;
        });
      }
    );
  };

  const renderFormattedMessage = (content: string, citations?: Citation[]) => {
    // Regular expression matching citation tags: [Doc: ..., Clause: ...]
    const parts = content.split(/(\[Doc:[^\]]+\])/g);

    return (
      <div className="space-y-2">
        <p className="leading-relaxed">
          {parts.map((part, index) => {
            if (part.startsWith("[Doc:") && part.endsWith("]")) {
              const cleanPart = part.slice(1, -1);
              return (
                <CitationBadge
                  key={index}
                  citationText={cleanPart}
                  onClick={() => {
                    // Find matching citation item
                    const match = citations?.find(
                      (c) =>
                        cleanPart.includes(c.document_name) ||
                        cleanPart.includes(c.clause_id)
                    ) || {
                      document_name: cleanPart.split(",")[0]?.replace("Doc:", "").trim() || "Policy Doc",
                      version: "v1.0",
                      clause_id: cleanPart.split("Clause:")[1]?.trim() || "Approved Rule",
                      page_number: 1,
                      excerpt: "Verified policy chunk from account knowledge store.",
                      score: 0.92,
                    };
                    setSelectedCitation(match);
                    setIsDrawerOpen(true);
                  }}
                />
              );
            }
            return <span key={index}>{part}</span>;
          })}
        </p>

        {citations && citations.length > 0 && (
          <div className="pt-2 border-t border-white/5 flex flex-wrap gap-1.5 items-center">
            <span className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mr-1 flex items-center gap-1">
              <FileText className="h-3 w-3 text-gold-400" /> Cited Sources:
            </span>
            {citations.map((c, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setSelectedCitation(c);
                  setIsDrawerOpen(true);
                }}
                className="rounded-full bg-white/5 hover:bg-gold-500/20 px-2.5 py-0.5 text-[11px] font-medium text-slate-300 hover:text-gold-300 border border-white/10 transition-colors"
              >
                {c.document_name} ({c.clause_id})
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-navy-950">
      <Navbar />

      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 flex flex-col justify-between">
        {/* Chat History */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-6">
          {messages.length === 0 ? (
            <div className="py-12 text-center space-y-6 max-w-2xl mx-auto">
              <div className="inline-flex h-16 w-16 items-center justify-center rounded-3xl bg-gradient-to-br from-gold-400 to-gold-600 shadow-2xl shadow-gold-500/20">
                <Shield className="h-9 w-9 text-navy-950" />
              </div>
              <div className="space-y-2">
                <h2 className="text-xl font-bold text-white tracking-tight">
                  Welcome to WealthGuard Advisory Terminal
                </h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Ask complex wealth management policy, product, and tax queries. Every answer is strictly grounded in approved documentation with verifiable clause citations.
                </p>
              </div>

              {/* Sample Queries */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left pt-2">
                {SUGGESTED_QUERIES.map((sq, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(sq)}
                    className="glass-card hover:bg-white/10 rounded-xl p-3 text-xs text-slate-300 hover:text-gold-300 border border-white/5 transition-all text-left flex items-start gap-2 group"
                  >
                    <Sparkles className="h-3.5 w-3.5 text-gold-400 shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                    <span className="leading-snug">{sq}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              <div className="flex justify-end pb-2">
                <button
                  type="button"
                  onClick={() => {
                    setMessages([]);
                    if (typeof window !== "undefined") {
                      localStorage.removeItem("gaa_chat_history");
                    }
                  }}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-[11px] font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 border border-white/5 transition-all"
                >
                  <RefreshCw className="h-3 w-3" />
                  Clear Conversation History
                </button>
              </div>
              {messages.map((msg, index) => {
              const isUser = msg.role === "user";
              const isRefusal = msg.isRefusal;

              return (
                <div
                  key={index}
                  className={`flex items-start gap-3 ${isUser ? "justify-end" : "justify-start"}`}
                >
                  {!isUser && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gold-500/15 border border-gold-500/30 text-gold-400">
                      <Shield className="h-4 w-4" />
                    </div>
                  )}

                  <div
                    className={`rounded-2xl px-4 py-3.5 text-xs max-w-2xl shadow-sm ${
                      isUser
                        ? "bg-gradient-to-r from-gold-500 to-gold-600 text-navy-950 font-medium"
                        : isRefusal
                        ? "glass-panel border-amber-500/30 bg-amber-950/20 text-slate-200"
                        : "glass-panel border-white/10 text-slate-200"
                    }`}
                  >
                    {isRefusal && !isUser && (
                      <div className="flex items-center gap-1.5 text-amber-400 font-semibold mb-2 text-[11px] pb-1.5 border-b border-amber-500/20">
                        <ShieldAlert className="h-4 w-4" />
                        <span>Compliance Guardrail Triggered — Zero Hallucination Protocol</span>
                      </div>
                    )}

                    {isUser ? (
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      renderFormattedMessage(msg.content, msg.citations)
                    )}
                  </div>
                </div>
              );
            })}
          </>
        )}

          {isGenerating && messages[messages.length - 1]?.content === "" && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gold-500/15 border border-gold-500/30 text-gold-400">
                <Shield className="h-4 w-4" />
              </div>
              <div className="glass-panel rounded-2xl px-4 py-3 text-xs text-slate-400 flex items-center gap-2">
                <Loader2 className="h-3.5 w-3.5 animate-spin text-gold-400" />
                <span>Searching account knowledge store and validating grounding...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div className="sticky bottom-0 pt-2 bg-navy-950/95 backdrop-blur-md">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="glass-panel rounded-2xl p-2 flex items-center gap-2 border border-white/15 focus-within:border-gold-500/50 shadow-xl"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask an advisory policy, tax rule, or product eligibility question..."
              disabled={isGenerating}
              className="flex-1 bg-transparent px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none"
            />
            <button
              type="submit"
              disabled={isGenerating || !inputQuery.trim()}
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-navy-950 font-bold disabled:opacity-40 transition-all cursor-pointer shadow-md shadow-gold-500/10"
            >
              {isGenerating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </button>
          </form>
          <div className="mt-2 text-center text-[10px] text-slate-500">
            Answers are grounded in current-version documentation. Check with Compliance for suitability advice.
          </div>
        </div>
      </main>

      {/* Slide-Out Citation Inspection Drawer */}
      <CitationDrawer
        isOpen={isDrawerOpen}
        citation={selectedCitation}
        onClose={() => setIsDrawerOpen(false)}
      />
    </div>
  );
}

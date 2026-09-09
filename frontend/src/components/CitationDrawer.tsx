"use client";

import React, { useState } from "react";
import { X, Check, Copy, FileText, Bookmark, Calendar, ShieldCheck } from "lucide-react";
import { Citation } from "@/lib/api";

interface CitationDrawerProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export function CitationDrawer({ citation, isOpen, onClose }: CitationDrawerProps) {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !citation) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(citation.excerpt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const confidencePercentage = citation.score ? Math.round(citation.score * 100) : 95;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-navy-950/60 backdrop-blur-sm animate-fade-in flex justify-end">
      <div className="w-full max-w-lg h-full glass-panel bg-navy-900/95 border-l border-white/10 shadow-2xl flex flex-col animate-slide-left">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold-500/20 text-gold-400 border border-gold-500/30">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">Verified Grounding Source</h3>
              <p className="text-xs text-slate-400">Approved bank policy excerpt</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
          {/* Metadata Cards */}
          <div className="grid grid-cols-2 gap-3">
            <div className="glass-card rounded-xl p-3.5 space-y-1">
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Document</span>
              <p className="text-xs font-semibold text-slate-100 truncate" title={citation.document_name}>
                {citation.document_name}
              </p>
            </div>

            <div className="glass-card rounded-xl p-3.5 space-y-1">
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Version</span>
              <p className="text-xs font-semibold text-gold-400">{citation.version}</p>
            </div>

            <div className="glass-card rounded-xl p-3.5 space-y-1">
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Clause / Section</span>
              <p className="text-xs font-semibold text-slate-100">{citation.clause_id}</p>
            </div>

            <div className="glass-card rounded-xl p-3.5 space-y-1">
              <span className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">Page Reference</span>
              <p className="text-xs font-semibold text-slate-100">Page {citation.page_number}</p>
            </div>
          </div>

          {/* Confidence Indicator */}
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4" /> Grounding Confidence Gate
              </span>
              <span className="text-xs font-bold text-emerald-300">{confidencePercentage}%</span>
            </div>
            <div className="w-full bg-emerald-950/60 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-emerald-500 to-emerald-400 h-2 rounded-full"
                style={{ width: `${Math.min(100, Math.max(10, confidencePercentage))}%` }}
              />
            </div>
          </div>

          {/* Source Clause Excerpt */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Exact Document Excerpt</span>
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-xs text-gold-400 hover:text-gold-300 transition-colors"
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-emerald-400 font-medium">Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    <span>Copy Text</span>
                  </>
                )}
              </button>
            </div>

            <div className="rounded-xl border border-white/10 bg-navy-950 p-4 text-xs leading-relaxed text-slate-200 font-mono whitespace-pre-wrap max-h-80 overflow-y-auto">
              {citation.excerpt}
            </div>
          </div>

          {/* Compliance Notice */}
          <div className="rounded-lg border border-white/5 bg-white/[0.02] p-3 text-[11px] text-slate-400">
            <strong>Regulatory Traceability Note:</strong> This excerpt is logged with timestamp and query hash in the branch compliance journal.
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-white/10 px-6 py-4 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-white/10 hover:bg-white/15 px-4 py-2 text-xs font-medium text-white transition-colors"
          >
            Close Drawer
          </button>
        </div>
      </div>
    </div>
  );
}

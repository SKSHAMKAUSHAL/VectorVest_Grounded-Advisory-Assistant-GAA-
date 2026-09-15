"use client";

import React from "react";
import { FileText } from "lucide-react";
import { Citation } from "@/lib/api";

interface CitationBadgeProps {
  citationText: string;
  onClick: () => void;
}

export function CitationBadge({ citationText, onClick }: CitationBadgeProps) {
  return (
    <button
      onClick={onClick}
      type="button"
      className="inline-flex items-center gap-1 my-0.5 mx-1 rounded-md bg-gold-500/10 hover:bg-gold-500/25 px-2 py-0.5 text-xs font-semibold text-gold-300 border border-gold-500/30 transition-all cursor-pointer shadow-sm hover:scale-[1.02] active:scale-[0.98]"
      title="Click to view verified clause excerpt and source metadata"
    >
      <FileText className="h-3 w-3 text-gold-400" />
      <span className="truncate max-w-[260px]">{citationText}</span>
    </button>
  );
}

export default CitationBadge;

"use client";

import React, { useState } from "react";
import { X, UploadCloud, File, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { uploadDocumentFile } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface DocumentUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function DocumentUploadModal({ isOpen, onClose, onSuccess }: DocumentUploadModalProps) {
  const { token } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState<string>("policy_manual");
  const [version, setVersion] = useState<string>("v1.0");
  const [effectiveDate, setEffectiveDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [isDiscontinued, setIsDiscontinued] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !token) {
      setError("Please select a document file to upload.");
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("doc_type", docType);
    formData.append("version", version);
    formData.append("effective_date", effectiveDate);
    formData.append("is_discontinued", String(isDiscontinued));

    try {
      await uploadDocumentFile(token, formData);
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-950/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg glass-panel bg-navy-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold-500/20 text-gold-400 border border-gold-500/30">
              <UploadCloud className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-tight">Index New Documentation</h3>
              <p className="text-xs text-slate-400">Clause parsing, vector indexing & cumulative memory</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-white/10 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* File Picker */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">
              Document File (.pdf, .txt)
            </label>
            <div className="relative border-2 border-dashed border-white/15 hover:border-gold-500/40 rounded-xl p-5 text-center transition-colors">
              <input
                type="file"
                accept=".pdf,.txt,.docx"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setFile(e.target.files[0]);
                  }
                }}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="flex flex-col items-center">
                <File className="h-8 w-8 text-gold-400/80 mb-2" />
                {file ? (
                  <p className="text-xs font-semibold text-slate-200">{file.name}</p>
                ) : (
                  <>
                    <p className="text-xs font-medium text-slate-300">Click to select or drag and drop</p>
                    <p className="text-[11px] text-slate-500 mt-1">PDF circulars, policy manuals, or product brochures</p>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Doc Type & Version */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Document Type</label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full glass-input rounded-xl px-3 py-2 text-xs text-slate-100"
              >
                <option value="policy_manual">Policy Manual</option>
                <option value="tax_circular">Tax Circular</option>
                <option value="product_brochure">Product Brochure</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Document Version</label>
              <input
                type="text"
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="v1.0"
                className="w-full glass-input rounded-xl px-3 py-2 text-xs text-slate-100"
                required
              />
            </div>
          </div>

          {/* Effective Date */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Effective Date</label>
            <input
              type="date"
              value={effectiveDate}
              onChange={(e) => setEffectiveDate(e.target.value)}
              className="w-full glass-input rounded-xl px-3 py-2 text-xs text-slate-100"
              required
            />
          </div>

          {/* Discontinued Switch */}
          <div className="flex items-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.02] p-3">
            <input
              type="checkbox"
              id="is_discontinued"
              checked={isDiscontinued}
              onChange={(e) => setIsDiscontinued(e.target.checked)}
              className="h-4 w-4 rounded border-white/20 bg-navy-950 text-gold-500 focus:ring-gold-500/30"
            />
            <label htmlFor="is_discontinued" className="text-xs text-slate-300 cursor-pointer select-none">
              Mark as <strong>Discontinued / Sunset Product</strong> (will be excluded from default RM advisory retrieval)
            </label>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-white/10">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl px-4 py-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !file}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 px-5 py-2.5 text-xs font-bold text-navy-950 shadow-lg shadow-gold-500/15 disabled:opacity-50 transition-all cursor-pointer"
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Processing & Indexing...</span>
                </>
              ) : (
                <>
                  <UploadCloud className="h-4 w-4" />
                  <span>Upload & Index</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default DocumentUploadModal;

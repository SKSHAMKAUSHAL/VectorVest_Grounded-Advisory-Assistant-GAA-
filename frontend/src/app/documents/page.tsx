"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { fetchDocuments, deleteDocumentFile, downloadDocumentPdf, DocumentItem } from "@/lib/api";
import Navbar from "@/components/Navbar";
import DocumentUploadModal from "@/components/DocumentUploadModal";

export default function DocumentsPage() {
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();

  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedType, setSelectedType] = useState<string>("");
  const [showDiscontinued, setShowDiscontinued] = useState<boolean>(true);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Authentication guard
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const loadDocuments = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDocuments(
        token,
        selectedType || undefined,
        showDiscontinued ? undefined : false
      );
      setDocuments(data.documents);
    } catch (err: any) {
      setError(err.message || "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, [token, selectedType, showDiscontinued]);

  useEffect(() => {
    if (token) {
      loadDocuments();
    }
  }, [token, loadDocuments]);

  const handleDelete = async (doc: DocumentItem) => {
    if (!token) return;
    const confirmed = window.confirm(
      `Are you sure you want to delete "${doc.filename}" (v${doc.version})? This will also remove all indexed vectors from vector search.`
    );
    if (!confirmed) return;

    setDeletingId(doc.id);
    try {
      await deleteDocumentFile(token, doc.id);
      setActionSuccess(`Document "${doc.filename}" deleted successfully.`);
      setTimeout(() => setActionSuccess(null), 4000);
      loadDocuments();
    } catch (err: any) {
      alert(`Error deleting document: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const filteredDocs = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.doc_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    doc.version.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalChunks = documents.reduce((acc, d) => acc + (d.total_chunks || 0), 0);
  const discontinuedCount = documents.filter((d) => d.is_discontinued).length;
  const activeCount = documents.length - discontinuedCount;

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
        <div className="flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <span>Loading session...</span>
        </div>
      </div>
    );
  }

  const isComplianceAdmin = user.role === "ComplianceAdmin";

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar onOpenUpload={() => setIsUploadOpen(true)} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Document Knowledge Base
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Multi-Tenant Isolated
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Branch policy guidelines, product prospectuses, and compliance mandates indexed for semantic retrieval.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsUploadOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-emerald-950/40"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Upload Document
            </button>
          </div>
        </div>

        {/* Success toast */}
        {actionSuccess && (
          <div className="mt-4 p-3 bg-emerald-900/30 border border-emerald-600/40 text-emerald-300 rounded-lg text-sm flex items-center justify-between">
            <span>{actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-emerald-200">
              ✕
            </button>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Documents</div>
            <div className="text-2xl font-bold text-white mt-1">{documents.length}</div>
            <div className="text-xs text-slate-500 mt-1">Branch-scoped policies</div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Vector Chunks</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{totalChunks}</div>
            <div className="text-xs text-slate-500 mt-1">Clause-aware embeddings</div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Active Policies</div>
            <div className="text-2xl font-bold text-sky-400 mt-1">{activeCount}</div>
            <div className="text-xs text-slate-500 mt-1">Eligible for AI advisory</div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Discontinued</div>
            <div className="text-2xl font-bold text-amber-400 mt-1">{discontinuedCount}</div>
            <div className="text-xs text-slate-500 mt-1">Excluded from retrieval</div>
          </div>
        </div>

        {/* Filter / Search Bar */}
        <div className="bg-slate-900/50 border border-slate-800/80 rounded-xl p-4 mb-6 flex flex-col md:flex-row gap-4 items-stretch md:items-center justify-between">
          <div className="flex-1 relative">
            <svg
              className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by filename, document type, or version..."
              className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              aria-label="Filter by document type"
              className="bg-slate-950 border border-slate-800 text-slate-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="">All Document Types</option>
              <option value="Fund Factsheet">Fund Factsheet</option>
              <option value="Regulatory Circular">Regulatory Circular</option>
              <option value="Product Disclosure">Product Disclosure</option>
              <option value="Policy Term Sheet">Policy Term Sheet</option>
              <option value="Investment Mandate">Investment Mandate</option>
            </select>

            <label className="flex items-center gap-2 text-xs text-slate-400 cursor-pointer select-none bg-slate-950 px-3 py-2 border border-slate-800 rounded-lg">
              <input
                type="checkbox"
                checked={showDiscontinued}
                onChange={(e) => setShowDiscontinued(e.target.checked)}
                className="w-3.5 h-3.5 text-emerald-600 rounded bg-slate-900 border-slate-700"
              />
              <span>Include Discontinued</span>
            </label>

            <button
              onClick={loadDocuments}
              className="p-2 text-slate-400 hover:text-slate-200 bg-slate-950 border border-slate-800 rounded-lg transition-colors"
              title="Refresh list"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>

        {/* Table / Content */}
        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/60 text-rose-300 rounded-xl text-sm mb-6">
            {error}
          </div>
        )}

        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4 font-semibold">Document</th>
                  <th className="py-3.5 px-4 font-semibold">Type</th>
                  <th className="py-3.5 px-4 font-semibold">Version</th>
                  <th className="py-3.5 px-4 font-semibold">Effective Date</th>
                  <th className="py-3.5 px-4 font-semibold">Chunks</th>
                  <th className="py-3.5 px-4 font-semibold">Status</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-500">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                        <span>Loading document library...</span>
                      </div>
                    </td>
                  </tr>
                ) : filteredDocs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-500">
                      <div className="max-w-sm mx-auto">
                        <svg className="w-10 h-10 text-slate-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-sm font-medium text-slate-300">No documents found</p>
                        <p className="text-xs text-slate-500 mt-1">
                          Upload financial guidelines, fund prospectuses, or compliance circulars to seed the advisor model.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredDocs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-4 px-4">
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded-lg bg-slate-800 border border-slate-700/60 text-slate-300 mt-0.5">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          </div>
                          <div>
                            <div className="font-medium text-white line-clamp-1">{doc.filename}</div>
                            <div className="text-xs text-slate-500 mt-0.5">
                              Uploaded {new Date(doc.created_at).toLocaleDateString()}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          {doc.doc_type}
                        </span>
                      </td>

                      <td className="py-4 px-4 whitespace-nowrap">
                        <span className="font-mono text-xs text-slate-300">v{doc.version}</span>
                      </td>

                      <td className="py-4 px-4 whitespace-nowrap text-xs text-slate-400">
                        {doc.effective_date ? new Date(doc.effective_date).toLocaleDateString() : "N/A"}
                      </td>

                      <td className="py-4 px-4 whitespace-nowrap text-xs">
                        <span className="text-emerald-400 font-semibold">{doc.total_chunks}</span>
                        <span className="text-slate-500"> chunks ({doc.total_pages} pgs)</span>
                      </td>

                      <td className="py-4 px-4 whitespace-nowrap">
                        <div className="flex flex-col gap-1 items-start">
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                              doc.status === "indexed"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : doc.status === "processing"
                                ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                            }`}
                          >
                            {doc.status.toUpperCase()}
                          </span>
                          {doc.is_discontinued && (
                            <span className="px-2 py-0.5 rounded-full text-2xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                              Discontinued
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4 whitespace-nowrap text-right">
                        <div className="inline-flex items-center gap-2 justify-end">
                          <button
                            type="button"
                            onClick={async () => {
                              if (!token) return;
                              try {
                                await downloadDocumentPdf(token, doc.id, doc.filename);
                              } catch (err: any) {
                                alert(err.message || "Failed to download PDF");
                              }
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-gold-400 hover:text-gold-200 hover:bg-gold-950/40 rounded transition-colors border border-gold-500/30"
                            title="Export verified policy summary PDF"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <span>PDF</span>
                          </button>

                          <button
                            onClick={() => handleDelete(doc)}
                            disabled={deletingId === doc.id}
                            className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold text-rose-400 hover:text-white hover:bg-rose-600/30 rounded-lg transition-all border border-rose-500/30 hover:border-rose-500 disabled:opacity-50 cursor-pointer shadow-sm"
                            title={`Delete ${doc.filename}`}
                          >
                            {deletingId === doc.id ? (
                              <>
                                <div className="w-3.5 h-3.5 border-2 border-rose-400 border-t-transparent rounded-full animate-spin"></div>
                                <span>Deleting...</span>
                              </>
                            ) : (
                              <>
                                <svg className="w-3.5 h-3.5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                <span>Delete PDF</span>
                              </>
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* Upload Modal */}
      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={() => {
          loadDocuments();
          setActionSuccess("Document uploaded and indexed into vector memory.");
          setTimeout(() => setActionSuccess(null), 4000);
        }}
      />
    </div>
  );
}

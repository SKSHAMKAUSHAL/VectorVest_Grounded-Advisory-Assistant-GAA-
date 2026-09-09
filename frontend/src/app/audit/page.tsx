"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { fetchAuditLogs, AuditLogItem } from "@/lib/api";
import Navbar from "@/components/Navbar";
import DocumentUploadModal from "@/components/DocumentUploadModal";

export default function AuditPage() {
  const { user, token, loading: authLoading } = useAuth();
  const router = useRouter();

  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [refusalFilter, setRefusalFilter] = useState<string>("all"); // "all" | "refusals" | "approved"
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditLogItem | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  // Auth guard
  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  const loadAuditLogs = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const isRefusalParam =
        refusalFilter === "refusals" ? true : refusalFilter === "approved" ? false : undefined;
      const res = await fetchAuditLogs(token, 100, 0, isRefusalParam);
      setLogs(res.logs);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || "Failed to load compliance audit logs");
    } finally {
      setLoading(false);
    }
  }, [token, refusalFilter]);

  useEffect(() => {
    if (token) {
      loadAuditLogs();
    }
  }, [token, loadAuditLogs]);

  const filteredLogs = logs.filter((log) => {
    const qMatch = log.query.toLowerCase().includes(searchQuery.toLowerCase());
    const respMatch = log.response.toLowerCase().includes(searchQuery.toLowerCase());
    const userMatch = log.user_id.toLowerCase().includes(searchQuery.toLowerCase());
    return qMatch || respMatch || userMatch;
  });

  // Calculate metrics
  const totalCount = total || logs.length;
  const refusalCount = logs.filter((l) => l.is_refusal).length;
  const approvedCount = logs.length - refusalCount;
  const avgLatency =
    logs.length > 0
      ? Math.round(logs.reduce((acc, l) => acc + (l.latency_ms || 0), 0) / logs.length)
      : 0;

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
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Compliance & Audit Trail
              </h1>
              {isComplianceAdmin ? (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                  Compliance Officer Mode
                </span>
              ) : (
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                  RM Activity View
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Immutable logging of all advisory queries, multi-turn rewrites, vector similarity scores, and zero-hallucination guardrail triggers.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadAuditLogs}
              className="inline-flex items-center gap-2 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-lg text-sm text-slate-300 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh Logs
            </button>
          </div>
        </div>

        {/* Audit Metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Advisory Queries</div>
            <div className="text-2xl font-bold text-white mt-1">{totalCount}</div>
            <div className="text-xs text-slate-500 mt-1">Branch-isolated interaction logs</div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Approved Advice (&ge;0.68)</div>
            <div className="text-2xl font-bold text-emerald-400 mt-1">
              {approvedCount}
              <span className="text-xs font-normal text-slate-400 ml-2">
                ({logs.length > 0 ? Math.round((approvedCount / logs.length) * 100) : 100}%)
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-1">Fully cited & policy grounded</div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Compliance Escalations (&lt;0.68)</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">
              {refusalCount}
              <span className="text-xs font-normal text-slate-400 ml-2">
                ({logs.length > 0 ? Math.round((refusalCount / logs.length) * 100) : 0}%)
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-1">Zero-hallucination refusals</div>
          </div>

          <div className="bg-slate-900/70 border border-slate-800/80 rounded-xl p-4">
            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Average Latency</div>
            <div className="text-2xl font-bold text-sky-400 mt-1">
              {avgLatency} <span className="text-xs font-normal text-slate-400">ms</span>
            </div>
            <div className="text-xs text-slate-500 mt-1">Embed + vector + LLM pipeline</div>
          </div>
        </div>

        {/* Filter Bar */}
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
              placeholder="Search query, response text, or user ID..."
              className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setRefusalFilter("all")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                refusalFilter === "all"
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200"
              }`}
            >
              All Queries
            </button>
            <button
              onClick={() => setRefusalFilter("refusals")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                refusalFilter === "refusals"
                  ? "bg-rose-600 text-white"
                  : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200"
              }`}
            >
              Escalations (&lt;0.68)
            </button>
            <button
              onClick={() => setRefusalFilter("approved")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                refusalFilter === "approved"
                  ? "bg-sky-600 text-white"
                  : "bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200"
              }`}
            >
              Approved Grounded
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-4 bg-rose-950/40 border border-rose-800/60 text-rose-300 rounded-xl text-sm mb-6">
            {error}
          </div>
        )}

        {/* Audit Log Table */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-slate-950/60 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4 font-semibold">Timestamp</th>
                  <th className="py-3.5 px-4 font-semibold">Query</th>
                  <th className="py-3.5 px-4 font-semibold">Max Similarity</th>
                  <th className="py-3.5 px-4 font-semibold">Compliance Status</th>
                  <th className="py-3.5 px-4 font-semibold">Latency</th>
                  <th className="py-3.5 px-4 font-semibold text-right">Inspection</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-4 h-4 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                        <span>Loading audit trail records...</span>
                      </div>
                    </td>
                  </tr>
                ) : filteredLogs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-500">
                      <div className="max-w-sm mx-auto">
                        <svg className="w-10 h-10 text-slate-600 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-sm font-medium text-slate-300">No audit records found</p>
                        <p className="text-xs text-slate-500 mt-1">
                          Advisory queries asked by Wealth RMs will automatically log here with similarity verification scores.
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredLogs.map((log) => {
                    const isRefusal = log.is_refusal || (log.similarity_score < 0.68);
                    return (
                      <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-4 px-4 whitespace-nowrap text-xs text-slate-400 font-mono">
                          {new Date(log.created_at).toLocaleString()}
                        </td>

                        <td className="py-4 px-4 max-w-xs sm:max-w-sm">
                          <div className="font-medium text-white truncate" title={log.query}>
                            {log.query}
                          </div>
                          {log.rewritten_query && log.rewritten_query !== log.query && (
                            <div className="text-2xs text-slate-500 truncate mt-0.5" title={`Rewritten: ${log.rewritten_query}`}>
                              ↳ <span className="italic">Rewritten:</span> {log.rewritten_query}
                            </div>
                          )}
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap">
                          <div className="flex items-center gap-2">
                            <span
                              className={`font-mono text-xs font-bold ${
                                log.similarity_score >= 0.68
                                  ? "text-emerald-400"
                                  : "text-rose-400"
                              }`}
                            >
                              {(log.similarity_score * 100).toFixed(1)}%
                            </span>
                            <div className="w-14 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  log.similarity_score >= 0.68 ? "bg-emerald-500" : "bg-rose-500"
                                }`}
                                style={{ width: `${Math.min(100, Math.max(0, log.similarity_score * 100))}%` }}
                              ></div>
                            </div>
                          </div>
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap">
                          {isRefusal ? (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
                              Escalation Refusal
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                              Grounded Advice
                            </span>
                          )}
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap text-xs text-slate-400 font-mono">
                          {log.latency_ms} ms
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap text-right">
                          <button
                            onClick={() => setSelectedLog(log)}
                            className="px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-750 rounded border border-slate-700 transition-colors"
                          >
                            Inspect Trace
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Inspection Modal */}
        {selectedLog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 shadow-2xl relative max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white">Compliance Audit Record</h3>
                  <span className="text-xs font-mono text-slate-500">#{selectedLog.id.slice(0, 8)}</span>
                </div>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4 my-4 text-sm">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                    Relationship Manager Query
                  </div>
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-200">
                    {selectedLog.query}
                  </div>
                </div>

                {selectedLog.rewritten_query && (
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                      Multi-Turn Rewritten Query
                    </div>
                    <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-300 font-mono text-xs">
                      {selectedLog.rewritten_query}
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    <div className="text-2xs text-slate-400 uppercase font-semibold">Semantic Match Score</div>
                    <div className="text-lg font-bold font-mono mt-0.5 text-emerald-400">
                      {(selectedLog.similarity_score * 100).toFixed(2)}%
                    </div>
                    <div className="text-2xs text-slate-500 mt-0.5">Threshold: 68.0% minimum</div>
                  </div>

                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg">
                    <div className="text-2xs text-slate-400 uppercase font-semibold">Guardrail Status</div>
                    <div className="mt-1">
                      {selectedLog.is_refusal ? (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-500/20 text-rose-300">
                          Refusal Escalated
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-emerald-500/20 text-emerald-300">
                          Compliant Advisory
                        </span>
                      )}
                    </div>
                    <div className="text-2xs text-slate-500 mt-0.5">Latency: {selectedLog.latency_ms} ms</div>
                  </div>
                </div>

                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                    System Advisory Output
                  </div>
                  <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-slate-200 whitespace-pre-wrap font-sans leading-relaxed text-xs">
                    {selectedLog.response}
                  </div>
                </div>

                <div className="text-2xs text-slate-500 pt-2 border-t border-slate-800 flex justify-between">
                  <span>Timestamp: {new Date(selectedLog.created_at).toISOString()}</span>
                  <span>Tenant ID: {selectedLog.account_id}</span>
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedLog(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium transition-colors"
                >
                  Close Inspection
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      <DocumentUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={() => loadAuditLogs()}
      />
    </div>
  );
}

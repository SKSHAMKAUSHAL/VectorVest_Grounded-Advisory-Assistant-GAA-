"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Shield, Mail, ArrowLeft, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { requestPasswordReset } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setMessage(null);

    try {
      const res = await requestPasswordReset(email);
      setMessage(res.message);
      if (res.reset_token) {
        setResetToken(res.reset_token);
      }
    } catch (err: any) {
      setError(err.message || "Failed to generate password reset request");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 shadow-xl shadow-gold-500/15">
            <Shield className="h-6 w-6 text-navy-950" />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">Reset Credentials</h1>
          <p className="text-xs text-slate-400">
            Enter your bank email to receive a secure time-limited reset token.
          </p>
        </div>

        <div className="glass-panel rounded-2xl p-7 border border-white/10 shadow-2xl space-y-4">
          {error && (
            <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div className="space-y-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 text-xs text-emerald-300">
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span>{message}</span>
              </div>
              {resetToken && (
                <div className="rounded-lg bg-navy-950 p-3 font-mono text-[11px] text-slate-200 border border-emerald-500/20 break-all">
                  <div className="text-[10px] uppercase tracking-wider text-slate-400 mb-1">Generated Reset Token (Dev):</div>
                  {resetToken}
                </div>
              )}
              <Link
                href={`/reset-password?token=${encodeURIComponent(resetToken || "")}`}
                className="inline-block rounded-lg bg-emerald-500 hover:bg-emerald-600 text-navy-950 font-bold px-3 py-1.5 text-xs transition-colors"
              >
                Proceed to Set New Password &rarr;
              </Link>
            </div>
          )}

          {!resetToken && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Registered Email</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="rm@wealth.bank.com"
                    required
                    className="w-full glass-input rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 py-3 text-xs font-bold text-navy-950 shadow-lg shadow-gold-500/20 disabled:opacity-50 transition-all cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Dispatching Request...</span>
                  </>
                ) : (
                  <span>Request Reset Token</span>
                )}
              </button>
            </form>
          )}

          <div className="border-t border-white/10 pt-4 text-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Terminal Sign In</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

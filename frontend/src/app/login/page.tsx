"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Shield, Lock, Mail, ArrowRight, AlertCircle, Loader2, Sparkles } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await login(email, password);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Invalid email or password");
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickFill = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4 bg-gradient-to-b from-navy-950 via-navy-900 to-navy-950">
      <div className="w-full max-w-md space-y-6">
        {/* Branding Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 shadow-xl shadow-gold-500/15">
            <Shield className="h-8 w-8 text-navy-950" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white">WealthGuard AI</h1>
          <p className="text-xs text-slate-400 max-w-xs mx-auto">
            Grounded Policy & Compliance Engine for Wealth Management Relationship Managers
          </p>
        </div>

        {/* Login Card */}
        <div className="glass-panel rounded-2xl p-7 border border-white/10 shadow-2xl space-y-5">
          {error && (
            <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Bank Email</label>
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

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-slate-300">Password</label>
                <Link
                  href="/forgot-password"
                  className="text-[11px] text-gold-400 hover:text-gold-300 transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
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
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Terminal</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Fill Demo Credentials */}
          <div className="border-t border-white/10 pt-4 space-y-2">
            <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-gold-400" /> Demo Credentials Quick-Fill:
            </span>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill("rm@wealth.bank.com", "AdvisoryPass2024!")}
                className="rounded-lg bg-white/5 hover:bg-white/10 p-2 text-left border border-white/5 transition-colors"
              >
                <div className="text-[11px] font-semibold text-slate-200">Relationship Mgr</div>
                <div className="text-[10px] text-slate-400 truncate">rm@wealth.bank.com</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill("compliance@wealth.bank.com", "AuditSecure2024!")}
                className="rounded-lg bg-white/5 hover:bg-white/10 p-2 text-left border border-white/5 transition-colors"
              >
                <div className="text-[11px] font-semibold text-emerald-400">Compliance Admin</div>
                <div className="text-[10px] text-slate-400 truncate">compliance@wealth.bank.com</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Shield,
  Lock,
  Mail,
  User,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Loader2,
  Eye,
  EyeOff,
  Check,
  X,
  FileCheck2,
  Building2,
  Scale,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

// ---------------------------------------------------------------------------
// Validation Schemas (Strict Zod Specs)
// ---------------------------------------------------------------------------
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const nameRegex = /^[a-zA-Z\s]+$/;

export const signInSchema = z.object({
  email: z
    .string()
    .min(1, "Email address is required")
    .regex(emailRegex, "Please enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean().optional(),
});

export const signUpSchema = z
  .object({
    fullName: z
      .string()
      .min(2, "Full name must be at least 2 characters")
      .regex(nameRegex, "Full name can only contain letters and spaces"),
    email: z
      .string()
      .min(1, "Email address is required")
      .regex(emailRegex, "Please enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .regex(/[^a-zA-Z0-9]/, "Password must contain at least one special character"),
    confirmPassword: z.string().min(1, "Please confirm your password"),
    termsAccepted: z.boolean().refine((val) => val === true, {
      message: "You must accept the terms & conditions",
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type SignInFormData = z.infer<typeof signInSchema>;
export type SignUpFormData = z.infer<typeof signUpSchema>;

interface AuthModuleProps {
  initialTab?: "signin" | "signup";
}

export default function AuthModule({ initialTab = "signin" }: AuthModuleProps) {
  const router = useRouter();
  const { login, signup } = useAuth();
  const [activeTab, setActiveTab] = useState<"signin" | "signup">(initialTab);

  // Password visibility states
  const [showSignInPassword, setShowSignInPassword] = useState(false);
  const [showSignUpPassword, setShowSignUpPassword] = useState(false);
  const [showSignUpConfirmPassword, setShowSignUpConfirmPassword] = useState(false);

  // Server error / success states
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Forms setup
  const {
    register: registerSignIn,
    handleSubmit: handleSubmitSignIn,
    setValue: setValueSignIn,
    formState: { errors: signInErrors, isSubmitting: isSignInSubmitting },
  } = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
    mode: "onBlur",
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
  });

  const {
    register: registerSignUp,
    handleSubmit: handleSubmitSignUp,
    watch: watchSignUp,
    formState: { errors: signUpErrors, isSubmitting: isSignUpSubmitting },
  } = useForm<SignUpFormData>({
    resolver: zodResolver(signUpSchema),
    mode: "onBlur",
    defaultValues: {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
      termsAccepted: undefined,
    },
  });

  // Calculate live password strength
  const signUpPassword = watchSignUp("password") || "";
  const passwordStrength = useMemo(() => {
    if (!signUpPassword) return { score: 0, label: "None", color: "bg-slate-700" };
    let score = 0;
    if (signUpPassword.length >= 8) score += 1;
    if (/[A-Z]/.test(signUpPassword)) score += 1;
    if (/[a-z]/.test(signUpPassword)) score += 1;
    if (/[0-9]/.test(signUpPassword)) score += 1;
    if (/[^a-zA-Z0-9]/.test(signUpPassword)) score += 1;

    if (score <= 2) return { score: 1, label: "Weak", color: "bg-rose-500", text: "text-rose-400" };
    if (score <= 4) return { score: 2, label: "Medium", color: "bg-amber-500", text: "text-amber-400" };
    return { score: 3, label: "Strong", color: "bg-emerald-500", text: "text-emerald-400" };
  }, [signUpPassword]);

  // Handle Sign In submission
  const onSignInSubmit = async (data: SignInFormData) => {
    setServerError(null);
    setSuccessMessage(null);
    try {
      await login(data.email, data.password);
      setSuccessMessage("Authentication verified. Redirecting to advisory workspace...");
      setTimeout(() => {
        router.push("/");
      }, 600);
    } catch (err: any) {
      setServerError(err.message || "Invalid email or password");
    }
  };

  // Handle Sign Up submission
  const onSignUpSubmit = async (data: SignUpFormData) => {
    setServerError(null);
    setSuccessMessage(null);
    try {
      await signup(data.fullName, data.email, data.password);
      setSuccessMessage("Account created successfully! Redirecting to advisory workspace...");
      setTimeout(() => {
        router.push("/");
      }, 800);
    } catch (err: any) {
      setServerError(err.message || "Registration failed. Please try again.");
    }
  };

  // Demo credential quick-fill
  const fillDemoCredentials = (email: string, pass: string) => {
    setValueSignIn("email", email, { shouldValidate: true });
    setValueSignIn("password", pass, { shouldValidate: true });
    setServerError(null);
  };

  return (
    <div className="flex min-h-screen bg-navy-950 text-slate-100 font-sans">
      {/* ------------------------------------------------------------------ */}
      {/* LEFT PANEL: Immersive Branding & Value Propositions (Desktop Only) */}
      {/* ------------------------------------------------------------------ */}
      <aside className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 bg-gradient-to-br from-navy-950 via-navy-900 to-navy-950 border-r border-white/5 relative overflow-hidden">
        {/* Ambient Decorative Orbs */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-gold-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-32 -right-32 w-96 h-96 rounded-full bg-navy-600/20 blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center shadow-lg shadow-gold-500/20">
              <Shield className="h-6 w-6 text-navy-950 font-bold" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">WealthGuard AI</h1>
              <p className="text-xs text-gold-400 font-medium">Grounded Advisory Assistant (GAA)</p>
            </div>
          </div>
          <p className="text-sm text-slate-300 max-w-md leading-relaxed">
            Institutional-grade conversational policy copilot for Wealth Relationship Managers. 
            Empowering advisors with deterministic compliance guardrails and zero-hallucination answers.
          </p>
        </div>

        {/* Value Proposition Highlights */}
        <div className="relative z-10 space-y-6 my-auto max-w-md">
          <div className="flex items-start gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/5 backdrop-blur-sm">
            <div className="p-2.5 rounded-lg bg-gold-500/10 text-gold-400 shrink-0">
              <Scale className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Zero-Hallucination Confidence Gate</h2>
              <p className="text-xs text-slate-400 mt-1">
                Deterministic refusal guardrail halts ungrounded answers when similarity falls below 0.68, redirecting to Legal & Compliance.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/5 backdrop-blur-sm">
            <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-400 shrink-0">
              <FileCheck2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Verifiable Clause Citations</h2>
              <p className="text-xs text-slate-400 mt-1">
                Every policy assertion provides exact document name, version, clause ID, and page excerpts with click-to-preview drawers.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/5 backdrop-blur-sm">
            <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400 shrink-0">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white">Multi-Tenant Branch Isolation</h2>
              <p className="text-xs text-slate-400 mt-1">
                Strict partition scopes isolate branch policy databases, preventing cross-tenant information leakage across advisory desks.
              </p>
            </div>
          </div>
        </div>

        {/* Security & Regulatory Badges */}
        <div className="relative z-10 pt-6 border-t border-white/5 flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>SOC2 Type II Aligned</span>
          </div>
          <span>ISO 27001 Data Governance</span>
          <span>AES-256 Vector Encryption</span>
        </div>
      </aside>

      {/* ------------------------------------------------------------------ */}
      {/* RIGHT PANEL: Centered Responsive Authentication Container         */}
      {/* ------------------------------------------------------------------ */}
      <main className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-10 lg:p-12 relative">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile Brand Header */}
          <div className="lg:hidden text-center space-y-2 mb-6">
            <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 shadow-lg shadow-gold-500/20">
              <Shield className="h-6 w-6 text-navy-950 font-bold" />
            </div>
            <h1 className="text-xl font-bold text-white">WealthGuard AI</h1>
            <p className="text-xs text-slate-400">Grounded Advisory Assistant (GAA)</p>
          </div>

          {/* Tab Switcher */}
          <div className="flex rounded-xl bg-navy-900/80 p-1 border border-white/10" role="tablist" aria-label="Authentication Options">
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "signin"}
              onClick={() => {
                setActiveTab("signin");
                setServerError(null);
                setSuccessMessage(null);
              }}
              className={`flex-1 py-2.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === "signin"
                  ? "bg-gold-500 text-navy-950 shadow-md shadow-gold-500/10 font-bold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={activeTab === "signup"}
              onClick={() => {
                setActiveTab("signup");
                setServerError(null);
                setSuccessMessage(null);
              }}
              className={`flex-1 py-2.5 text-xs font-semibold rounded-lg transition-all ${
                activeTab === "signup"
                  ? "bg-gold-500 text-navy-950 shadow-md shadow-gold-500/10 font-bold"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Dismissible Server Error Banner */}
          {serverError && (
            <div
              role="alert"
              className="flex items-start justify-between gap-2.5 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs animate-in fade-in"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{serverError}</span>
              </div>
              <button
                type="button"
                onClick={() => setServerError(null)}
                className="text-rose-400 hover:text-rose-200"
                aria-label="Dismiss error notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}

          {/* Success Banner */}
          {successMessage && (
            <div
              role="status"
              className="flex items-center gap-2 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs animate-in fade-in"
            >
              <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* -------------------------------------------------------------- */}
          {/* TAB 1: SIGN IN FORM                                            */}
          {/* -------------------------------------------------------------- */}
          {activeTab === "signin" && (
            <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-5">
              <div className="space-y-1">
                <h2 className="text-lg font-bold text-white">Sign In to Advisory Terminal</h2>
                <p className="text-xs text-slate-400">Enter your institutional credentials to access the bank policy copilot.</p>
              </div>



              <form onSubmit={handleSubmitSignIn(onSignInSubmit)} className="space-y-4" noValidate>
                {/* Email Field */}
                <div>
                  <label htmlFor="signin-email" className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Corporate Bank Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                      id="signin-email"
                      type="email"
                      placeholder="name@example.com"
                      autoComplete="email"
                      aria-invalid={!!signInErrors.email}
                      aria-describedby={signInErrors.email ? "signin-email-error" : undefined}
                      {...registerSignIn("email")}
                      className={`w-full glass-input rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white transition-all ${
                        signInErrors.email
                          ? "border-rose-500/80 focus:ring-rose-500/30 focus:border-rose-500"
                          : "border-white/10 focus:border-gold-500"
                      }`}
                    />
                  </div>
                  {signInErrors.email && (
                    <p id="signin-email-error" className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {signInErrors.email.message}
                    </p>
                  )}
                </div>

                {/* Password Field */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label htmlFor="signin-password" className="text-xs font-semibold text-slate-300">
                      Password
                    </label>
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
                      id="signin-password"
                      type={showSignInPassword ? "text" : "password"}
                      placeholder="••••••••"
                      autoComplete="current-password"
                      aria-invalid={!!signInErrors.password}
                      aria-describedby={signInErrors.password ? "signin-password-error" : undefined}
                      {...registerSignIn("password")}
                      className={`w-full glass-input rounded-xl pl-10 pr-10 py-2.5 text-xs text-white transition-all ${
                        signInErrors.password
                          ? "border-rose-500/80 focus:ring-rose-500/30 focus:border-rose-500"
                          : "border-white/10 focus:border-gold-500"
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowSignInPassword(!showSignInPassword)}
                      className="absolute right-3 top-2.5 p-0.5 text-slate-400 hover:text-slate-200 transition-colors"
                      aria-label={showSignInPassword ? "Hide password" : "Show password"}
                    >
                      {showSignInPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {signInErrors.password && (
                    <p id="signin-password-error" className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {signInErrors.password.message}
                    </p>
                  )}
                </div>

                {/* Remember Me */}
                <div className="flex items-center gap-2 pt-0.5">
                  <input
                    id="remember-me"
                    type="checkbox"
                    {...registerSignIn("rememberMe")}
                    className="h-3.5 w-3.5 rounded border-white/20 bg-navy-900 text-gold-500 focus:ring-gold-500/30 accent-gold-500"
                  />
                  <label htmlFor="remember-me" className="text-xs text-slate-300 cursor-pointer select-none">
                    Remember me on this trusted terminal
                  </label>
                </div>

                {/* Primary CTA Button */}
                <button
                  type="submit"
                  disabled={isSignInSubmitting}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-navy-950 font-bold text-xs tracking-wide shadow-lg shadow-gold-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSignInSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Authenticating...</span>
                    </>
                  ) : (
                    <>
                      <span>Sign In</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Quick-Fill Demo Options */}
              <div className="pt-2 border-t border-white/10 space-y-2">
                <span className="text-[10px] font-semibold tracking-wider uppercase text-slate-400 block">
                  Quick Access Demo Roles
                </span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => fillDemoCredentials("rm@wealth.bank.com", "AdvisoryPass2024!")}
                    className="p-2 text-left rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/5 transition-all group"
                  >
                    <div className="text-[11px] font-semibold text-slate-200 group-hover:text-gold-300">
                      RM Advisor
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">rm@wealth.bank.com</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => fillDemoCredentials("compliance@wealth.bank.com", "AuditSecure2024!")}
                    className="p-2 text-left rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/5 transition-all group"
                  >
                    <div className="text-[11px] font-semibold text-slate-200 group-hover:text-gold-300">
                      Compliance Officer
                    </div>
                    <div className="text-[10px] text-slate-400 truncate">compliance@wealth.bank.com</div>
                  </button>
                </div>
              </div>

              {/* Bottom Switcher */}
              <div className="text-center text-xs text-slate-400 pt-1">
                Don&apos;t have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab("signup");
                    setServerError(null);
                  }}
                  className="font-semibold text-gold-400 hover:text-gold-300 underline underline-offset-4"
                >
                  Sign Up
                </button>
              </div>
            </div>
          )}

          {/* -------------------------------------------------------------- */}
          {/* TAB 2: SIGN UP (REGISTRATION) FORM                            */}
          {/* -------------------------------------------------------------- */}
          {activeTab === "signup" && (
            <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-white/10 shadow-2xl space-y-5">
              <div className="space-y-1">
                <h2 className="text-lg font-bold text-white">Create Advisor Account</h2>
                <p className="text-xs text-slate-400">Register a new Relationship Manager profile on the central branch.</p>
              </div>



              <form onSubmit={handleSubmitSignUp(onSignUpSubmit)} className="space-y-3.5" noValidate>
                {/* Full Name */}
                <div>
                  <label htmlFor="signup-name" className="block text-xs font-semibold text-slate-300 mb-1">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                      id="signup-name"
                      type="text"
                      placeholder="Jane Doe"
                      autoComplete="name"
                      aria-invalid={!!signUpErrors.fullName}
                      aria-describedby={signUpErrors.fullName ? "signup-name-error" : undefined}
                      {...registerSignUp("fullName")}
                      className={`w-full glass-input rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white transition-all ${
                        signUpErrors.fullName
                          ? "border-rose-500/80 focus:ring-rose-500/30 focus:border-rose-500"
                          : "border-white/10 focus:border-gold-500"
                      }`}
                    />
                  </div>
                  {signUpErrors.fullName && (
                    <p id="signup-name-error" className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {signUpErrors.fullName.message}
                    </p>
                  )}
                </div>

                {/* Email Address */}
                <div>
                  <label htmlFor="signup-email" className="block text-xs font-semibold text-slate-300 mb-1">
                    Work Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                      id="signup-email"
                      type="email"
                      placeholder="name@example.com"
                      autoComplete="email"
                      aria-invalid={!!signUpErrors.email}
                      aria-describedby={signUpErrors.email ? "signup-email-error" : undefined}
                      {...registerSignUp("email")}
                      className={`w-full glass-input rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white transition-all ${
                        signUpErrors.email
                          ? "border-rose-500/80 focus:ring-rose-500/30 focus:border-rose-500"
                          : "border-white/10 focus:border-gold-500"
                      }`}
                    />
                  </div>
                  {signUpErrors.email && (
                    <p id="signup-email-error" className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {signUpErrors.email.message}
                    </p>
                  )}
                </div>

                {/* Password Field */}
                <div>
                  <label htmlFor="signup-password" className="block text-xs font-semibold text-slate-300 mb-1">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                      id="signup-password"
                      type={showSignUpPassword ? "text" : "password"}
                      placeholder="Min. 8 characters"
                      autoComplete="new-password"
                      aria-invalid={!!signUpErrors.password}
                      aria-describedby="signup-password-hint"
                      {...registerSignUp("password")}
                      className={`w-full glass-input rounded-xl pl-10 pr-10 py-2.5 text-xs text-white transition-all ${
                        signUpErrors.password
                          ? "border-rose-500/80 focus:ring-rose-500/30 focus:border-rose-500"
                          : "border-white/10 focus:border-gold-500"
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowSignUpPassword(!showSignUpPassword)}
                      className="absolute right-3 top-2.5 p-0.5 text-slate-400 hover:text-slate-200 transition-colors"
                      aria-label={showSignUpPassword ? "Hide password" : "Show password"}
                    >
                      {showSignUpPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>

                  {/* Password Strength Indicator Bar */}
                  {signUpPassword && (
                    <div className="mt-2 space-y-1" id="signup-password-hint">
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="text-slate-400">Security strength:</span>
                        <span className={`font-semibold ${passwordStrength.text}`}>
                          {passwordStrength.label}
                        </span>
                      </div>
                      <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden flex gap-1">
                        <div
                          className={`h-full flex-1 rounded-full transition-all duration-300 ${
                            passwordStrength.score >= 1 ? passwordStrength.color : "bg-transparent"
                          }`}
                        />
                        <div
                          className={`h-full flex-1 rounded-full transition-all duration-300 ${
                            passwordStrength.score >= 2 ? passwordStrength.color : "bg-transparent"
                          }`}
                        />
                        <div
                          className={`h-full flex-1 rounded-full transition-all duration-300 ${
                            passwordStrength.score >= 3 ? passwordStrength.color : "bg-transparent"
                          }`}
                        />
                      </div>
                    </div>
                  )}

                  {signUpErrors.password && (
                    <p className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {signUpErrors.password.message}
                    </p>
                  )}
                </div>

                {/* Confirm Password */}
                <div>
                  <label htmlFor="signup-confirm-password" className="block text-xs font-semibold text-slate-300 mb-1">
                    Confirm Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                      id="signup-confirm-password"
                      type={showSignUpConfirmPassword ? "text" : "password"}
                      placeholder="Repeat your password"
                      autoComplete="new-password"
                      aria-invalid={!!signUpErrors.confirmPassword}
                      aria-describedby={signUpErrors.confirmPassword ? "signup-confirm-error" : undefined}
                      {...registerSignUp("confirmPassword")}
                      className={`w-full glass-input rounded-xl pl-10 pr-10 py-2.5 text-xs text-white transition-all ${
                        signUpErrors.confirmPassword
                          ? "border-rose-500/80 focus:ring-rose-500/30 focus:border-rose-500"
                          : "border-white/10 focus:border-gold-500"
                      }`}
                    />
                    <button
                      type="button"
                      onClick={() => setShowSignUpConfirmPassword(!showSignUpConfirmPassword)}
                      className="absolute right-3 top-2.5 p-0.5 text-slate-400 hover:text-slate-200 transition-colors"
                      aria-label={showSignUpConfirmPassword ? "Hide password" : "Show password"}
                    >
                      {showSignUpConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {signUpErrors.confirmPassword && (
                    <p id="signup-confirm-error" className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {signUpErrors.confirmPassword.message}
                    </p>
                  )}
                </div>

                {/* Terms and Conditions Checkbox */}
                <div className="pt-1">
                  <div className="flex items-start gap-2">
                    <input
                      id="terms-accepted"
                      type="checkbox"
                      aria-invalid={!!signUpErrors.termsAccepted}
                      {...registerSignUp("termsAccepted")}
                      className="h-3.5 w-3.5 mt-0.5 rounded border-white/20 bg-navy-900 text-gold-500 focus:ring-gold-500/30 accent-gold-500"
                    />
                    <label htmlFor="terms-accepted" className="text-[11px] text-slate-300 leading-tight">
                      I agree to the{" "}
                      <a href="#" onClick={(e) => { e.preventDefault(); alert("WealthGuard Enterprise Terms of Service: Compliant banking advisory usage only."); }} className="text-gold-400 hover:underline">
                        Terms of Service
                      </a>{" "}
                      and{" "}
                      <a href="#" onClick={(e) => { e.preventDefault(); alert("WealthGuard Privacy Policy: Zero retention of prompt data beyond tenant compliance logs."); }} className="text-gold-400 hover:underline">
                        Privacy Policy
                      </a>
                    </label>
                  </div>
                  {signUpErrors.termsAccepted && (
                    <p className="text-[11px] text-rose-400 mt-1 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {signUpErrors.termsAccepted.message}
                    </p>
                  )}
                </div>

                {/* Primary CTA Button */}
                <button
                  type="submit"
                  disabled={isSignUpSubmitting}
                  className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-gold-500 to-gold-600 hover:from-gold-400 hover:to-gold-500 text-navy-950 font-bold text-xs tracking-wide shadow-lg shadow-gold-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                >
                  {isSignUpSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Creating Account...</span>
                    </>
                  ) : (
                    <>
                      <span>Create Account</span>
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>

              {/* Bottom Switcher */}
              <div className="text-center text-xs text-slate-400 pt-1">
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setActiveTab("signin");
                    setServerError(null);
                  }}
                  className="font-semibold text-gold-400 hover:text-gold-300 underline underline-offset-4"
                >
                  Sign In
                </button>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Shield, BookOpen, MessageSquare, ClipboardCheck, LogOut, Building2, UserCircle } from "lucide-react";

export interface NavbarProps {
  onOpenUpload?: () => void;
}

export function Navbar({ onOpenUpload }: NavbarProps = {}) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  if (!user) return null;

  const isCompliance = user.role === "ComplianceAdmin";

  const navLinks = [
    { href: "/", label: "Advisory Chat", icon: MessageSquare },
    { href: "/documents", label: "Document Store", icon: BookOpen },
    ...(isCompliance
      ? [{ href: "/audit", label: "Compliance Audit", icon: ClipboardCheck }]
      : []),
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-white/10 glass-panel bg-navy-950/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand & Branch */}
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-gold-400 to-gold-600 shadow-md shadow-gold-500/10">
              <Shield className="h-5 w-5 text-navy-950" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-white">WealthGuard AI</span>
              <span className="ml-1.5 rounded bg-gold-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-gold-400 border border-gold-500/20">
                ENTERPRISE
              </span>
            </div>
          </Link>

          {/* Tenant Branch Pill */}
          <div className="hidden md:flex items-center gap-1.5 rounded-full bg-navy-850 px-3 py-1 text-xs text-slate-300 border border-white/5">
            <Building2 className="h-3.5 w-3.5 text-gold-400" />
            <span className="font-medium truncate max-w-[200px]">
              {user.account?.branch_name || user.account_id}
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1">
          {navLinks.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-medium transition-all ${
                  isActive
                    ? "bg-gold-500/15 text-gold-400 border border-gold-500/30 shadow-sm"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-200"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Role & Logout */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex flex-col text-right">
            <span className="text-xs font-medium text-slate-200">{user.full_name}</span>
            <span className="text-[11px] text-slate-400">
              {isCompliance ? "Compliance Auditor" : "Relationship Manager"}
            </span>
          </div>

          <span
            className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
              isCompliance
                ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                : "bg-blue-500/15 text-blue-400 border border-blue-500/30"
            }`}
          >
            {user.role}
          </span>

          <button
            onClick={logout}
            title="Sign Out"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-slate-400 transition-colors hover:bg-rose-500/15 hover:text-rose-400 hover:border-rose-500/30"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;

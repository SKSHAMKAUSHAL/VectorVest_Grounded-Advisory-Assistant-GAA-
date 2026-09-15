import Link from "next/link";
import { Landmark } from "lucide-react";

import { cn } from "@/lib/utils";

export function Brand({ className }: { className?: string }) {
  return (
    <Link href="/" className={cn("flex items-center gap-2.5", className)}>
      <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
        <Landmark className="h-5 w-5" aria-hidden />
      </span>
      <span className="leading-tight">
        <span className="block text-sm font-bold tracking-tight">
          VectorVest
        </span>
        <span className="block text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Wealth Management · GAA
        </span>
      </span>
    </Link>
  );
}
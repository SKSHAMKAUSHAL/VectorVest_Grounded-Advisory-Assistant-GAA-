import { CalendarClock, ShieldAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";

export function ComplianceBanner() {
  return (
    <section className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8 lg:pb-28">
      <div className="flex flex-col gap-4 rounded-xl border bg-card p-6 sm:flex-row sm:items-center sm:justify-between sm:p-8">
        <div className="flex items-start gap-4">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-accent-foreground">
            <ShieldAlert className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <h3 className="font-semibold">
              Verify with Compliance for client-specific suitability.
            </h3>
            <p className="mt-1 max-w-2xl text-sm leading-relaxed text-muted-foreground">
              Answers are grounded in the current approved corpus and carry a
              mandatory disclaimer. This assistant answers policy, tax and
              product questions — it does not recommend what a specific client
              should buy.
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <Badge variant="secondary" className="gap-1.5 text-xs">
            <CalendarClock className="h-3.5 w-3.5" />
            Last indexed: today · 06:00 UTC
          </Badge>
        </div>
      </div>
    </section>
  );
}
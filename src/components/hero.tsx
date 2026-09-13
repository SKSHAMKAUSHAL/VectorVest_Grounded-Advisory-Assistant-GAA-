import {
  ArrowRight,
  CheckCircle,
  Clock3,
  Quote,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export function Hero() {
  return (
    <section className="relative overflow-hidden">
      <div
        className="pointer-events-none absolute inset-0 bg-grid [mask-image:radial-gradient(ellipse_at_top,black_35%,transparent_75%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-brand-glow"
        aria-hidden
      />

      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:px-8 lg:py-24">
        {/* Copy */}
        <div>
          <Badge variant="gold" className="gap-1.5">
            <Sparkles className="h-3.5 w-3.5" />
            Wealth Management Division · Pilot preview
          </Badge>

          <h1 className="mt-5 text-balance text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
            Advisory answers that are{" "}
            <span className="text-primary">grounded</span>, cited and current.
          </h1>

          <p className="mt-5 max-w-xl text-lg text-muted-foreground">
            Ask in plain language. Every answer cites the exact policy clause,
            tax circular or brochure — versioned and audited — so nothing you
            repeat to a client comes from memory.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Button size="lg" className="gap-2">
              Open the advisor
              <ArrowRight className="h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline">
              View sample Q&As
            </Button>
          </div>

          <ul className="mt-8 flex flex-col gap-2.5 text-sm text-muted-foreground sm:flex-row sm:gap-6">
            <li className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-primary" />
              Citations: document · version · clause
            </li>
            <li className="flex items-center gap-2">
              <Clock3 className="h-4 w-4 text-primary" />
              Answers in ≤ 2 minutes
            </li>
          </ul>
        </div>

        {/* Mock assistant panel */}
        <div className="mx-auto w-full max-w-lg">
          <Card className="overflow-hidden">
            <div className="flex items-center justify-between border-b bg-muted/40 px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
                </span>
                <span className="text-sm font-semibold">GAA Advisor</span>
                <span className="hidden text-xs text-muted-foreground sm:block">
                  Grounded to current corpus
                </span>
              </div>
              <Badge variant="secondary" className="text-[11px]">
                Indexed 06:00 UTC
              </Badge>
            </div>

            <CardContent className="flex flex-col gap-4 p-4">
              {/* User bubble */}
              <div className="ml-auto max-w-[85%] rounded-2xl rounded-tr-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                What tax treatment applies when an NRI client redeems units of
                a Large Cap fund?
              </div>

              {/* Assistant bubble with citations */}
              <div className="max-w-[92%] rounded-2xl rounded-tl-sm border bg-background px-4 py-3 text-sm">
                <p>
                  For a resident but{" "}
                  <span className="font-medium">not ordinarily resident</span>{" "}
                  individual, capital gains on redemption of mutual fund units
                  are taxed at the applicable slab — the same treatment as for
                  residents, under the current circular.
                </p>

                <div className="mt-3 flex flex-wrap gap-1.5">
                  <Badge variant="secondary" className="gap-1 text-[11px]">
                    <Quote className="h-3 w-3" />
                    Tax Circular 2024-18 · §4.2
                  </Badge>
                  <Badge variant="secondary" className="gap-1 text-[11px]">
                    <Quote className="h-3 w-3" />
                    Policy Manual v4.2 · §7.4
                  </Badge>
                </div>

                <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground">
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                  Grounding verified · 3 docs retrieved, superseded excluded
                </p>
              </div>

              {/* Follow-up input */}
              <div className="rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                Ask a follow-up — e.g. “and for NRIs in the US?”
              </div>

              <p className="text-center text-[11px] text-muted-foreground">
                Answers are advisory guidance only. Verify with Compliance for
                client-specific suitability.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
import { CheckCircle, Clock3, ScrollText, Users } from "lucide-react";

import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const KPIS = [
  {
    icon: CheckCircle,
    value: "≥ 90%",
    label: "Grounding audit pass",
    sub: "Answers cited to current-version sources",
  },
  {
    icon: Clock3,
    value: "≤ 2 min",
    label: "Query resolution",
    sub: "Down from 14-minute look-ups",
  },
  {
    icon: ScrollText,
    value: "≥ 98%",
    label: "Citation coverage",
    sub: "% of answers with a verifiable source",
  },
  {
    icon: Users,
    value: "60",
    label: "Relationship managers",
    sub: "Across 12 branches · internal pilot",
  },
];

export function KpiStats() {
  return (
    <section className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {KPIS.map(({ icon: Icon, value, label, sub }) => (
          <Card key={label} className="overflow-hidden">
            <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0 p-5">
              <div>
                <CardTitle className="font-mono text-3xl tracking-tight">
                  {value}
                </CardTitle>
                <p className="mt-1 text-sm font-medium">{label}</p>
                <CardDescription className="mt-1.5 leading-snug">
                  {sub}
                </CardDescription>
              </div>
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" aria-hidden />
              </span>
            </CardHeader>
          </Card>
        ))}
      </div>
    </section>
  );
}
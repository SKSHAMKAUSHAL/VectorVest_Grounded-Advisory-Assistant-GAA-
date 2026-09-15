import {
  Ban,
  Eye,
  FileText,
  MessagesSquare,
  ShieldAlert,
  Zap,
} from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const FEATURES = [
  {
    icon: FileText,
    title: "Grounded citations",
    body: "Every answer shows the source document, version and clause/section it was drawn from — ready to show the client or defend in an audit.",
  },
  {
    icon: ShieldAlert,
    title: "Explicit refusal",
    body: "When no grounding evidence is found, the assistant says so instead of speculating. No fabricated answers, ever.",
  },
  {
    icon: MessagesSquare,
    title: "Multi-turn context",
    body: "Ask follow-ups like “what about NRIs?” in the same conversation — no need to restate the full question.",
  },
  {
    icon: Ban,
    title: "Discontinued-product filter",
    body: "Archived and superseded documents are excluded from default retrieval, so a sunset product can’t resurface in an answer.",
  },
  {
    icon: Eye,
    title: "Compliance audit trail",
    body: "Each query, the retrieved chunks, the generated answer and a timestamp are logged for compliance officers.",
  },
  {
    icon: Zap,
    title: "Streamed in ≤ 2 minutes",
    body: "Answers stream with inline citations so you get what you need mid-call, not after the meeting.",
  },
];

export function FeatureGrid() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-28">
      <div className="max-w-2xl">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-primary">
          Scope · v1.0
        </p>
        <h2 className="mt-3 text-balance text-3xl font-bold tracking-tight sm:text-4xl">
          Built for the way relationship managers actually advise.
        </h2>
        <p className="mt-4 text-muted-foreground">
          Six capabilities from the sprint-two spec — each mapped to a user
          story in the product requirements document.
        </p>
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <Card key={title}>
            <CardHeader>
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" aria-hidden />
              </span>
              <CardTitle className="mt-4 text-lg">{title}</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="leading-relaxed">
                {body}
              </CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
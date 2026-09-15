import Link from "next/link";

import { Brand } from "@/components/brand";

const COLUMNS = [
  {
    title: "Product",
    links: ["Advisor", "Knowledge Base", "Compliance Audit", "Dashboard"],
  },
  {
    title: "Resources",
    links: ["Investment Policy Manual", "Tax Circulars", "Product Brochures", "Release notes"],
  },
  {
    title: "Support",
    links: ["Compliance helpdesk", "RM training", "Report an issue", "Access request"],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t bg-muted/30">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Brand />
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              Grounded Advisory Assistant — internal tooling for the Wealth
              Management division of VectorVest. Answers are cited, versioned
              and logged for compliance review.
            </p>
            <p className="mt-4 text-xs text-muted-foreground">
              Corpus: Policy Manual v4.2 · 90 tax circulars · 45 active
              brochures · v1 is English only, web only.
            </p>
          </div>

          {COLUMNS.map(({ title, links }) => (
            <div key={title}>
              <h4 className="text-sm font-semibold">{title}</h4>
              <ul className="mt-4 space-y-2.5">
                {links.map((label) => (
                  <li key={label}>
                    <Link
                      href="#"
                      className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col gap-3 border-t pt-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 VectorVest Wealth Management · Internal use only</p>
          <p>
            All advisory-related content is subject to regulatory sign-off
            ahead of the client-facing pilot.
          </p>
        </div>
      </div>
    </footer>
  );
}
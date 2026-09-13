# Grounded Advisory Assistant (GAA) — VectorVest Wealth Management

Frontend for the **Grounded Advisory Assistant**: an internal, RM-facing
retrieval-augmented assistant that answers investment policy, tax-rule and
product-brochure questions with grounded, cited, current-version answers.

## Stack

| Layer        | Choice                                              |
| ------------ | --------------------------------------------------- |
| Framework    | [Next.js 14](https://nextjs.org/) (App Router, 14.2.35) |
| Language     | TypeScript (strict)                                 |
| Styling      | Tailwind CSS 3.4                                    |
| UI kit       | [shadcn/ui](https://ui.shadcn.com) (default style, CSS variables, `@/*` alias) |
| Icons        | lucide-react                                        |
| Fonts        | Geist (bundled locally)                             |
| Package mgr  | npm                                                 |

## Theme — Wealth-Management "Midnight Navy"

A banking-flavoured theme defined entirely through Tailwind CSS variables in
`src/app/globals.css`:

- **Light mode** — cool paper background (`--background: 210 43% 98%`), deep
  navy primary (`--primary: 213 77% 14%`), pale mint secondary, gold accent
  (`--accent: 46 74% 52% `).
- **Dark mode** — "vault" palette: near-black navy surfaces, emerald primary,
  gold accents. Toggle by adding the `dark` class to `<html>` (Tailwind
  `darkMode: ["class"]` is already configured).
- Radius `0.75rem`, `Inter`-style Geist type scale, plus `bg-grid` and
  `bg-brand-glow` utility layers for the hero backdrop.

## Getting started

```bash
npm install        # install dependencies
npm run dev        # http://localhost:3000
npm run build      # production build (validates types + lint)
npm run start      # serve the production build
npm run lint       # ESLint (eslint-config-next)
```

## Project layout

```
components.json        # shadcn/ui configuration
tailwind.config.ts     # Tailwind + shadcn theme wiring (hsl CSS vars)
src/
  app/
    layout.tsx         # Root layout (metadata, Geist fonts)
    page.tsx           # Home — the banking-themed landing
    globals.css        # Theme tokens + base styles
  components/
    ui/                # shadcn/ui primitives (button, card, input, badge,
                       #  separator, tabs, avatar, dropdown-menu)
    brand.tsx          # “VectorVest · Wealth Management” wordmark
    site-header.tsx    # Sticky nav + RM user dropdown
    hero.tsx           # Hero + mock cited Q&A panel
    kpi-stats.tsx      # PRD KPI summary cards
    feature-grid.tsx   # v1.0 capability grid (cited, refusal, multi-turn…)
    compliance-banner.tsx
    site-footer.tsx
  lib/utils.ts         # cn() helper (clsx + tailwind-merge)
```

## Adding shadcn/ui components

The project uses the shadcn **default** style with CSS variables and a `src/`
directory (see `components.json`). Components live in `src/components/ui/`.

```bash
npx shadcn@2 add alert-dialog table  # fetches from the classic v2 registry
```

> Note: the scaffolding targets **Next.js 14 + Tailwind 3**, so use the
> `shadcn@2` CLI, not the Tailwind-4-only v3 CLI.

## Product notes (from `PRD.md`)

- v1 is **internal / RM-facing only**, web portal, English-only, batch
  re-indexing — no client-facing chat and no mobile app.
- Every answer must carry citations (document, version, clause) and refuse
  when evidence is insufficient.
- Compliance audit log (query, retrieved chunks, answer, timestamp) is a
  v1.0 requirement planned as a future route.

## Branch

Active work happens on `feat/frontend-init` toward the first PR.
import { ComplianceBanner } from "@/components/compliance-banner";
import { FeatureGrid } from "@/components/feature-grid";
import { Hero } from "@/components/hero";
import { KpiStats } from "@/components/kpi-stats";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <Hero />
        <KpiStats />
        <FeatureGrid />
        <ComplianceBanner />
      </main>
      <SiteFooter />
    </div>
  );
}

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function DashboardRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/");
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-navy-950 text-white">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-400"></div>
    </div>
  );
}

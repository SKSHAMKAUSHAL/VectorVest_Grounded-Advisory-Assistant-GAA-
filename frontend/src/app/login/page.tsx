import AuthModule from "@/components/AuthModule";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Advisor Authentication | WealthGuard AI",
  description: "Sign in to WealthGuard AI Grounded Advisory Assistant.",
};

export default function LoginPage() {
  return <AuthModule initialTab="signin" />;
}

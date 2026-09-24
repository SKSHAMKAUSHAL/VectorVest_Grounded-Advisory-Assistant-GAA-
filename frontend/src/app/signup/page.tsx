import AuthModule from "@/components/AuthModule";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Advisor Account | WealthGuard AI",
  description: "Register for WealthGuard AI Grounded Advisory Assistant.",
};

export default function SignUpPage() {
  return <AuthModule initialTab="signup" />;
}

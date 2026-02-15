import type { Metadata } from "next";
import { LoginPage } from "@/components/auth/LoginPage";

export const metadata: Metadata = {
  title: "Login",
  description:
    "Login or create your BusBook account with OTP verification. Book buses for group travel in Rajasthan.",
};

/**
 * Auth Login Page — /auth/login
 *
 * Phone+OTP authentication flow with inline registration for new users.
 * Replaces the Supabase email+password starter template.
 */
export default function Page() {
  return <LoginPage />;
}

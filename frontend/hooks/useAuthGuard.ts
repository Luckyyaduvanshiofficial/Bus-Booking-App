/**
 * Auth guard hook for protected routes.
 *
 * Redirects unauthenticated users to /auth/login.
 * Shows loading state while checking auth status.
 *
 * @param redirectTo - Where to redirect if not authenticated (default: /auth/login)
 * @returns { isLoading, isAuthenticated }
 *
 * @example
 * ```tsx
 * function DashboardPage() {
 *   const { isLoading } = useAuthGuard();
 *   if (isLoading) return <LoadingSkeleton />;
 *   return <Dashboard />;
 * }
 * ```
 */

"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

interface AuthGuardOptions {
  /** Where to redirect if not authenticated */
  redirectTo?: string;
  /** Required user role (optional) */
  requiredRole?: "customer" | "operator" | "admin";
}

export function useAuthGuard(options: AuthGuardOptions = {}) {
  const { redirectTo = "/auth/login", requiredRole } = options;
  const router = useRouter();
  const { isAuthenticated, isLoading, user } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated) {
      router.replace(redirectTo);
      return;
    }

    if (requiredRole && user?.role !== requiredRole) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, user, requiredRole, redirectTo, router]);

  return { isLoading, isAuthenticated, user };
}

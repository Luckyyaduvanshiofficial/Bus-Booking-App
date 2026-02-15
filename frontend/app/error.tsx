"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RefreshCw } from "lucide-react";

/**
 * Global error boundary — catches unhandled errors.
 * Shows branded, user-friendly error UI with retry option.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error in development
    if (process.env.NODE_ENV === "development") {
      console.error("Global error boundary caught:", error);
    }
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-50">
          <AlertTriangle className="h-8 w-8 text-red-500" />
        </div>
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">
            Something went wrong
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            We encountered an unexpected error. Please try again or go back to
            the homepage.
          </p>
        </div>
        <div className="flex gap-4">
          <button
            onClick={reset}
            className="flex items-center gap-2 rounded-xl bg-brand-orange px-6 py-3 text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.02] hover:bg-orange-600 focus:ring-2 focus:ring-orange-500 focus:outline-none"
            aria-label="Try again"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
          <Link
            href="/"
            className="flex items-center gap-2 rounded-xl border-2 border-slate-300 px-6 py-3 text-sm font-semibold text-slate-700 transition-all duration-300 hover:border-brand-blue hover:text-brand-blue focus:ring-2 focus:ring-orange-500 focus:outline-none"
            aria-label="Go to homepage"
          >
            Go Home
          </Link>
        </div>
      </div>
    </div>
  );
}

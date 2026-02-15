import type { ReactNode } from "react";

/**
 * Max-width container enforcing consistent horizontal padding.
 * Used as the standard content wrapper across all pages.
 */
export function MainContainer({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`mx-auto w-full max-w-7xl px-4 md:px-6 ${className}`}>
      {children}
    </div>
  );
}

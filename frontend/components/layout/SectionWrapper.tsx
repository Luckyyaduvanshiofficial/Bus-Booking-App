import type { ReactNode } from "react";

/**
 * Section wrapper enforcing py-16 minimum spacing between sections.
 * Ensures consistent vertical rhythm on all pages.
 */
export function SectionWrapper({
  children,
  className = "",
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <section id={id} className={`py-16 ${className}`}>
      {children}
    </section>
  );
}

"use client";

import { memo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Search, CalendarDays, User } from "lucide-react";

const MOBILE_TABS = [
  { href: "/", icon: Home, label: "Home" },
  { href: "/search", icon: Search, label: "Search" },
  { href: "/bookings", icon: CalendarDays, label: "Bookings" },
  { href: "/profile", icon: User, label: "Profile" },
] as const;

/**
 * Fixed bottom navigation for mobile users.
 * Shows only on screens < md breakpoint.
 */
export const MobileNav = memo(function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-50 border-t border-slate-200 bg-white md:hidden"
      aria-label="Mobile navigation"
    >
      <div className="flex h-16 items-center justify-around">
        {MOBILE_TABS.map((tab) => {
          const isActive =
            tab.href === "/"
              ? pathname === "/"
              : pathname.startsWith(tab.href);
          const Icon = tab.icon;

          return (
            <Link
              key={tab.href}
              href={tab.href}
              className={`flex flex-col items-center gap-1 px-4 py-2 text-xs transition-colors duration-300 ${
                isActive
                  ? "font-semibold text-brand-orange"
                  : "text-slate-400 hover:text-slate-600"
              }`}
              aria-label={tab.label}
              aria-current={isActive ? "page" : undefined}
            >
              <Icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
});

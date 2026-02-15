"use client";

import { memo, useState, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Menu,
  X,
  Bus,
  User,
  LogOut,
  LayoutDashboard,
  Bell,
  ChevronDown,
} from "lucide-react";
import { NAV_LINKS } from "@/lib/constants";
import { useAuth } from "@/hooks/useAuth";

/**
 * Primary site header — sticky white navigation bar.
 *
 * Left: Brand logo + name
 * Center: Navigation links (desktop)
 * Right: Auth button + "List Your Bus" CTA (or logged-in user menu)
 */
export const Header = memo(function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const { isAuthenticated, user, signOut } = useAuth();
  const router = useRouter();

  const handleSignOut = useCallback(() => {
    signOut();
    setIsProfileOpen(false);
    setIsMobileMenuOpen(false);
    router.push("/");
  }, [signOut, router]);

  const closeMobileMenu = useCallback(() => {
    setIsMobileMenuOpen(false);
  }, []);

  const dashboardLink =
    user?.role === "operator" ? "/operator/dashboard" : "/dashboard";

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur-sm">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 md:px-6">
        {/* ── Logo ──────────────────────────────────── */}
        <Link
          href="/"
          className="flex items-center gap-2 transition-opacity duration-300 hover:opacity-80"
          aria-label="BusBook Home"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-blue">
            <Bus className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold text-brand-blue">
            Bus<span className="text-brand-orange">Book</span>
          </span>
        </Link>

        {/* ── Desktop Nav Links ─────────────────────── */}
        <div className="hidden items-center gap-8 md:flex">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-slate-600 transition-colors duration-300 hover:text-brand-blue"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* ── Desktop Right Actions ─────────────────── */}
        <div className="hidden items-center gap-4 md:flex">
          <Link
            href="/operator/register"
            className="rounded-xl border-2 border-brand-blue px-4 py-2 text-sm font-semibold text-brand-blue transition-all duration-300 hover:bg-brand-blue hover:text-white focus:ring-2 focus:ring-orange-500 focus:outline-none"
            aria-label="List your bus on BusBook"
          >
            List Your Bus
          </Link>

          {isAuthenticated && user ? (
            <div className="relative">
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center gap-2 rounded-xl bg-slate-100 px-3 py-2 text-sm font-medium text-slate-700 transition-colors duration-300 hover:bg-slate-200"
                aria-label="Open user menu"
                aria-expanded={isProfileOpen}
              >
                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-blue text-xs font-bold text-white">
                  {user.name?.[0]?.toUpperCase() ?? "U"}
                </div>
                <span className="max-w-[120px] truncate">
                  {user.name || "User"}
                </span>
                <ChevronDown className="h-3.5 w-3.5" />
              </button>

              {/* ── Profile Dropdown ───────────────── */}
              {isProfileOpen && (
                <>
                  {/* Backdrop to close dropdown */}
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsProfileOpen(false)}
                    aria-hidden="true"
                  />
                  <div className="absolute right-0 z-50 mt-2 w-56 rounded-xl border border-slate-200 bg-white py-2 shadow-lg">
                    <div className="border-b border-slate-100 px-4 py-2">
                      <p className="text-sm font-medium text-slate-900 truncate">
                        {user.name || "User"}
                      </p>
                      <p className="text-xs text-slate-500 truncate">
                        +91 {user.phone?.replace(/^\+?91/, "")}
                      </p>
                    </div>
                    <Link
                      href={dashboardLink}
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      <LayoutDashboard className="h-4 w-4 text-slate-400" />
                      Dashboard
                    </Link>
                    <Link
                      href="/dashboard/notifications"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      <Bell className="h-4 w-4 text-slate-400" />
                      Notifications
                    </Link>
                    <Link
                      href="/dashboard/profile"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-2.5 px-4 py-2.5 text-sm text-slate-700 hover:bg-slate-50"
                    >
                      <User className="h-4 w-4 text-slate-400" />
                      Profile
                    </Link>
                    <hr className="my-1 border-slate-100" />
                    <button
                      onClick={handleSignOut}
                      className="flex w-full items-center gap-2.5 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50"
                      aria-label="Sign out of your account"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : (
            <Link
              href="/auth/login"
              className="flex items-center gap-2 rounded-xl bg-brand-orange px-4 py-2 text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.02] hover:bg-orange-600 focus:ring-2 focus:ring-orange-500 focus:outline-none"
              aria-label="Log in to your account"
            >
              <User className="h-4 w-4" />
              Login
            </Link>
          )}
        </div>

        {/* ── Mobile Hamburger ──────────────────────── */}
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-700 transition-colors duration-300 hover:bg-slate-100 md:hidden"
          aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          aria-expanded={isMobileMenuOpen}
        >
          {isMobileMenuOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </nav>

      {/* ── Mobile Menu Dropdown ────────────────────── */}
      {isMobileMenuOpen && (
        <div className="border-t border-slate-200 bg-white px-4 py-4 md:hidden">
          <div className="flex flex-col gap-2">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={closeMobileMenu}
                className="rounded-xl px-4 py-3 text-sm font-medium text-slate-700 transition-colors duration-300 hover:bg-slate-50"
              >
                {link.label}
              </Link>
            ))}
            <hr className="my-2 border-slate-200" />

            {isAuthenticated && user ? (
              <>
                {/* Logged-in user info */}
                <div className="flex items-center gap-3 px-4 py-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-blue text-sm font-bold text-white">
                    {user.name?.[0]?.toUpperCase() ?? "U"}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">
                      {user.name || "User"}
                    </p>
                    <p className="text-xs text-slate-500">
                      +91 {user.phone?.replace(/^\+?91/, "")}
                    </p>
                  </div>
                </div>
                <Link
                  href={dashboardLink}
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Dashboard
                </Link>
                <Link
                  href="/dashboard/profile"
                  onClick={closeMobileMenu}
                  className="rounded-xl px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Profile
                </Link>
                <button
                  onClick={handleSignOut}
                  className="rounded-xl px-4 py-3 text-left text-sm font-medium text-red-600 hover:bg-red-50"
                  aria-label="Sign out"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/operator/register"
                  onClick={closeMobileMenu}
                  className="rounded-xl border-2 border-brand-blue px-4 py-3 text-center text-sm font-semibold text-brand-blue transition-all duration-300 hover:bg-brand-blue hover:text-white"
                  aria-label="List your bus on BusBook"
                >
                  List Your Bus
                </Link>
                <Link
                  href="/auth/login"
                  onClick={closeMobileMenu}
                  className="rounded-xl bg-brand-orange px-4 py-3 text-center text-sm font-semibold text-white transition-all duration-300 hover:bg-orange-600"
                  aria-label="Log in to your account"
                >
                  Login
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
});

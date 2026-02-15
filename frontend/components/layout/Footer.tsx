import Link from "next/link";
import { Bus, Mail, Phone, MapPin } from "lucide-react";
import { NAV_LINKS, POPULAR_ROUTES } from "@/lib/constants";

/**
 * Site footer with multi-column layout.
 * Brand blue text on #F8FAFC background.
 */
export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-16 md:px-6">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {/* ── Brand Column ─────────────────────────── */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2" aria-label="BusBook Home">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-blue">
                <Bus className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-bold text-brand-blue">
                Bus<span className="text-brand-orange">Book</span>
              </span>
            </Link>
            <p className="mt-4 text-sm leading-relaxed text-slate-500">
              Rajasthan&apos;s trusted platform for booking buses, tempo
              travellers, and luxury coaches for group travel.
            </p>
            <div className="mt-4 flex flex-col gap-2">
              <a
                href="mailto:support@busbook.in"
                className="flex items-center gap-2 text-sm text-slate-500 transition-colors hover:text-brand-blue"
              >
                <Mail className="h-4 w-4" />
                support@busbook.in
              </a>
              <a
                href="tel:+919829012345"
                className="flex items-center gap-2 text-sm text-slate-500 transition-colors hover:text-brand-blue"
              >
                <Phone className="h-4 w-4" />
                +91 98290 12345
              </a>
            </div>
          </div>

          {/* ── Company Links ────────────────────────── */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900">Company</h3>
            <ul className="mt-4 flex flex-col gap-2">
              {[
                { href: "/about", label: "About Us" },
                { href: "/contact", label: "Contact" },
                { href: "/terms", label: "Terms of Service" },
                { href: "/privacy", label: "Privacy Policy" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-500 transition-colors hover:text-brand-blue"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* ── For Operators ────────────────────────── */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900">
              For Operators
            </h3>
            <ul className="mt-4 flex flex-col gap-2">
              {[
                { href: "/operator/register", label: "Register as Operator" },
                { href: "/operator/dashboard", label: "Operator Dashboard" },
                { href: "/operator/documents", label: "Document Upload" },
                { href: "/operator/earnings", label: "Earnings & Payouts" },
              ].map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-500 transition-colors hover:text-brand-blue"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* ── Popular Routes ───────────────────────── */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900">
              Popular Routes
            </h3>
            <ul className="mt-4 flex flex-col gap-2">
              {POPULAR_ROUTES.slice(0, 5).map((route) => (
                <li key={`${route.from}-${route.to}`}>
                  <Link
                    href={`/search?from=${route.from.toLowerCase()}&to=${route.to.toLowerCase()}`}
                    className="flex items-center gap-1 text-sm text-slate-500 transition-colors hover:text-brand-blue"
                  >
                    <MapPin className="h-3 w-3 shrink-0" />
                    {route.from} → {route.to}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* ── Bottom Bar ─────────────────────────────── */}
        <div className="mt-12 border-t border-slate-200 pt-8">
          <p className="text-center text-xs text-slate-400">
            © {new Date().getFullYear()} BusBook. All rights reserved. Made with
            ❤️ in Jaipur, Rajasthan.
          </p>
        </div>
      </div>
    </footer>
  );
}

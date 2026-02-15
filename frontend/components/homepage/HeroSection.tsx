import { SearchForm } from "@/components/search/SearchForm";
import { Shield, CreditCard, Star, Headphones } from "lucide-react";

/**
 * Homepage hero section - gradient background with centered search card.
 */
export function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-orange-50 py-16 md:py-24">
      {/* Decorative background elements */}
      <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -top-24 -right-24 h-96 w-96 rounded-full bg-orange-100/40 blur-3xl" />
        <div className="absolute -bottom-32 -left-32 h-96 w-96 rounded-full bg-blue-100/40 blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-7xl px-4 md:px-6">
        <div className="flex flex-col items-center text-center">
          {/* ── Badge ─────────────────────────────── */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-4 py-1.5">
            <span className="text-xs font-semibold text-brand-blue">
              🚌 Rajasthan&apos;s #1 Bus Booking Platform
            </span>
          </div>

          {/* ── Headline ──────────────────────────── */}
          <h1 className="max-w-4xl text-4xl font-bold leading-tight text-slate-900 md:text-5xl lg:text-6xl">
            Book Buses for{" "}
            <span className="text-brand-orange">Group Travel</span>{" "}
            in Rajasthan
          </h1>

          {/* ── Subheadline ───────────────────────── */}
          <p className="mt-6 max-w-2xl text-lg text-slate-500">
            Weddings, family trips, pilgrimages, and corporate events.
            Verified operators, transparent pricing, and secure payments.
          </p>

          {/* ── Trust badges row ──────────────────── */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-500">
            <div className="flex items-center gap-1.5">
              <Shield className="h-4 w-4 text-brand-blue" />
              <span>Verified Operators</span>
            </div>
            <div className="flex items-center gap-1.5">
              <CreditCard className="h-4 w-4 text-brand-blue" />
              <span>Secure Payments</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Star className="h-4 w-4 text-brand-gold" />
              <span>4.8/5 Avg Rating</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Headphones className="h-4 w-4 text-brand-blue" />
              <span>24/7 Support</span>
            </div>
          </div>

          {/* ── Search Card ───────────────────────── */}
          <div className="mt-12 w-full max-w-4xl">
            <SearchForm />
          </div>
        </div>
      </div>
    </section>
  );
}

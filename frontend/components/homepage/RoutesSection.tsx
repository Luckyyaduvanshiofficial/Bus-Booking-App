import Link from "next/link";
import { MainContainer } from "@/components/layout/MainContainer";
import { SectionWrapper } from "@/components/layout/SectionWrapper";
import { POPULAR_ROUTES } from "@/lib/constants";
import { MapPin, ArrowRight, Navigation } from "lucide-react";

/**
 * Popular Routes section — route cards with estimated pricing.
 *
 * Uses POPULAR_ROUTES constant data (Rajasthan routes from Jaipur).
 * Clicking a route pre-fills the search page.
 */
export function RoutesSection() {
  return (
    <SectionWrapper className="bg-white">
      <MainContainer>
        <div className="flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900 md:text-3xl">
              Popular <span className="text-brand-orange">Routes</span>
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              Most-booked group travel destinations from Jaipur
            </p>
          </div>
          <Link
            href="/search"
            className="hidden items-center gap-1 text-sm font-semibold text-brand-blue transition-colors hover:text-brand-orange md:flex"
          >
            View All Routes
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        <div className="mt-8 grid grid-cols-2 gap-4 md:grid-cols-3 lg:gap-6">
          {POPULAR_ROUTES.map((route) => (
            <Link
              key={`${route.from}-${route.to}`}
              href={`/search?from=${route.from.toLowerCase()}&to=${route.to.toLowerCase()}`}
              className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md"
            >
              {/* Route visual header */}
              <div className="flex h-28 items-center justify-center rounded-xl bg-gradient-to-br from-blue-50 to-orange-50 md:h-32">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-sm">
                    <MapPin className="h-5 w-5 text-brand-blue" />
                  </div>
                  <div className="flex flex-col items-center">
                    <div className="h-px w-8 bg-slate-300" />
                    <Navigation className="my-1 h-3 w-3 rotate-90 text-brand-orange" />
                    <div className="h-px w-8 bg-slate-300" />
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-sm">
                    <MapPin className="h-5 w-5 text-brand-orange" />
                  </div>
                </div>
              </div>

              {/* Route info */}
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-slate-900 md:text-base">
                  {route.from} → {route.to}
                </h3>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-xs text-slate-400">
                    {route.distance}
                  </span>
                  <span className="text-sm font-bold text-brand-orange">
                    {route.estimatedPrice}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Mobile "View All" link */}
        <div className="mt-6 text-center md:hidden">
          <Link
            href="/search"
            className="inline-flex items-center gap-1 text-sm font-semibold text-brand-blue hover:text-brand-orange"
          >
            View All Routes
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </MainContainer>
    </SectionWrapper>
  );
}

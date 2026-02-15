import Link from "next/link";
import { MainContainer } from "@/components/layout/MainContainer";
import { SectionWrapper } from "@/components/layout/SectionWrapper";
import { Bus, ArrowRight, TrendingUp, Users, IndianRupee } from "lucide-react";

/**
 * Operator CTA section — conversion banner for bus operators.
 * "List your bus on BusBook and grow your business."
 */
export function OperatorCTASection() {
  return (
    <SectionWrapper className="bg-brand-blue">
      <MainContainer>
        <div className="flex flex-col items-center gap-8 md:flex-row md:justify-between">
          {/* ── Left: Content ──────────────────────── */}
          <div className="text-center md:text-left">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5">
              <Bus className="h-4 w-4 text-brand-orange" />
              <span className="text-xs font-semibold text-white/90">
                For Bus Operators
              </span>
            </div>
            <h2 className="mt-4 text-2xl font-bold text-white md:text-3xl">
              Grow Your Business with{" "}
              <span className="text-brand-orange">BusBook</span>
            </h2>
            <p className="mt-4 max-w-lg text-sm leading-relaxed text-white/70">
              List your buses, receive bookings from verified customers, and get
              timely payouts. Join hundreds of operators already earning more
              with BusBook.
            </p>

            {/* ── Stats ────────────────────────────── */}
            <div className="mt-6 flex flex-wrap justify-center gap-6 md:justify-start">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-brand-gold" />
                <div>
                  <p className="text-lg font-bold text-white">500+</p>
                  <p className="text-xs text-white/50">Bookings / month</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Users className="h-5 w-5 text-brand-gold" />
                <div>
                  <p className="text-lg font-bold text-white">150+</p>
                  <p className="text-xs text-white/50">Verified Operators</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <IndianRupee className="h-5 w-5 text-brand-gold" />
                <div>
                  <p className="text-lg font-bold text-white">₹2Cr+</p>
                  <p className="text-xs text-white/50">Paid to Operators</p>
                </div>
              </div>
            </div>

            <Link
              href="/operator/register"
              className="mt-8 inline-flex items-center gap-2 rounded-xl bg-brand-orange px-8 py-4 text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.02] hover:bg-orange-600 focus:ring-2 focus:ring-white focus:outline-none"
              aria-label="Register as a bus operator"
            >
              List Your Bus — It&apos;s Free
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {/* ── Right: Visual element ──────────────── */}
          <div className="hidden w-80 shrink-0 md:block">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
              <div className="space-y-4">
                <div className="flex items-center justify-between rounded-xl bg-white/10 px-4 py-3">
                  <span className="text-sm text-white/80">Today&apos;s Earnings</span>
                  <span className="text-lg font-bold text-brand-gold">
                    ₹24,500
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-white/10 px-4 py-3">
                  <span className="text-sm text-white/80">Active Bookings</span>
                  <span className="text-lg font-bold text-white">12</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-white/10 px-4 py-3">
                  <span className="text-sm text-white/80">Your Rating</span>
                  <span className="text-lg font-bold text-brand-gold">
                    ⭐ 4.8
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </MainContainer>
    </SectionWrapper>
  );
}

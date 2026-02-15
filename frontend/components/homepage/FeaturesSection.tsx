"use client";

import { memo } from "react";
import { MainContainer } from "@/components/layout/MainContainer";
import { SectionWrapper } from "@/components/layout/SectionWrapper";
import {
  ShieldCheck,
  Wallet,
  BadgeCheck,
  Clock,
} from "lucide-react";

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "Verified Operators",
    description:
      "Every operator is background-checked with verified documents, insurance, and permits before listing.",
    color: "bg-blue-50 text-brand-blue",
  },
  {
    icon: Wallet,
    title: "Secure Payments",
    description:
      "Pay online via UPI, cards, or net banking. All transactions are encrypted and PCI-compliant.",
    color: "bg-orange-50 text-brand-orange",
  },
  {
    icon: BadgeCheck,
    title: "Best Prices",
    description:
      "Transparent pricing with no hidden charges. Compare operators and choose the best deal for your trip.",
    color: "bg-green-50 text-green-600",
  },
  {
    icon: Clock,
    title: "Instant Booking",
    description:
      "Book your bus in under 2 minutes. Get instant confirmation and operator details on your phone.",
    color: "bg-purple-50 text-purple-600",
  },
] as const;

/**
 * Features section — 4 trust-building cards with icons.
 */
export const FeaturesSection = memo(function FeaturesSection() {
  return (
    <SectionWrapper className="bg-white">
      <MainContainer>
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-slate-900 md:text-3xl">
            Why Choose <span className="text-brand-orange">BusBook</span>?
          </h2>
          <p className="mt-4 text-sm text-slate-500">
            Trusted by thousands of travellers across Rajasthan
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div
                  className={`flex h-12 w-12 items-center justify-center rounded-xl ${feature.color}`}
                >
                  <Icon className="h-6 w-6" />
                </div>
                <h3 className="mt-4 text-lg font-semibold text-slate-900">
                  {feature.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </MainContainer>
    </SectionWrapper>
  );
});

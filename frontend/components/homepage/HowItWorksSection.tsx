import { MainContainer } from "@/components/layout/MainContainer";
import { SectionWrapper } from "@/components/layout/SectionWrapper";
import { Search, CalendarCheck, Bus } from "lucide-react";

const STEPS = [
  {
    icon: Search,
    step: "01",
    title: "Search Your Route",
    description:
      "Enter your pickup, destination, travel date, and group size. We'll show you the best available buses.",
  },
  {
    icon: CalendarCheck,
    step: "02",
    title: "Book & Pay Securely",
    description:
      "Choose your bus, review pricing, and pay online or via advance booking. Instant confirmation on your phone.",
  },
  {
    icon: Bus,
    step: "03",
    title: "Enjoy Your Trip",
    description:
      "Your verified operator arrives on time. Sit back, relax, and enjoy the journey with your group.",
  },
] as const;

/**
 * How It Works section — 3-step visual flow.
 */
export function HowItWorksSection() {
  return (
    <SectionWrapper className="bg-gradient-to-b from-slate-50 to-white">
      <MainContainer>
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-slate-900 md:text-3xl">
            How It <span className="text-brand-blue">Works</span>
          </h2>
          <p className="mt-4 text-sm text-slate-500">
            Book your group bus in 3 simple steps
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-8 md:grid-cols-3">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={step.step} className="relative flex flex-col items-center text-center">
                {/* Connector line (desktop only) */}
                {index < STEPS.length - 1 && (
                  <div
                    className="absolute right-0 top-8 hidden h-px w-full translate-x-1/2 bg-slate-200 md:block"
                    aria-hidden="true"
                  />
                )}
                {/* Step number */}
                <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-blue shadow-md">
                  <Icon className="h-7 w-7 text-white" />
                  <span className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-brand-orange text-xs font-bold text-white">
                    {step.step}
                  </span>
                </div>
                <h3 className="mt-6 text-lg font-semibold text-slate-900">
                  {step.title}
                </h3>
                <p className="mt-2 max-w-xs text-sm leading-relaxed text-slate-500">
                  {step.description}
                </p>
              </div>
            );
          })}
        </div>
      </MainContainer>
    </SectionWrapper>
  );
}

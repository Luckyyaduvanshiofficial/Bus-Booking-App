import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { MobileNav } from "@/components/layout/MobileNav";
import { HeroSection } from "@/components/homepage/HeroSection";
import { FeaturesSection } from "@/components/homepage/FeaturesSection";
import { HowItWorksSection } from "@/components/homepage/HowItWorksSection";
import { RoutesSection } from "@/components/homepage/RoutesSection";
import { TestimonialsSection } from "@/components/homepage/TestimonialsSection";
import { OperatorCTASection } from "@/components/homepage/OperatorCTASection";

/**
 * Homepage — BusBook Landing Page
 *
 * MakeMyTrip-inspired premium landing page with:
 * - Hero section with search card
 * - Trust-building features
 * - How it works flow
 * - Popular Rajasthan routes
 * - Customer testimonials
 * - Operator conversion CTA
 *
 * SEO: Proper H1, semantic sections, JSON-LD schema.
 */
export default function Home() {
  return (
    <>
      <Header />
      <main className="pb-16 md:pb-0">
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <RoutesSection />
        <TestimonialsSection />
        <OperatorCTASection />
      </main>
      <Footer />
      <MobileNav />

      {/* JSON-LD Organization Schema */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Organization",
            name: "BusBook",
            description:
              "Rajasthan's trusted bus booking platform for group travel — weddings, family trips, pilgrimages.",
            url: "https://busbook.in",
            logo: "https://busbook.in/logo.png",
            sameAs: [],
            address: {
              "@type": "PostalAddress",
              addressLocality: "Jaipur",
              addressRegion: "Rajasthan",
              addressCountry: "IN",
            },
            contactPoint: {
              "@type": "ContactPoint",
              telephone: "+91-98290-12345",
              contactType: "customer service",
              availableLanguage: ["English", "Hindi"],
            },
          }),
        }}
      />
    </>
  );
}

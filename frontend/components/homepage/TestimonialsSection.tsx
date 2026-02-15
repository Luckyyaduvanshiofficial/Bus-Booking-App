"use client";

import { memo } from "react";
import { MainContainer } from "@/components/layout/MainContainer";
import { SectionWrapper } from "@/components/layout/SectionWrapper";
import { Star, Quote } from "lucide-react";

const TESTIMONIALS = [
  {
    name: "Rajesh Sharma",
    location: "Jaipur",
    rating: 5,
    text: "Booked a 40-seater for my daughter's wedding. The bus was spotless, driver was punctual, and the whole experience was seamless. Highly recommend!",
    trip: "Jaipur → Udaipur",
  },
  {
    name: "Priya Agarwal",
    location: "Jodhpur",
    rating: 5,
    text: "We needed a tempo traveller for a family pilgrimage to Pushkar. BusBook made it so easy — verified operator, fair price, and great communication.",
    trip: "Jodhpur → Pushkar",
  },
  {
    name: "Amit Gupta",
    location: "Jaipur",
    rating: 4,
    text: "Used BusBook for a corporate offsite to Jaisalmer. The luxury coach was excellent. Will definitely use again for our next team outing.",
    trip: "Jaipur → Jaisalmer",
  },
] as const;

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5" aria-label={`${rating} out of 5 stars`}>
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={`h-4 w-4 ${
            i < rating
              ? "fill-brand-gold text-brand-gold"
              : "text-slate-200"
          }`}
        />
      ))}
    </div>
  );
}

/**
 * Testimonials section — customer reviews with gold star ratings.
 */
export const TestimonialsSection = memo(function TestimonialsSection() {
  return (
    <SectionWrapper className="bg-gradient-to-b from-white to-slate-50">
      <MainContainer>
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-slate-900 md:text-3xl">
            What Our <span className="text-brand-blue">Travellers</span> Say
          </h2>
          <p className="mt-4 text-sm text-slate-500">
            Real reviews from real customers across Rajasthan
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 md:grid-cols-3">
          {TESTIMONIALS.map((testimonial, index) => (
            <div
              key={testimonial.name}
              className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-md"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Quote icon */}
              <Quote className="h-8 w-8 text-blue-100" />

              {/* Review text */}
              <p className="mt-4 text-sm leading-relaxed text-slate-600">
                &ldquo;{testimonial.text}&rdquo;
              </p>

              {/* Rating */}
              <div className="mt-4">
                <StarRating rating={testimonial.rating} />
              </div>

              {/* Author */}
              <div className="mt-4 flex items-center gap-3 border-t border-slate-100 pt-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-blue text-sm font-bold text-white">
                  {testimonial.name[0]}
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {testimonial.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {testimonial.trip} • {testimonial.location}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </MainContainer>
    </SectionWrapper>
  );
});

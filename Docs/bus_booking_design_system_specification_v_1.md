# 🚌 Bus Booking Platform — Design System Specification (Production v1.0)

This document defines the OFFICIAL frontend design system, implementation constraints, SEO layer, performance requirements, and strict AI enforcement rules.

This is a production-grade specification.
Not a template guideline.
Not optional.

---

# 1️⃣ PRODUCT FOUNDATION

## Platform Type
- Two-sided travel marketplace
- Customer + Operator + Admin roles
- Rajasthan-first regional focus
- Mobile-first usage expectation

## Technical Stack
- Next.js 14 (App Router)
- TypeScript (strict mode)
- Tailwind CSS
- shadcn/ui (customized)
- React Hook Form + Zod
- React Query (server state)
- Zustand (auth only)
- Framer Motion
- Supabase (session layer)
- Django REST API backend

---

# 2️⃣ CORE BRAND SYSTEM

## Brand Identity
Theme Direction: "Modern Indian Travel"

Design must communicate:
- Trust
- Warmth
- Reliability
- Clean professionalism
- Payment safety

Must NOT resemble:
- Crypto dashboards
- Neon AI tools
- Generic Tailwind clones
- Glassmorphism playground

---

# 3️⃣ COLOR SYSTEM (MANDATORY TOKENS)

Primary (Trust Blue): #0B3C5D
Accent (Travel Orange): #FF6B00
Gold (Ratings/Verified): #FFC145
Background: #F8FAFC
Card Surface: #FFFFFF

Neutral Scale:
- slate-900
- slate-700
- slate-500
- slate-300

## Enforcement
- No random Tailwind colors.
- No pure black (#000).
- No pure white page backgrounds.

---

# 4️⃣ DESIGN TOKENS

## Border Radius
- Buttons → rounded-xl
- Cards → rounded-2xl
- Inputs → rounded-lg
- Modals → rounded-3xl
- Search container → rounded-full

## Spacing (8px Grid Only)
Allowed: 2 / 4 / 6 / 8 / 12
Sections: py-16 minimum

Forbidden:
- Arbitrary spacing values

## Shadows
- Card → shadow-sm hover:shadow-md
- Feature → shadow-md hover:shadow-lg
- Modal → shadow-2xl
- Dropdown → shadow-lg

---

# 5️⃣ TYPOGRAPHY SYSTEM

Font: Inter (primary) or Geist (alternative)

Hierarchy:
- Hero → text-4xl md:text-5xl font-bold
- Section → text-2xl font-semibold
- Card Title → text-lg font-semibold
- Body → text-sm text-slate-600
- Caption → text-xs text-slate-400

No arbitrary font sizes allowed.

---

# 6️⃣ COMPONENT-LEVEL IMPLEMENTATION GUIDELINES

## Button
- Height ≥ h-12
- rounded-xl
- Primary: Orange background
- Secondary: Blue border variant
- Must include focus:ring
- Must include hover scale animation

## Card
- rounded-2xl
- border-slate-200
- hover lift (-translate-y-1)
- transition-all duration-300

## BusCard
Must include:
- Image gallery
- Operator verified badge (blue)
- Gold star rating
- Amenities icons
- Price highlighted in orange
- Primary CTA button
- Hover animation

## Search Bar
- Segmented layout
- rounded-full container
- Strong elevation
- Above the fold

## Booking Flow
- Step progress indicator
- Secure payment badge
- Clear price breakdown
- Validation feedback

---

# 7️⃣ SEO SPECIFICATION

## Metadata
- Use Next.js metadata API
- Dynamic titles per route
- Descriptive meta descriptions
- Canonical URLs

## Structured Data
- JSON-LD for bus listings
- Organization schema
- Breadcrumb schema

## Semantic HTML
- Proper heading order (H1 → H2 → H3)
- Accessible labels
- Alt text mandatory

## URL Strategy
- /search?from=jaipur&to=udaipur
- SEO-friendly route generation for popular routes

---

# 8️⃣ PERFORMANCE REQUIREMENTS

## Rendering Strategy
- Server Components by default
- Client components only for interactivity

## Loading
- Skeleton loaders required
- No blank screens

## Images
- next/image mandatory
- Lazy loading default
- Proper sizes attribute

## Code Splitting
- Dynamic import heavy components

## Bundle Discipline
- No unused shadcn components
- No heavy UI libraries

---

# 9️⃣ ACCESSIBILITY (WCAG AA)

- Color contrast ≥ 4.5:1
- Keyboard accessible
- Focus visible
- Proper aria attributes

---

# 🔟 STATE & DATA RULES

- Server data → React Query
- Auth → Zustand
- UI state → Local component state
- Never duplicate server state in global store

---

# 1️⃣1️⃣ SECURITY RULES

- No secrets in frontend
- Payments verified server-side
- Error messages sanitized
- Supabase session stored securely

---

# 1️⃣2️⃣ AI AGENT ENFORCEMENT RULES

AI must NOT:
- Use random Tailwind colors
- Break spacing grid
- Add unapproved gradients
- Modify config files without explicit instruction
- Introduce new state libraries

AI must ALWAYS:
- Follow design tokens
- Add loading states
- Add error handling
- Maintain strict TypeScript typing
- Maintain responsive layouts

---

# 1️⃣3️⃣ PRODUCTION READINESS CHECKLIST

Before deployment:

- npm run build passes
- No TypeScript errors
- No ESLint errors
- Lighthouse score ≥ 90
- All routes responsive
- Payment flow validated
- Error states tested
- SEO metadata validated

---

# 🎯 FINAL OBJECTIVE

Deliver a frontend that:
- Feels like a funded startup product
- Matches backend architecture
- Looks trustworthy and premium
- Scales without design inconsistency

This specification is authoritative.
All implementation must comply.


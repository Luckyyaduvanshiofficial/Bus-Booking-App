import { SkeletonCard } from "@/components/skeletons/SkeletonCard";

/**
 * Global loading fallback — shows skeleton grid while page loads.
 */
export default function Loading() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-16 md:px-6">
      {/* Hero skeleton */}
      <div className="flex flex-col items-center gap-8">
        <div className="h-12 w-2/3 animate-pulse rounded-xl bg-slate-200" />
        <div className="h-6 w-1/2 animate-pulse rounded-xl bg-slate-200" />
        <div className="h-16 w-full max-w-3xl animate-pulse rounded-full bg-slate-200" />
      </div>
      {/* Card grid skeleton */}
      <div className="mt-16 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    </div>
  );
}

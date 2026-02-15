/**
 * Brand-themed card skeleton with animate-pulse.
 * Matches BusCard dimensions for seamless loading transitions.
 */
export function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      {/* Image placeholder */}
      <div className="h-48 w-full rounded-xl bg-slate-200" />
      {/* Title */}
      <div className="mt-4 h-5 w-3/4 rounded-md bg-slate-200" />
      {/* Subtitle */}
      <div className="mt-2 h-4 w-1/2 rounded-md bg-slate-200" />
      {/* Amenities row */}
      <div className="mt-4 flex gap-2">
        <div className="h-6 w-16 rounded-md bg-slate-200" />
        <div className="h-6 w-16 rounded-md bg-slate-200" />
        <div className="h-6 w-16 rounded-md bg-slate-200" />
      </div>
      {/* Price + CTA */}
      <div className="mt-4 flex items-center justify-between">
        <div className="h-6 w-24 rounded-md bg-slate-200" />
        <div className="h-10 w-28 rounded-xl bg-slate-200" />
      </div>
    </div>
  );
}

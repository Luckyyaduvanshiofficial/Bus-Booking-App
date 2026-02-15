/**
 * Skeleton for popular route cards in the homepage.
 */
export function SkeletonRouteCard() {
  return (
    <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="h-32 w-full rounded-xl bg-slate-200" />
      <div className="mt-4 h-4 w-2/3 rounded-md bg-slate-200" />
      <div className="mt-2 flex items-center justify-between">
        <div className="h-3 w-16 rounded-md bg-slate-200" />
        <div className="h-5 w-20 rounded-md bg-slate-200" />
      </div>
    </div>
  );
}

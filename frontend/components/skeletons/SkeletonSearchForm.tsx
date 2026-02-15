/**
 * Search form skeleton matching the hero search card layout.
 */
export function SkeletonSearchForm() {
  return (
    <div className="animate-pulse rounded-full bg-white p-4 shadow-xl md:p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-2">
        <div className="h-12 flex-1 rounded-xl bg-slate-200" />
        <div className="h-12 flex-1 rounded-xl bg-slate-200" />
        <div className="h-12 flex-1 rounded-xl bg-slate-200" />
        <div className="h-12 w-full rounded-xl bg-slate-200 md:w-36" />
      </div>
    </div>
  );
}

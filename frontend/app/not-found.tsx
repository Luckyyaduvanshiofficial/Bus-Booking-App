import Link from "next/link";
import { MapPin, Home } from "lucide-react";

/**
 * Custom 404 page with brand styling.
 */
export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4">
      <div className="flex flex-col items-center gap-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50">
          <MapPin className="h-8 w-8 text-brand-blue" />
        </div>
        <div>
          <h1 className="text-6xl font-bold text-brand-blue">404</h1>
          <h2 className="mt-2 text-2xl font-semibold text-slate-900">
            Page not found
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Looks like this route doesn&apos;t exist. Let&apos;s get you back on
            track.
          </p>
        </div>
        <div className="flex gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 rounded-xl bg-brand-orange px-6 py-3 text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.02] hover:bg-orange-600 focus:ring-2 focus:ring-orange-500 focus:outline-none"
            aria-label="Go to homepage"
          >
            <Home className="h-4 w-4" />
            Go Home
          </Link>
          <Link
            href="/search"
            className="flex items-center gap-2 rounded-xl border-2 border-brand-blue px-6 py-3 text-sm font-semibold text-brand-blue transition-all duration-300 hover:bg-brand-blue hover:text-white focus:ring-2 focus:ring-orange-500 focus:outline-none"
            aria-label="Search for buses"
          >
            Search Buses
          </Link>
        </div>
      </div>
    </div>
  );
}

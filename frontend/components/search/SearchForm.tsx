"use client";

import { memo, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  MapPin,
  Calendar,
  Users,
  Search,
  ArrowRightLeft,
} from "lucide-react";

/**
 * Segmented search form for the homepage hero.
 *
 * - rounded-full container with shadow-xl
 * - Fields: From, To, Date, Passengers
 * - Orange "Search Buses" CTA
 * - Mobile: vertical stack
 */
export const SearchForm = memo(function SearchForm() {
  const router = useRouter();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [date, setDate] = useState("");
  const [passengers, setPassengers] = useState("");

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const params = new URLSearchParams();
      if (from) params.set("from", from);
      if (to) params.set("to", to);
      if (date) params.set("date", date);
      if (passengers) params.set("passengers", passengers);
      router.push(`/search?${params.toString()}`);
    },
    [from, to, date, passengers, router]
  );

  const handleSwap = useCallback(() => {
    setFrom(to);
    setTo(from);
  }, [from, to]);

  // Tomorrow's date as minimum
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  const minDate = tomorrow.toISOString().split("T")[0];

  return (
    <form
      onSubmit={handleSearch}
      className="w-full rounded-3xl bg-white p-4 shadow-xl md:rounded-full md:p-2"
    >
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-0">
        {/* ── From ──────────────────────────────── */}
        <div className="group relative flex flex-1 items-center gap-2 rounded-xl px-4 py-3 transition-colors hover:bg-slate-50 md:rounded-full">
          <MapPin className="h-5 w-5 shrink-0 text-brand-blue" />
          <div className="flex flex-1 flex-col">
            <label
              htmlFor="search-from"
              className="text-xs font-medium text-slate-400"
            >
              From
            </label>
            <input
              id="search-from"
              type="text"
              placeholder="Jaipur"
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="w-full border-none bg-transparent text-sm font-medium text-slate-900 placeholder:text-slate-300 focus:outline-none"
              autoComplete="off"
            />
          </div>
        </div>

        {/* ── Swap Button ──────────────────────── */}
        <button
          type="button"
          onClick={handleSwap}
          className="mx-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-slate-200 text-slate-400 transition-all duration-300 hover:border-brand-orange hover:text-brand-orange md:mx-0"
          aria-label="Swap from and to locations"
        >
          <ArrowRightLeft className="h-4 w-4" />
        </button>

        {/* ── To ────────────────────────────────── */}
        <div className="group relative flex flex-1 items-center gap-2 rounded-xl px-4 py-3 transition-colors hover:bg-slate-50 md:rounded-full">
          <MapPin className="h-5 w-5 shrink-0 text-brand-orange" />
          <div className="flex flex-1 flex-col">
            <label
              htmlFor="search-to"
              className="text-xs font-medium text-slate-400"
            >
              To
            </label>
            <input
              id="search-to"
              type="text"
              placeholder="Udaipur"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="w-full border-none bg-transparent text-sm font-medium text-slate-900 placeholder:text-slate-300 focus:outline-none"
              autoComplete="off"
            />
          </div>
        </div>

        {/* ── Divider (desktop) ─────────────────── */}
        <div className="hidden h-8 w-px bg-slate-200 md:block" />

        {/* ── Date ──────────────────────────────── */}
        <div className="group flex flex-1 items-center gap-2 rounded-xl px-4 py-3 transition-colors hover:bg-slate-50 md:rounded-full">
          <Calendar className="h-5 w-5 shrink-0 text-brand-blue" />
          <div className="flex flex-1 flex-col">
            <label
              htmlFor="search-date"
              className="text-xs font-medium text-slate-400"
            >
              Travel Date
            </label>
            <input
              id="search-date"
              type="date"
              min={minDate}
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full border-none bg-transparent text-sm font-medium text-slate-900 focus:outline-none"
            />
          </div>
        </div>

        {/* ── Divider (desktop) ─────────────────── */}
        <div className="hidden h-8 w-px bg-slate-200 md:block" />

        {/* ── Passengers ────────────────────────── */}
        <div className="group flex items-center gap-2 rounded-xl px-4 py-3 transition-colors hover:bg-slate-50 md:w-36 md:rounded-full">
          <Users className="h-5 w-5 shrink-0 text-brand-blue" />
          <div className="flex flex-1 flex-col">
            <label
              htmlFor="search-passengers"
              className="text-xs font-medium text-slate-400"
            >
              Passengers
            </label>
            <input
              id="search-passengers"
              type="number"
              min={7}
              max={60}
              placeholder="40"
              value={passengers}
              onChange={(e) => setPassengers(e.target.value)}
              className="w-full border-none bg-transparent text-sm font-medium text-slate-900 placeholder:text-slate-300 focus:outline-none"
            />
          </div>
        </div>

        {/* ── Search Button ─────────────────────── */}
        <button
          type="submit"
          className="flex h-12 items-center justify-center gap-2 rounded-xl bg-brand-orange px-6 text-sm font-semibold text-white transition-all duration-300 hover:scale-[1.02] hover:bg-orange-600 focus:ring-2 focus:ring-orange-500 focus:outline-none md:rounded-full md:px-8"
          aria-label="Search for available buses"
        >
          <Search className="h-4 w-4" />
          <span className="md:hidden lg:inline">Search</span>
        </button>
      </div>
    </form>
  );
});

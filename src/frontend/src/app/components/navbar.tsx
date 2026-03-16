"use client";

import Link from "next/link";
import React from "react";
import { usePathname } from "next/navigation";
import { Url } from "next/dist/shared/lib/router/router";

const navItems = [
    {
        id: "home",
        label: "Home",
        href: "/",
    },
    {
        id: "squat",
        label: "Squat",
        href: "/exercises/squat",
    },
    {
        id: "bench-press",
        label: "Bench Press",
        href: "/exercises/bench-press",
    },
    {
        id: "bent-over-barbell-row",
        label: "Bent-over Barbell Row",
        href: "/exercises/bent-over-barbell-row",
    },
];

const Navbar: React.FunctionComponent = () => {
  const pathname = usePathname();
  const isActive = (path: Url) => pathname === path;

  return (
    <nav className="w-full pb-4 md:pb-4">
      {/*
        <Link
          href="/"
          className="text-lg md:text-3xl font-bold text-spotify-green"
        >
          Visual Spotter
        </Link>
      */}
      <ul className="flex w-full flex-col items-stretch gap-2  md:flex-row lg:items-center">
        {navItems.map((eachItem) => (
          <li key={eachItem.id} className="w-full lg:w-auto">
            <Link
              href={eachItem.href}
              className={`flex w-full items-center justify-center rounded-xl border px-4 py-3 text-sm font-medium transition-colors lg:w-auto ${
                isActive(eachItem.href)
                  ? "border-cyan-300/70 bg-cyan-300/15 text-cyan-200"
                  : "border-blue-800/60 bg-blue-900/40 text-slate-100 hover:border-blue-500/70 hover:bg-blue-800/50 hover:text-blue-100"
              }`}
            >
              {eachItem.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default Navbar;



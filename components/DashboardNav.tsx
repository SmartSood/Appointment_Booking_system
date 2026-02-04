"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { AddonDefinition } from "@/lib/addons/registry";

export function DashboardNav({ addons }: { addons: AddonDefinition[] }) {
  const pathname = usePathname();

  return (
    <nav className="flex items-center gap-1">
      {addons.map((addon) => {
        const isActive = pathname === addon.path;
        return (
          <Link
            key={addon.id}
            href={addon.path}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition ${
              isActive
                ? "bg-primary-100 text-primary-700"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-800"
            }`}
          >
            {addon.icon && <span className="mr-1.5">{addon.icon}</span>}
            {addon.name}
          </Link>
        );
      })}
    </nav>
  );
}

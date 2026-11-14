"use client";
/**
 * Sidebar de navigation — HIPPO ANALYTICS
 */
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  CalendarDays,
  Gauge,
  Users,
  UserCheck,
  Brain,
  ListOrdered,
  BarChart3,
  History,
  Upload,
  Settings,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAVIGATION = [
  { groupe: "Principal", items: [
    { label: "Tableau de bord", href: "/", icon: LayoutDashboard },
    { label: "Programme du jour", href: "/programmes", icon: CalendarDays },
    { label: "Courses", href: "/courses", icon: CalendarDays },
  ]},
  { groupe: "Analyse", items: [
    { label: "Chevaux", href: "/chevaux", icon: Gauge },
    { label: "Jockeys", href: "/jockeys", icon: Users },
    { label: "Entraîneurs", href: "/entraineurs", icon: UserCheck },
  ]},
  { groupe: "Prédiction", items: [
    { label: "Prédictions IA", href: "/predictions", icon: Brain },
    { label: "Hypothèses", href: "/hypotheses", icon: ListOrdered },
    { label: "Statistiques", href: "/statistiques", icon: BarChart3 },
  ]},
  { groupe: "Gestion", items: [
    { label: "Historique", href: "/historique", icon: History },
    { label: "Importation", href: "/importation", icon: Upload },
    { label: "Synchronisation", href: "/synchronisation", icon: RefreshCw },
    { label: "Administration", href: "/administration", icon: Settings },
  ]},
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-hippo-900 text-white flex flex-col shrink-0 overflow-y-auto">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-hippo-800">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🐎</span>
          <div>
            <p className="font-bold text-lg leading-tight">HIPPO ANALYTICS</p>
            <p className="text-hippo-300 text-xs">PMU Burkina Faso</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-6">
        {NAVIGATION.map((groupe) => (
          <div key={groupe.groupe}>
            <p className="px-3 mb-1 text-xs font-semibold uppercase tracking-wider text-hippo-400">
              {groupe.groupe}
            </p>
            <ul className="space-y-0.5">
              {groupe.items.map((item) => {
                const Icon = item.icon;
                const actif = pathname === item.href ||
                  (item.href !== "/" && pathname.startsWith(item.href));
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                        actif
                          ? "bg-hippo-700 text-white font-medium"
                          : "text-hippo-300 hover:bg-hippo-800 hover:text-white"
                      )}
                    >
                      <Icon size={16} />
                      {item.label}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Version */}
      <div className="px-6 py-3 border-t border-hippo-800">
        <p className="text-hippo-400 text-xs">Version 1.0.0 — LONAB</p>
      </div>
    </aside>
  );
}

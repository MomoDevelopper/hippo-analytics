"use client";
/**
 * Composants UI réutilisables.
 */
import { cn } from "@/lib/utils";

// ── StatCard ─────────────────────────────────────────────
interface StatCardProps {
  titre: string;
  valeur: string | number;
  sous_titre?: string;
  couleur?: "blue" | "green" | "yellow" | "red" | "gray";
  icon?: React.ReactNode;
}

export function StatCard({ titre, valeur, sous_titre, couleur = "blue", icon }: StatCardProps) {
  const couleurs = {
    blue:   "border-l-hippo-500 bg-hippo-50",
    green:  "border-l-green-500 bg-green-50",
    yellow: "border-l-yellow-500 bg-yellow-50",
    red:    "border-l-red-500 bg-red-50",
    gray:   "border-l-gray-400 bg-gray-50",
  };

  return (
    <div className={cn("card border-l-4 flex items-start gap-4", couleurs[couleur])}>
      {icon && <div className="mt-0.5 text-gray-500">{icon}</div>}
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-gray-500">{titre}</p>
        <p className="text-2xl font-bold text-gray-800 mt-0.5">{valeur}</p>
        {sous_titre && <p className="text-xs text-gray-400 mt-0.5">{sous_titre}</p>}
      </div>
    </div>
  );
}

// ── NoteBar ───────────────────────────────────────────────
interface NoteBarProps {
  valeur: number;
  label?: string;
  className?: string;
}

export function NoteBar({ valeur, label, className }: NoteBarProps) {
  const couleur =
    valeur >= 80 ? "bg-green-500" :
    valeur >= 65 ? "bg-blue-500" :
    valeur >= 50 ? "bg-yellow-500" :
    "bg-red-400";

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {label && <span className="text-xs text-gray-500 w-20 shrink-0">{label}</span>}
      <div className="note-bar flex-1">
        <div
          className={cn("note-bar-fill", couleur)}
          style={{ width: `${Math.min(100, Math.max(0, valeur))}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700 w-8 text-right">
        {valeur.toFixed(0)}
      </span>
    </div>
  );
}

// ── Badge de catégorie ────────────────────────────────────
import { couleurCategorie, libelleCategorie } from "@/lib/utils";

export function BadgeCategorie({ categorie }: { categorie: string | null | undefined }) {
  return (
    <span className={cn("badge", couleurCategorie(categorie))}>
      {libelleCategorie(categorie)}
    </span>
  );
}

// ── Skeleton de chargement ────────────────────────────────
export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("animate-pulse bg-gray-200 rounded", className)} />;
}

export function SkeletonCard() {
  return (
    <div className="card space-y-3">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-1/4" />
    </div>
  );
}

// ── Message d'erreur ──────────────────────────────────────
export function ErreurMessage({ message }: { message: string }) {
  return (
    <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
      ⚠️ {message}
    </div>
  );
}

// ── Message vide ──────────────────────────────────────────
export function MessageVide({ texte = "Aucune donnée disponible" }: { texte?: string }) {
  return (
    <div className="text-center py-12 text-gray-400">
      <p className="text-4xl mb-3">📭</p>
      <p className="text-sm">{texte}</p>
    </div>
  );
}

// ── Badge de statut ───────────────────────────────────────
import { couleurStatut, libelleStatut } from "@/lib/utils";

export function BadgeStatut({ statut }: { statut: string | null | undefined }) {
  return (
    <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium", couleurStatut(statut))}>
      {libelleStatut(statut)}
    </span>
  );
}

// ── Spinner ───────────────────────────────────────────────
export function Spinner({ size = 20 }: { size?: number }) {
  return (
    <svg
      className="animate-spin text-hippo-600"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  );
}

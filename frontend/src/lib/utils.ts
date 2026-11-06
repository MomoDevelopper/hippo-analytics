/**
 * Fonctions utilitaires partagées dans HIPPO ANALYTICS.
 */
import { clsx, type ClassValue } from "clsx";

/** Combine des classes CSS conditionnellement (wrapper de clsx). */
export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

/** Formate une date ISO en format français DD/MM/YYYY. */
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", year: "numeric" });
  } catch {
    return dateStr;
  }
}

/** Formate une date et heure ISO en français. */
export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    return d.toLocaleString("fr-FR", {
      day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

/** Formate un pourcentage avec N décimales. */
export function formatPct(value: number | null | undefined, decimals = 1): string {
  if (value == null) return "—";
  return `${value.toFixed(decimals)}%`;
}

/** Formate une cote hippique (ex: 4.5 → "4/1"). */
export function formatCote(cote: number | null | undefined): string {
  if (cote == null) return "N/D";
  return `${cote.toFixed(1)}`;
}

/** Retourne la couleur CSS correspondant à une note 0-100. */
export function couleurNote(note: number): string {
  if (note >= 80) return "text-green-600";
  if (note >= 65) return "text-blue-600";
  if (note >= 50) return "text-yellow-600";
  return "text-red-500";
}

/** Retourne la couleur badge d'une catégorie de cheval. */
export function couleurCategorie(categorie: string | null | undefined): string {
  switch (categorie) {
    case "favori_stat":    return "bg-green-100 text-green-800 border-green-300";
    case "favori_cote":    return "bg-blue-100 text-blue-800 border-blue-300";
    case "outsider":       return "bg-yellow-100 text-yellow-800 border-yellow-300";
    case "risque":         return "bg-red-100 text-red-800 border-red-300";
    default:               return "bg-gray-100 text-gray-700 border-gray-300";
  }
}

/** Traduit une catégorie en libellé français. */
export function libelleCategorie(categorie: string | null | undefined): string {
  switch (categorie) {
    case "favori_stat":  return "Favori Statistique";
    case "favori_cote":  return "Favori des Cotes";
    case "outsider":     return "Outsider Intéressant";
    case "risque":       return "Cheval à Risque";
    default:             return categorie || "—";
  }
}

/** Traduit un statut de course en libellé français. */
export function libelleStatut(statut: string | null | undefined): string {
  switch (statut) {
    case "programmée":  return "Programmée";
    case "en_cours":    return "En cours";
    case "terminée":    return "Terminée";
    case "annulée":     return "Annulée";
    default:            return statut || "—";
  }
}

/** Couleur du badge de statut de course. */
export function couleurStatut(statut: string | null | undefined): string {
  switch (statut) {
    case "programmée":  return "bg-blue-100 text-blue-700";
    case "en_cours":    return "bg-yellow-100 text-yellow-700 animate-pulse";
    case "terminée":    return "bg-gray-100 text-gray-600";
    case "annulée":     return "bg-red-100 text-red-600";
    default:            return "bg-gray-100 text-gray-600";
  }
}

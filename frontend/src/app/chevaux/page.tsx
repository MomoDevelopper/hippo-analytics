"use client";
/**
 * Page — Liste des chevaux avec recherche
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Search, Horse } from "lucide-react";
import { chevauxApi } from "@/lib/api";
import { Skeleton, MessageVide } from "@/components/ui";
import type { Cheval } from "@/types";

export default function ChevauxPage() {
  const [recherche, setRecherche] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery<{ data: { chevaux: Cheval[]; total: number } }>({
    queryKey: ["chevaux", recherche, page],
    queryFn: () => chevauxApi.lister({ nom: recherche || undefined, page }),
    placeholderData: (prev) => prev,
  });

  const chevaux = data?.data?.chevaux ?? [];
  const total = data?.data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Horse size={24} className="text-hippo-600" /> Chevaux
        </h1>
        <p className="text-sm text-gray-500 mt-1">{total} chevaux enregistrés</p>
      </div>

      {/* Barre de recherche */}
      <div className="relative">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          value={recherche}
          onChange={(e) => { setRecherche(e.target.value); setPage(1); }}
          placeholder="Rechercher un cheval par son nom..."
          className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-hippo-300 bg-white"
        />
      </div>

      {/* Grille de chevaux */}
      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {[...Array(12)].map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
        </div>
      ) : chevaux.length === 0 ? (
        <MessageVide texte={recherche ? `Aucun cheval trouvé pour "${recherche}"` : "Aucun cheval enregistré"} />
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {chevaux.map((c) => (
            <Link
              key={c.id}
              href={`/chevaux/${c.id}`}
              className="card hover:shadow-md hover:border-hippo-200 transition-all group cursor-pointer"
            >
              <div className="flex items-start justify-between mb-2">
                <span className="text-xl">🐎</span>
                <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full">
                  {c.sexe ?? "?"} · {c.age ?? "?"}ans
                </span>
              </div>
              <p className="font-bold text-gray-800 group-hover:text-hippo-700 truncate">
                {c.nom}
              </p>
              <p className="text-xs text-gray-500 mt-1 truncate">{c.entraineur?.nom ?? "Entraîneur inconnu"}</p>
              <p className="text-xs text-gray-400 truncate">{c.proprietaire ?? "—"}</p>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > 50 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="btn-secondary text-sm py-1.5 px-3 disabled:opacity-40"
          >
            ← Précédent
          </button>
          <span className="flex items-center text-sm text-gray-500 px-3">
            Page {page} sur {Math.ceil(total / 50)}
          </span>
          <button
            onClick={() => setPage(page + 1)}
            disabled={page >= Math.ceil(total / 50)}
            className="btn-secondary text-sm py-1.5 px-3 disabled:opacity-40"
          >
            Suivant →
          </button>
        </div>
      )}
    </div>
  );
}

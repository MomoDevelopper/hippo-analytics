"use client";
/**
 * Page — Fiche détaillée d'un cheval
 */
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Gauge, TrendingUp, Award } from "lucide-react";
import { chevauxApi } from "@/lib/api";
import { NoteBar, Skeleton, ErreurMessage } from "@/components/ui";
import { formatDate, formatCote } from "@/lib/utils";
import type { Cheval } from "@/types";

export default function FicheChevalPage() {
  const params = useParams();
  const chevalId = Number(params.id);

  const { data, isLoading } = useQuery<{ data: Cheval }>({
    queryKey: ["cheval", chevalId],
    queryFn: () => chevauxApi.fiche(chevalId),
  });

  const cheval = data?.data;

  if (isLoading) return (
    <div className="space-y-4">
      <Skeleton className="h-32 rounded-xl" />
      <Skeleton className="h-64 rounded-xl" />
    </div>
  );
  if (!cheval) return <ErreurMessage message="Cheval introuvable" />;

  const stats = cheval.statistiques;

  return (
    <div className="space-y-6">
      {/* En-tête cheval */}
      <div className="card">
        <div className="flex items-start gap-5">
          <div className="w-16 h-16 bg-hippo-100 rounded-2xl flex items-center justify-center text-3xl shrink-0">
            🐎
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900">{cheval.nom}</h1>
            <div className="flex flex-wrap gap-3 mt-2 text-sm text-gray-500">
              {cheval.sexe && <span className="bg-gray-100 px-2 py-0.5 rounded-full text-xs">
                {cheval.sexe === "M" ? "Mâle" : cheval.sexe === "F" ? "Femelle" : cheval.sexe === "H" ? "Hongre" : cheval.sexe}
              </span>}
              {cheval.age && <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full text-xs">{cheval.age} ans</span>}
              {cheval.robe && <span className="bg-orange-50 text-orange-700 px-2 py-0.5 rounded-full text-xs">{cheval.robe}</span>}
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3 text-sm">
              {cheval.proprietaire && (
                <div><span className="text-gray-400">Propriétaire : </span>
                  <span className="font-medium">{cheval.proprietaire}</span>
                </div>
              )}
              {cheval.entraineur && (
                <div><span className="text-gray-400">Entraîneur : </span>
                  <span className="font-medium">{cheval.entraineur.nom}</span>
                </div>
              )}
              {cheval.naisseur && (
                <div><span className="text-gray-400">Naisseur : </span>
                  <span className="font-medium">{cheval.naisseur}</span>
                </div>
              )}
              {cheval.origine && (
                <div><span className="text-gray-400">Origine : </span>
                  <span className="font-medium text-xs">{cheval.origine}</span>
                </div>
              )}
            </div>
          </div>

          {/* Stats rapides */}
          {stats && (
            <div className="text-right shrink-0">
              <div className="flex gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">{stats.victoires}</p>
                  <p className="text-xs text-gray-400">Victoires</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">{stats.places_top3}</p>
                  <p className="text-xs text-gray-400">Podiums</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-700">{stats.sorties_analysees}</p>
                  <p className="text-xs text-gray-400">Sorties</p>
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-2">
                Taux de victoire : <span className="font-bold text-green-600">{stats.taux_victoire.toFixed(1)}%</span>
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Historique des performances */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={18} className="text-hippo-600" />
          <h2 className="font-semibold text-gray-800">Dernières performances</h2>
        </div>

        {!cheval.dernieres_performances?.length ? (
          <p className="text-gray-400 text-sm text-center py-6">Aucune performance enregistrée</p>
        ) : (
          <table className="table-hippo">
            <thead>
              <tr>
                <th>Date</th>
                <th>Hippodrome</th>
                <th>Distance</th>
                <th>Place</th>
                <th>Partants</th>
                <th>Jockey</th>
                <th>Cote</th>
              </tr>
            </thead>
            <tbody>
              {cheval.dernieres_performances.map((p, i) => (
                <tr key={i}>
                  <td>{formatDate(p.date)}</td>
                  <td>{p.hippodrome ?? "—"}</td>
                  <td>{p.distance ? `${p.distance}m` : "—"}</td>
                  <td>
                    <span className={`font-bold ${
                      p.place === 1 ? "text-yellow-500" :
                      p.place && p.place <= 3 ? "text-green-600" :
                      p.place && p.place <= 5 ? "text-blue-600" : "text-gray-600"
                    }`}>
                      {p.place != null ? `${p.place}${p.place === 1 ? "er" : "ème"}` : "—"}
                    </span>
                    {p.partants && <span className="text-gray-400 text-xs ml-1">/{p.partants}</span>}
                  </td>
                  <td className="text-gray-500 text-xs">{p.partants ?? "—"}</td>
                  <td className="text-gray-600 text-sm">{p.jockey ?? "—"}</td>
                  <td className="text-gray-500">{formatCote(p.cote)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

"use client";
/**
 * Page — Classement des entraîneurs
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { UserCheck } from "lucide-react";
import { entraineursApi } from "@/lib/api";
import { Skeleton, MessageVide } from "@/components/ui";
import type { Entraineur } from "@/types";

export default function EntraineursPage() {
  const [periode, setPeriode] = useState(90);

  const { data, isLoading } = useQuery<{ data: { classement: Entraineur[] } }>({
    queryKey: ["entraineurs", periode],
    queryFn: () => entraineursApi.classement(periode),
  });

  const classement = data?.data?.classement ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <UserCheck size={24} className="text-hippo-600" /> Classement des entraîneurs
          </h1>
          <p className="text-sm text-gray-500 mt-1">{classement.length} entraîneurs analysés</p>
        </div>
        <select
          value={periode}
          onChange={(e) => setPeriode(Number(e.target.value))}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-hippo-300"
        >
          <option value={30}>30 derniers jours</option>
          <option value={90}>90 derniers jours</option>
          <option value={365}>12 derniers mois</option>
        </select>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[...Array(8)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : classement.length === 0 ? (
          <div className="p-6"><MessageVide texte="Aucune donnée disponible pour cette période" /></div>
        ) : (
          <table className="table-hippo">
            <thead>
              <tr>
                <th>Rang</th>
                <th>Entraîneur</th>
                <th>Écurie</th>
                <th>Chevaux engagés</th>
                <th>Sorties</th>
                <th>Victoires</th>
                <th>Top 5</th>
                <th>% Victoires</th>
                <th>% Classés</th>
              </tr>
            </thead>
            <tbody>
              {classement.map((e) => (
                <tr key={e.id}>
                  <td>
                    <span className={`font-bold ${
                      e.rang === 1 ? "text-yellow-500 text-lg" :
                      e.rang === 2 ? "text-gray-400 text-lg" :
                      e.rang === 3 ? "text-orange-400 text-lg" : "text-gray-600"
                    }`}>
                      {e.rang === 1 ? "🥇" : e.rang === 2 ? "🥈" : e.rang === 3 ? "🥉" : `#${e.rang}`}
                    </span>
                  </td>
                  <td className="font-semibold">{e.nom}</td>
                  <td className="text-gray-500 text-xs">{(e as any).ecurie ?? "—"}</td>
                  <td className="text-gray-600">{(e as any).chevaux_engages}</td>
                  <td className="text-gray-600">{(e as any).sorties}</td>
                  <td><span className="font-bold text-green-600">{e.victoires}</span></td>
                  <td className="text-blue-600">{(e as any).top5}</td>
                  <td>
                    <span className="font-medium text-green-700">{e.taux_victoire?.toFixed(1)}%</span>
                  </td>
                  <td className="text-gray-600">{(e as any).taux_classes?.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

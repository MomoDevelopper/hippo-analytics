"use client";
/**
 * Page — Classement des jockeys
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Users, TrendingUp } from "lucide-react";
import { jockeysApi } from "@/lib/api";
import { Skeleton, MessageVide } from "@/components/ui";
import type { Jockey } from "@/types";

export default function JockeysPage() {
  const [periode, setPeriode] = useState(90);

  const { data, isLoading } = useQuery<{ data: { classement: Jockey[]; periode_jours: number } }>({
    queryKey: ["jockeys", periode],
    queryFn: () => jockeysApi.classement(periode),
  });

  const classement = data?.data?.classement ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users size={24} className="text-hippo-600" /> Classement des jockeys
          </h1>
          <p className="text-sm text-gray-500 mt-1">{classement.length} jockeys analysés</p>
        </div>
        <select
          value={periode}
          onChange={(e) => setPeriode(Number(e.target.value))}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-hippo-300"
        >
          <option value={7}>7 derniers jours</option>
          <option value={30}>30 derniers jours</option>
          <option value={90}>90 derniers jours</option>
          <option value={365}>12 derniers mois</option>
        </select>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[...Array(10)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : classement.length === 0 ? (
          <div className="p-6"><MessageVide texte="Aucune donnée disponible pour cette période" /></div>
        ) : (
          <table className="table-hippo">
            <thead>
              <tr>
                <th>Rang</th>
                <th>Jockey</th>
                <th>Courses</th>
                <th>Victoires</th>
                <th>Podiums (Top 3)</th>
                <th>Taux victoire</th>
                <th>Taux Top 3</th>
              </tr>
            </thead>
            <tbody>
              {classement.map((j) => (
                <tr key={j.id}>
                  <td>
                    <span className={`font-bold ${
                      j.rang === 1 ? "text-yellow-500 text-lg" :
                      j.rang === 2 ? "text-gray-400 text-lg" :
                      j.rang === 3 ? "text-orange-400 text-lg" : "text-gray-600"
                    }`}>
                      {j.rang === 1 ? "🥇" : j.rang === 2 ? "🥈" : j.rang === 3 ? "🥉" : `#${j.rang}`}
                    </span>
                  </td>
                  <td className="font-semibold text-gray-800">{j.nom}</td>
                  <td className="text-gray-600">{j.courses}</td>
                  <td>
                    <span className="font-bold text-green-600">{j.victoires}</span>
                  </td>
                  <td className="text-blue-600">{j.places_top3}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-green-500 rounded-full"
                          style={{ width: `${Math.min(100, (j.taux_victoire ?? 0) * 3.33)}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-green-700">
                        {j.taux_victoire?.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="text-gray-600 text-sm">{j.taux_top3?.toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

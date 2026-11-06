"use client";
/**
 * Page — Statistiques et performance du modèle de prédiction
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, TrendingUp, Target, Award, Database } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from "recharts";
import { statistiquesApi } from "@/lib/api";
import { StatCard, Skeleton, MessageVide } from "@/components/ui";
import { formatPct } from "@/lib/utils";
import type { StatistiquesGlobales } from "@/types";

const COULEURS_PIE = ["#0284c7", "#22c55e", "#f59e0b", "#ef4444"];

export default function StatistiquesPage() {
  const [periode, setPeriode] = useState(30);

  const { data: statsGlobales, isLoading: loadingGlobales } = useQuery<{ data: StatistiquesGlobales }>({
    queryKey: ["statistiques-globales"],
    queryFn: () => statistiquesApi.globales(),
  });

  const { data: statsModele, isLoading: loadingModele } = useQuery<{ data: any }>({
    queryKey: ["statistiques-modele", periode],
    queryFn: () => statistiquesApi.modele(periode),
    retry: false,
  });

  const stats = statsGlobales?.data;
  const modele = statsModele?.data;

  const donneesDb = stats ? [
    { nom: "Chevaux", valeur: stats.base_de_donnees.total_chevaux, couleur: "#0284c7" },
    { nom: "Jockeys", valeur: stats.base_de_donnees.total_jockeys, couleur: "#22c55e" },
    { nom: "Entraîneurs", valeur: stats.base_de_donnees.total_entraineurs, couleur: "#f59e0b" },
    { nom: "Courses terminées", valeur: stats.base_de_donnees.courses_terminees, couleur: "#8b5cf6" },
  ] : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <BarChart3 size={24} className="text-hippo-600" /> Statistiques
          </h1>
          <p className="text-sm text-gray-500 mt-1">Performance du modèle et état de la base de données</p>
        </div>
        <select
          value={periode}
          onChange={(e) => setPeriode(Number(e.target.value))}
          className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-hippo-300"
        >
          <option value={7}>7 derniers jours</option>
          <option value={30}>30 derniers jours</option>
          <option value={90}>90 derniers jours</option>
        </select>
      </div>

      {/* Statistiques globales */}
      {loadingGlobales ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-24 rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard titre="Total courses" valeur={stats?.base_de_donnees.total_courses ?? 0}
            icon={<Database size={18}/>} couleur="blue" />
          <StatCard titre="Courses terminées" valeur={stats?.base_de_donnees.courses_terminees ?? 0}
            icon={<Award size={18}/>} couleur="green" />
          <StatCard titre="Pronostics générés" valeur={stats?.moteur_prediction.pronostics_generes ?? 0}
            icon={<Target size={18}/>} couleur="yellow" />
          <StatCard titre="Évaluations disponibles" valeur={stats?.moteur_prediction.courses_evaluables ?? 0}
            icon={<TrendingUp size={18}/>} couleur="gray" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Graphique base de données */}
        <div className="card">
          <h2 className="font-semibold text-gray-800 mb-4">Contenu de la base de données</h2>
          {donneesDb.length === 0 ? (
            <MessageVide texte="Aucune donnée" />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={donneesDb} barSize={32}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="nom" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="valeur" name="Nombre" radius={[4, 4, 0, 0]}>
                  {donneesDb.map((entry, i) => (
                    <Cell key={i} fill={entry.couleur} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Performance du modèle */}
        <div className="card">
          <h2 className="font-semibold text-gray-800 mb-4">
            Performance du modèle
            <span className="text-xs text-gray-400 font-normal ml-2">({periode} derniers jours)</span>
          </h2>

          {loadingModele ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : !modele || modele.message ? (
            <div className="flex flex-col items-center justify-center h-48 text-center">
              <p className="text-4xl mb-3">📊</p>
              <p className="text-gray-500 text-sm font-medium">
                {modele?.message ?? "Données insuffisantes"}
              </p>
              <p className="text-gray-400 text-xs mt-2">
                Enregistrez des résultats officiels pour mesurer la précision du modèle
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">
                {modele.courses_evaluees} course(s) évaluée(s) sur {periode} jours
              </p>

              {[
                { label: "Gagnant dans le Top 5 prédit", valeur: modele.taux_gagnant_predit, couleur: "bg-green-500" },
                { label: "Top 5 complet identifié", valeur: modele.taux_top5_complet, couleur: "bg-blue-500" },
                { label: "Ordre exact", valeur: modele.taux_ordre_exact, couleur: "bg-purple-500" },
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600">{item.label}</span>
                    <span className="font-semibold text-gray-800">{item.valeur?.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${item.couleur} transition-all duration-700`}
                      style={{ width: `${Math.min(100, item.valeur ?? 0)}%` }}
                    />
                  </div>
                </div>
              ))}

              <div className="pt-2 border-t border-gray-100 text-sm">
                <span className="text-gray-500">Chevaux communs en moyenne : </span>
                <span className="font-bold text-hippo-700">
                  {modele.moyenne_chevaux_communs?.toFixed(2)} / 5
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

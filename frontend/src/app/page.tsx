"use client";
/**
 * Tableau de bord principal — HIPPO ANALYTICS
 * Vue d'ensemble : stats, courses du jour, dernières prédictions, sync.
 */
import { useQuery } from "@tanstack/react-query";
import {
  Horse,
  Users,
  UserCheck,
  Trophy,
  RefreshCw,
  TrendingUp,
  CalendarDays,
  Brain,
} from "lucide-react";
import Link from "next/link";
import { statistiquesApi, coursesApi, syncApi } from "@/lib/api";
import { StatCard, SkeletonCard, BadgeStatut, MessageVide } from "@/components/ui";
import { formatDate, formatDateTime, formatPct } from "@/lib/utils";
import type { StatistiquesGlobales, Course, SyncStatus } from "@/types";

export default function DashboardPage() {
  const { data: statsData, isLoading: statsLoading } = useQuery<{ data: StatistiquesGlobales }>({
    queryKey: ["statistiques-globales"],
    queryFn: () => statistiquesApi.globales(),
  });

  const { data: coursesData, isLoading: coursesLoading } = useQuery<{ data: { courses: Course[] } }>({
    queryKey: ["courses-aujourd-hui"],
    queryFn: () => {
      const aujourd_hui = new Date().toISOString().split("T")[0];
      return coursesApi.lister({ date_course: aujourd_hui });
    },
    refetchInterval: 120_000,
  });

  const { data: syncData } = useQuery<{ data: SyncStatus }>({
    queryKey: ["sync-status"],
    queryFn: () => syncApi.statut(),
    refetchInterval: 60_000,
  });

  const stats = statsData?.data;
  const courses = coursesData?.data?.courses || [];
  const sync = syncData?.data;

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
        <p className="text-gray-500 text-sm mt-1">
          {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
        </p>
      </div>

      {/* Statistiques globales */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Aperçu général
        </h2>
        {statsLoading ? (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              titre="Chevaux enregistrés"
              valeur={stats?.base_de_donnees.total_chevaux ?? 0}
              icon={<Horse size={18} />}
              couleur="blue"
            />
            <StatCard
              titre="Jockeys actifs"
              valeur={stats?.base_de_donnees.total_jockeys ?? 0}
              icon={<Users size={18} />}
              couleur="green"
            />
            <StatCard
              titre="Entraîneurs"
              valeur={stats?.base_de_donnees.total_entraineurs ?? 0}
              icon={<UserCheck size={18} />}
              couleur="yellow"
            />
            <StatCard
              titre="Pronostics générés"
              valeur={stats?.moteur_prediction.pronostics_generes ?? 0}
              icon={<Brain size={18} />}
              couleur="gray"
            />
          </div>
        )}
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Courses du jour */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CalendarDays size={18} className="text-hippo-600" />
              <h2 className="font-semibold text-gray-800">Courses du jour</h2>
            </div>
            <Link href="/courses" className="text-xs text-hippo-600 hover:underline">
              Voir toutes →
            </Link>
          </div>

          {coursesLoading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-100 animate-pulse rounded-lg" />
              ))}
            </div>
          ) : courses.length === 0 ? (
            <MessageVide texte="Aucune course programmée aujourd'hui" />
          ) : (
            <div className="space-y-2">
              {courses.map((course) => (
                <Link
                  key={course.id}
                  href={`/courses/${course.id}`}
                  className="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:bg-blue-50/50 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-full bg-hippo-100 text-hippo-700 text-xs font-bold flex items-center justify-center">
                      C{course.numero}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-800 group-hover:text-hippo-700">
                        {course.hippodrome}
                      </p>
                      <p className="text-xs text-gray-400">
                        {course.distance ? `${course.distance}m` : "Distance N/D"} ·{" "}
                        {course.nombre_partants ?? "?"} partants
                      </p>
                    </div>
                  </div>
                  <BadgeStatut statut={course.statut} />
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Panneau de droite : Sync + Performances */}
        <div className="space-y-4">
          {/* Synchronisation autonome */}
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <RefreshCw size={16} className="text-hippo-600" />
              <h3 className="font-semibold text-gray-800 text-sm">Synchronisation LONAB</h3>
            </div>
            {sync ? (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Statut</span>
                  <span className={
                    sync.statut === "succès" ? "text-green-600 font-medium" :
                    sync.statut === "source_indisponible" ? "text-orange-500" :
                    sync.statut === "jamais_executé" ? "text-gray-400" :
                    "text-red-500"
                  }>
                    {sync.statut === "jamais_executé" ? "En attente" :
                     sync.statut === "succès" ? "✓ OK" :
                     sync.statut === "source_indisponible" ? "Source indisponible" :
                     sync.statut}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Dernière sync</span>
                  <span className="text-gray-700 text-xs">
                    {sync.derniere_execution ? formatDateTime(sync.derniere_execution) : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Fichiers récupérés</span>
                  <span className="text-gray-700">{sync.fichiers_recuperes}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Intervalle</span>
                  <span className="text-gray-700">Toutes les {sync.intervalle_heures}h</span>
                </div>
                {sync.erreur && (
                  <p className="text-xs text-red-500 mt-1">⚠️ {sync.erreur}</p>
                )}
              </div>
            ) : (
              <p className="text-xs text-gray-400">Connexion au backend...</p>
            )}
            <Link
              href="/synchronisation"
              className="mt-3 w-full btn-secondary text-xs py-1.5 justify-center"
            >
              Gérer la synchronisation
            </Link>
          </div>

          {/* Performance du modèle */}
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp size={16} className="text-hippo-600" />
              <h3 className="font-semibold text-gray-800 text-sm">Performance du modèle</h3>
            </div>
            {stats?.moteur_prediction.courses_evaluables === 0 ? (
              <p className="text-xs text-gray-400">
                Pas encore de données pour mesurer la précision du modèle.
                Enregistrez des résultats officiels pour activer cette section.
              </p>
            ) : (
              <div className="text-sm space-y-1">
                <p className="text-gray-600">{stats?.moteur_prediction.precision}</p>
                <p className="text-xs text-gray-400">
                  {stats?.moteur_prediction.courses_evaluables} course(s) évaluée(s)
                </p>
              </div>
            )}
            <Link
              href="/statistiques"
              className="mt-3 w-full btn-secondary text-xs py-1.5 justify-center"
            >
              Voir les statistiques
            </Link>
          </div>
        </div>
      </div>

      {/* Liens rapides */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Actions rapides
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { label: "Importer un programme", href: "/importation", icon: "📥", desc: "PDF ou Excel" },
            { label: "Lancer une prédiction", href: "/predictions", icon: "🎯", desc: "Monte Carlo" },
            { label: "Voir les hypothèses", href: "/hypotheses", icon: "📋", desc: "Top 5 ordonnés" },
            { label: "Enregistrer un résultat", href: "/historique", icon: "✅", desc: "Arrivée officielle" },
          ].map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="card hover:border-hippo-200 hover:shadow-md transition-all group cursor-pointer"
            >
              <p className="text-2xl mb-2">{item.icon}</p>
              <p className="text-sm font-medium text-gray-800 group-hover:text-hippo-700">
                {item.label}
              </p>
              <p className="text-xs text-gray-400">{item.desc}</p>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

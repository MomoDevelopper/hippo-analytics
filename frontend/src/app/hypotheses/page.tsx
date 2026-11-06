"use client";
/**
 * Page — Hypothèses (sélection d'une course pour voir les combinaisons)
 */
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ListOrdered, ArrowRight } from "lucide-react";
import { coursesApi } from "@/lib/api";
import { BadgeStatut, MessageVide, Skeleton } from "@/components/ui";
import { formatDate } from "@/lib/utils";
import type { Course } from "@/types";

export default function HypothesesPage() {
  const { data, isLoading } = useQuery<{ data: { courses: Course[] } }>({
    queryKey: ["courses-hypotheses"],
    queryFn: () => coursesApi.lister({}),
  });

  const courses = data?.data?.courses ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ListOrdered size={24} className="text-hippo-600" /> Hypothèses de classement
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Jusqu'à 524 160 ordres possibles pour 5 chevaux sur 16 · triés par probabilité décroissante
        </p>
      </div>

      <div className="p-4 bg-gray-50 rounded-xl border border-gray-100 text-sm text-gray-600">
        <p>
          Pour <strong>16 partants</strong>, le nombre total d'ordres possibles des 5 premiers est :{" "}
          <strong className="text-hippo-700 text-base">P(16,5) = 16 × 15 × 14 × 13 × 12 = 524 160</strong>
        </p>
        <p className="text-gray-400 mt-1 text-xs">
          Le moteur Monte Carlo simule 100 000 arrivées et classe ces hypothèses par fréquence d'apparition.
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-16 rounded-xl" />)}
        </div>
      ) : courses.length === 0 ? (
        <MessageVide texte="Aucune course disponible. Importez un programme et lancez une prédiction." />
      ) : (
        <div className="grid gap-3">
          {courses.map((course) => (
            <Link
              key={course.id}
              href={`/courses/${course.id}`}
              className="card hover:shadow-md hover:border-hippo-200 transition-all group flex items-center gap-4"
            >
              <div className="w-12 h-12 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center font-bold text-lg shrink-0">
                C{course.numero}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-0.5">
                  <p className="font-semibold text-gray-800 group-hover:text-hippo-700">
                    {course.hippodrome}
                  </p>
                  <BadgeStatut statut={course.statut} />
                </div>
                <p className="text-sm text-gray-500">
                  {formatDate(course.date)} · {course.reunion} ·{" "}
                  {course.nombre_partants ?? "?"} partants ·{" "}
                  {course.distance ? `${course.distance}m` : "Distance N/D"}
                </p>
              </div>
              <div className="flex items-center gap-2 text-hippo-600 text-sm font-medium">
                <ListOrdered size={16} />
                Voir les hypothèses
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

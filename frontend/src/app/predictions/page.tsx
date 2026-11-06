"use client";
/**
 * Page — Prédictions (sélection d'une course pour lancer l'analyse)
 */
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Brain, ArrowRight } from "lucide-react";
import { coursesApi } from "@/lib/api";
import { BadgeStatut, MessageVide, Skeleton } from "@/components/ui";
import { formatDate } from "@/lib/utils";
import type { Course } from "@/types";

export default function PredictionsPage() {
  const { data, isLoading } = useQuery<{ data: { courses: Course[] } }>({
    queryKey: ["courses-predictions"],
    queryFn: () => coursesApi.lister({ statut: "programmée" }),
  });

  const courses = data?.data?.courses ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Brain size={24} className="text-hippo-600" /> Prédictions IA
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Sélectionnez une course programmée pour lancer le moteur de prédiction Monte Carlo
        </p>
      </div>

      <div className="p-4 bg-hippo-50 rounded-xl border border-hippo-100 text-sm text-hippo-700">
        <p className="font-medium mb-1">🎯 Comment fonctionne le moteur de prédiction ?</p>
        <ol className="list-decimal list-inside space-y-1 text-hippo-600">
          <li>Calcul des notes (0-100) pour chaque partant : forme, distance, jockey, entraîneur, régularité</li>
          <li>Normalisation en probabilités de victoire via softmax</li>
          <li>100 000 arrivées simulées (Monte Carlo — modèle Plackett-Luce)</li>
          <li>Classement des 524 160 hypothèses possibles par probabilité décroissante</li>
        </ol>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}
        </div>
      ) : courses.length === 0 ? (
        <div className="card">
          <MessageVide texte="Aucune course programmée. Importez d'abord un programme PMU'B." />
          <div className="text-center mt-4">
            <Link href="/importation" className="btn-primary">
              Importer un programme
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid gap-3">
          {courses.map((course) => (
            <Link
              key={course.id}
              href={`/courses/${course.id}`}
              className="card hover:shadow-md hover:border-hippo-200 transition-all group flex items-center gap-4"
            >
              <div className="w-12 h-12 rounded-xl bg-hippo-100 text-hippo-700 flex items-center justify-center font-bold text-lg shrink-0">
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
                  {course.distance ? `${course.distance}m` : "Distance N/D"} ·{" "}
                  {course.nombre_partants ?? "?"} partants
                </p>
              </div>
              <div className="flex items-center gap-2 text-hippo-600 text-sm font-medium">
                <Brain size={16} />
                Analyser
                <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

"use client";
/**
 * Page — Liste des courses hippiques
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { CalendarDays, Search, Filter } from "lucide-react";
import { coursesApi } from "@/lib/api";
import { BadgeStatut, MessageVide, Skeleton } from "@/components/ui";
import { formatDate } from "@/lib/utils";
import type { Course } from "@/types";

export default function CoursesPage() {
  const [dateFiltre, setDateFiltre] = useState(() => new Date().toISOString().split("T")[0]);
  const [statutFiltre, setStatutFiltre] = useState("");

  const { data, isLoading } = useQuery<{ data: { courses: Course[]; total: number } }>({
    queryKey: ["courses", dateFiltre, statutFiltre],
    queryFn: () => coursesApi.lister({
      date_course: dateFiltre || undefined,
      statut: statutFiltre || undefined,
    }),
  });

  const courses = data?.data?.courses ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Courses</h1>
          <p className="text-gray-500 text-sm mt-1">
            {data?.data?.total ?? 0} course(s) trouvée(s)
          </p>
        </div>
        <Link href="/importation" className="btn-primary text-sm">
          + Importer un programme
        </Link>
      </div>

      {/* Filtres */}
      <div className="card flex flex-wrap gap-4">
        <div className="flex items-center gap-2">
          <CalendarDays size={16} className="text-gray-400" />
          <input
            type="date"
            value={dateFiltre}
            onChange={(e) => setDateFiltre(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-hippo-300"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          <select
            value={statutFiltre}
            onChange={(e) => setStatutFiltre(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-hippo-300"
          >
            <option value="">Tous les statuts</option>
            <option value="programmée">Programmée</option>
            <option value="en_cours">En cours</option>
            <option value="terminée">Terminée</option>
            <option value="annulée">Annulée</option>
          </select>
        </div>
        <button
          onClick={() => { setDateFiltre(""); setStatutFiltre(""); }}
          className="btn-secondary text-xs py-1.5"
        >
          Réinitialiser
        </button>
      </div>

      {/* Tableau des courses */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
          </div>
        ) : courses.length === 0 ? (
          <div className="p-6">
            <MessageVide texte="Aucune course pour cette date. Importez un programme PMU'B." />
          </div>
        ) : (
          <table className="table-hippo">
            <thead>
              <tr>
                <th>N°</th>
                <th>Date</th>
                <th>Hippodrome</th>
                <th>Réunion</th>
                <th>Distance</th>
                <th>Partants</th>
                <th>Statut</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {courses.map((course) => (
                <tr key={course.id}>
                  <td className="font-bold text-hippo-700">C{course.numero}</td>
                  <td>{formatDate(course.date)}</td>
                  <td className="font-medium">{course.hippodrome}</td>
                  <td>{course.reunion}</td>
                  <td>{course.distance ? `${course.distance} m` : "—"}</td>
                  <td>{course.nombre_partants ?? "—"}</td>
                  <td><BadgeStatut statut={course.statut} /></td>
                  <td>
                    <Link
                      href={`/courses/${course.id}`}
                      className="text-xs text-hippo-600 hover:underline font-medium"
                    >
                      Voir →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

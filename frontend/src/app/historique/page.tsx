"use client";
/**
 * Page — Historique des prédictions vs résultats officiels
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { History, CheckCircle, Plus } from "lucide-react";
import { coursesApi, resultatsApi } from "@/lib/api";
import { BadgeStatut, MessageVide, Skeleton } from "@/components/ui";
import { formatDate } from "@/lib/utils";
import type { Course } from "@/types";

export default function HistoriquePage() {
  const [courseSelectionnee, setCourseSelectionnee] = useState<number | null>(null);
  const [classement, setClassement] = useState("");
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery<{ data: { courses: Course[] } }>({
    queryKey: ["courses-terminees"],
    queryFn: () => coursesApi.lister({ statut: "terminée" }),
  });

  const { data: coursesAvec } = useQuery<{ data: { courses: Course[] } }>({
    queryKey: ["courses-toutes"],
    queryFn: () => coursesApi.lister({}),
  });

  const mutation = useMutation({
    mutationFn: (data: { course_id: number; classement_officiel: number[] }) =>
      resultatsApi.enregistrer(data),
    onSuccess: () => {
      toast.success("Résultat enregistré avec succès !");
      queryClient.invalidateQueries({ queryKey: ["courses-terminees"] });
      setCourseSelectionnee(null);
      setClassement("");
    },
    onError: (err: any) =>
      toast.error(err.response?.data?.detail ?? "Erreur lors de l'enregistrement"),
  });

  const courses = coursesAvec?.data?.courses ?? [];
  const coursesTerminees = data?.data?.courses ?? [];

  function handleEnregistrer() {
    if (!courseSelectionnee) return;
    const ids = classement
      .split(",")
      .map((s) => parseInt(s.trim()))
      .filter((n) => !isNaN(n));
    if (ids.length < 1) {
      toast.error("Saisissez au moins un cheval_id");
      return;
    }
    mutation.mutate({ course_id: courseSelectionnee, classement_officiel: ids });
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <History size={24} className="text-hippo-600" /> Historique des résultats
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Enregistrez les arrivées officielles pour mesurer la précision du modèle
        </p>
      </div>

      {/* Formulaire d'enregistrement d'arrivée */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Plus size={18} className="text-hippo-600" />
          <h2 className="font-semibold text-gray-800">Enregistrer une arrivée officielle</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-gray-600 mb-1 block">Course</label>
            <select
              value={courseSelectionnee ?? ""}
              onChange={(e) => setCourseSelectionnee(Number(e.target.value) || null)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-hippo-300"
            >
              <option value="">Sélectionner une course...</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {formatDate(c.date)} — {c.hippodrome} R{c.reunion}C{c.numero}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 mb-1 block">
              Classement officiel <span className="text-gray-400">(IDs des chevaux séparés par virgule)</span>
            </label>
            <input
              value={classement}
              onChange={(e) => setClassement(e.target.value)}
              placeholder="Ex: 3, 7, 12, 1, 9 (1er, 2ème, 3ème...)"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-hippo-300"
            />
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <button
            onClick={handleEnregistrer}
            disabled={!courseSelectionnee || !classement || mutation.isPending}
            className="btn-primary"
          >
            <CheckCircle size={16} />
            {mutation.isPending ? "Enregistrement..." : "Enregistrer l'arrivée"}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          ⚠️ Une fois enregistré, le résultat verrouille automatiquement les pronostics existants
          pour garantir l'intégrité des données.
        </p>
      </div>

      {/* Liste des courses terminées */}
      <div className="card p-0 overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center gap-2">
          <History size={16} className="text-hippo-600" />
          <h2 className="font-semibold text-gray-800 text-sm">Courses terminées</h2>
          <span className="ml-auto text-xs text-gray-400">{coursesTerminees.length} course(s)</span>
        </div>
        {isLoading ? (
          <div className="p-6 space-y-3">
            {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
          </div>
        ) : coursesTerminees.length === 0 ? (
          <div className="p-6">
            <MessageVide texte="Aucune course terminée enregistrée" />
          </div>
        ) : (
          <table className="table-hippo">
            <thead>
              <tr>
                <th>Date</th>
                <th>Hippodrome</th>
                <th>Course</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {coursesTerminees.map((c) => (
                <tr key={c.id}>
                  <td>{formatDate(c.date)}</td>
                  <td className="font-medium">{c.hippodrome}</td>
                  <td>{c.reunion} — C{c.numero}</td>
                  <td><BadgeStatut statut={c.statut} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

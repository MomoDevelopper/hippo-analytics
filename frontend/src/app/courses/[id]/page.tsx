"use client";
/**
 * Page — Détail d'une course avec partants, prédiction et hypothèses
 */
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Brain, Trophy, BarChart3, AlertCircle } from "lucide-react";
import { coursesApi, predictionsApi, hypothesesApi } from "@/lib/api";
import {
  BadgeStatut, BadgeCategorie, NoteBar, MessageVide,
  Skeleton, Spinner, ErreurMessage,
} from "@/components/ui";
import { formatCote, formatPct, couleurNote } from "@/lib/utils";
import type { Course, Evaluation, Hypothese } from "@/types";

export default function DetailCoursePage() {
  const params = useParams();
  const courseId = Number(params.id);
  const queryClient = useQueryClient();
  const [onglet, setOnglet] = useState<"partants" | "prediction" | "hypotheses">("partants");

  // Détail de la course
  const { data: courseData, isLoading } = useQuery<{ data: Course }>({
    queryKey: ["course", courseId],
    queryFn: () => coursesApi.detail(courseId),
  });

  // Prédiction existante
  const { data: predData } = useQuery<{ data: any }>({
    queryKey: ["prediction", courseId],
    queryFn: () => predictionsApi.obtenir(courseId),
    retry: false,
  });

  // Hypothèses
  const { data: hypData } = useQuery<{ data: any }>({
    queryKey: ["hypotheses", courseId],
    queryFn: () => hypothesesApi.top(courseId),
    retry: false,
  });

  // Lancer une prédiction
  const mutation = useMutation({
    mutationFn: () => predictionsApi.lancer(courseId, 100000),
    onSuccess: () => {
      toast.success("Prédiction générée avec succès !");
      queryClient.invalidateQueries({ queryKey: ["prediction", courseId] });
      queryClient.invalidateQueries({ queryKey: ["hypotheses", courseId] });
      setOnglet("prediction");
    },
    onError: () => toast.error("Erreur lors de la prédiction"),
  });

  const course = courseData?.data;
  const prediction = predData?.data;
  const hypotheses: Hypothese[] = hypData?.data?.hypotheses ?? [];

  if (isLoading) return <div className="p-8"><Skeleton className="h-64 w-full" /></div>;
  if (!course) return <ErreurMessage message="Course introuvable" />;

  return (
    <div className="space-y-6">
      {/* En-tête de la course */}
      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <span className="text-2xl font-bold text-hippo-700">
                {course.reunion} — Course n°{course.numero}
              </span>
              <BadgeStatut statut={course.statut} />
            </div>
            <h1 className="text-xl font-bold text-gray-900">{course.hippodrome}</h1>
            <div className="flex flex-wrap gap-4 mt-2 text-sm text-gray-500">
              <span>📅 {new Date(course.date).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}</span>
              {course.distance && <span>📏 {course.distance} m</span>}
              {course.type_piste && <span>🏟️ Piste {course.type_piste}</span>}
              {course.partants && <span>🐎 {course.partants.length} partants</span>}
            </div>
            {course.conditions && (
              <p className="text-xs text-gray-400 mt-1">{course.conditions}</p>
            )}
          </div>

          {/* Bouton prédiction */}
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="btn-primary"
          >
            {mutation.isPending ? (
              <><Spinner size={16} /> Simulation en cours...</>
            ) : (
              <><Brain size={16} /> Lancer la prédiction</>
            )}
          </button>
        </div>
      </div>

      {/* Onglets */}
      <div className="flex gap-1 border-b border-gray-200">
        {(["partants", "prediction", "hypotheses"] as const).map((o) => (
          <button
            key={o}
            onClick={() => setOnglet(o)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              onglet === o
                ? "border-hippo-600 text-hippo-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {o === "partants" && "🐎 Partants"}
            {o === "prediction" && "🎯 Prédiction IA"}
            {o === "hypotheses" && "📋 Hypothèses"}
          </button>
        ))}
      </div>

      {/* Contenu des onglets */}
      {onglet === "partants" && (
        <div className="card p-0 overflow-hidden">
          {!course.partants?.length ? (
            <div className="p-6"><MessageVide texte="Aucun partant enregistré pour cette course" /></div>
          ) : (
            <table className="table-hippo">
              <thead>
                <tr>
                  <th>N°</th>
                  <th>Cheval</th>
                  <th>Jockey</th>
                  <th>Entraîneur</th>
                  <th>Musique</th>
                  <th>Cote</th>
                </tr>
              </thead>
              <tbody>
                {course.partants.map((p) => (
                  <tr key={p.id} className={p.non_partant ? "opacity-40 line-through" : ""}>
                    <td className="font-bold text-hippo-700 w-10">{p.numero}</td>
                    <td className="font-semibold">{p.cheval ?? "—"}</td>
                    <td className="text-gray-600">{p.jockey ?? "—"}</td>
                    <td className="text-gray-500 text-xs">{p.entraineur ?? "—"}</td>
                    <td>
                      <code className="text-xs bg-gray-100 px-1.5 py-0.5 rounded font-mono">
                        {p.musique ?? "—"}
                      </code>
                    </td>
                    <td className="font-medium">
                      {p.cote ? (
                        <span className={p.cote <= 3 ? "text-green-600 font-bold" : "text-gray-700"}>
                          {formatCote(p.cote)}
                        </span>
                      ) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {onglet === "prediction" && (
        <div className="space-y-4">
          {!prediction ? (
            <div className="card text-center py-10">
              <Brain size={40} className="text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 font-medium">Aucune prédiction disponible</p>
              <p className="text-gray-400 text-sm mt-1">
                Cliquez sur "Lancer la prédiction" pour générer les probabilités
              </p>
            </div>
          ) : (
            <>
              {/* Top 5 prédit */}
              <div className="card">
                <div className="flex items-center gap-2 mb-4">
                  <Trophy size={18} className="text-gold-500" />
                  <h2 className="font-semibold text-gray-800">Top 5 prédit</h2>
                  <span className="text-xs text-gray-400 ml-auto">{prediction.methode}</span>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {(prediction.top5_predit ?? []).map((chevalId: number, i: number) => {
                    const ev = (prediction.classement ?? []).find(
                      (e: Evaluation) => e.cheval_id === chevalId
                    );
                    return (
                      <div
                        key={chevalId}
                        className={`flex items-center gap-2 px-3 py-2 rounded-xl border-2 ${
                          i === 0 ? "border-gold-400 bg-yellow-50" :
                          i === 1 ? "border-gray-300 bg-gray-50" :
                          i === 2 ? "border-orange-300 bg-orange-50" :
                          "border-gray-200 bg-white"
                        }`}
                      >
                        <span className={`text-lg font-bold ${
                          i === 0 ? "text-gold-500" : i === 1 ? "text-gray-500" : i === 2 ? "text-orange-400" : "text-gray-400"
                        }`}>
                          {i + 1}{i === 0 ? "er" : "ème"}
                        </span>
                        <div>
                          <p className="text-sm font-semibold">{ev?.nom_cheval ?? `#${chevalId}`}</p>
                          <p className="text-xs text-gray-400">
                            N°{ev?.numero} · {formatPct(ev?.probabilite_victoire)}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Classement détaillé */}
              <div className="card p-0 overflow-hidden">
                <div className="px-5 py-3 border-b border-gray-100 flex items-center gap-2">
                  <BarChart3 size={16} className="text-hippo-600" />
                  <h2 className="font-semibold text-gray-800 text-sm">Classement par note</h2>
                </div>
                <table className="table-hippo">
                  <thead>
                    <tr>
                      <th>Rang</th>
                      <th>N°</th>
                      <th>Cheval</th>
                      <th>Note globale</th>
                      <th>Forme</th>
                      <th>Distance</th>
                      <th>Jockey</th>
                      <th>P(victoire)</th>
                      <th>Catégorie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(prediction.classement ?? []).map((ev: Evaluation) => (
                      <tr key={ev.partant_id}>
                        <td className="font-bold text-hippo-700 w-10">{ev.rang_predit}</td>
                        <td className="text-gray-500">{ev.numero}</td>
                        <td className="font-semibold">{ev.nom_cheval}</td>
                        <td>
                          <div className="flex items-center gap-2 min-w-[100px]">
                            <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  ev.note_globale >= 75 ? "bg-green-500" :
                                  ev.note_globale >= 60 ? "bg-blue-500" :
                                  ev.note_globale >= 45 ? "bg-yellow-500" : "bg-red-400"
                                }`}
                                style={{ width: `${ev.note_globale}%` }}
                              />
                            </div>
                            <span className={`text-xs font-bold ${couleurNote(ev.note_globale)}`}>
                              {ev.note_globale.toFixed(0)}
                            </span>
                          </div>
                        </td>
                        <td className="text-xs">{ev.note_forme.toFixed(0)}</td>
                        <td className="text-xs">{ev.note_distance.toFixed(0)}</td>
                        <td className="text-xs">{ev.note_jockey.toFixed(0)}</td>
                        <td className="font-medium text-hippo-700">
                          {formatPct(ev.probabilite_victoire)}
                        </td>
                        <td><BadgeCategorie categorie={ev.categorie} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      {onglet === "hypotheses" && (
        <div className="card p-0 overflow-hidden">
          {hypotheses.length === 0 ? (
            <div className="p-6">
              <MessageVide texte="Lancez d'abord une prédiction pour générer les hypothèses" />
            </div>
          ) : (
            <>
              <div className="px-5 py-3 border-b border-gray-100">
                <p className="text-sm text-gray-500">
                  Top {hypotheses.length} hypothèses de classement des 5 premiers
                  · sur {(100000).toLocaleString("fr-FR")} simulations Monte Carlo
                </p>
              </div>
              <table className="table-hippo">
                <thead>
                  <tr>
                    <th>Rang</th>
                    <th>Ordre estimé (1er → 5ème)</th>
                    <th>Probabilité</th>
                    <th>Occurrences</th>
                  </tr>
                </thead>
                <tbody>
                  {hypotheses.map((h) => (
                    <tr key={h.rang} className={h.rang === 1 ? "bg-yellow-50" : ""}>
                      <td className="font-bold text-hippo-700 w-12">#{h.rang}</td>
                      <td>
                        <div className="flex items-center gap-1">
                          {h.ordre.map((id, i) => (
                            <span key={id}>
                              <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${
                                i === 0 ? "bg-yellow-100 text-yellow-700" :
                                i === 1 ? "bg-gray-100 text-gray-600" :
                                i === 2 ? "bg-orange-100 text-orange-600" :
                                "bg-blue-50 text-blue-600"
                              }`}>
                                {id}
                              </span>
                              {i < 4 && <span className="text-gray-300 mx-0.5">→</span>}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <span className="font-semibold text-hippo-700">
                          {(h.probabilite * 100).toFixed(3)}%
                        </span>
                      </td>
                      <td className="text-gray-500 text-sm">
                        {h.occurrences.toLocaleString("fr-FR")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}
    </div>
  );
}

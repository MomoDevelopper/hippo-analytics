"use client";
/**
 * Page — Synchronisation autonome LONAB
 */
import { useQuery, useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { RefreshCw, Wifi, WifiOff, Clock, Download, Server } from "lucide-react";
import { syncApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import { Spinner } from "@/components/ui";
import type { SyncStatus } from "@/types";

export default function SynchronisationPage() {
  const { data, isLoading, refetch } = useQuery<{ data: SyncStatus }>({
    queryKey: ["sync-status"],
    queryFn: () => syncApi.statut(),
    refetchInterval: 30_000,
  });

  const mutation = useMutation({
    mutationFn: () => syncApi.lancer(),
    onSuccess: () => {
      toast.success("Synchronisation lancée ! Vérifiez le statut dans quelques instants.");
      setTimeout(() => refetch(), 5000);
    },
    onError: () => toast.error("Erreur lors du lancement de la synchronisation"),
  });

  const sync = data?.data;
  const estOk = sync?.statut === "succès";
  const estIndisponible = sync?.statut === "source_indisponible";

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <RefreshCw size={24} className="text-hippo-600" /> Synchronisation autonome
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Le système collecte automatiquement les programmes PMU Burkina Faso (LONAB)
          même lorsque vous n'êtes pas connecté.
        </p>
      </div>

      {/* Statut principal */}
      <div className={`card border-l-4 ${
        estOk ? "border-l-green-500 bg-green-50" :
        estIndisponible ? "border-l-orange-400 bg-orange-50" :
        sync?.statut === "jamais_executé" ? "border-l-gray-300 bg-gray-50" :
        "border-l-red-400 bg-red-50"
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {estOk ? (
              <Wifi size={28} className="text-green-500" />
            ) : (
              <WifiOff size={28} className={estIndisponible ? "text-orange-400" : "text-red-400"} />
            )}
            <div>
              <p className="font-semibold text-gray-800 text-lg">
                {sync?.statut === "jamais_executé" ? "En attente de la première synchronisation" :
                 estOk ? "Synchronisation active ✓" :
                 estIndisponible ? "Source LONAB temporairement indisponible" :
                 `Erreur : ${sync?.statut}`}
              </p>
              {sync?.erreur && (
                <p className="text-sm text-red-600 mt-0.5">⚠️ {sync.erreur}</p>
              )}
            </div>
          </div>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="btn-primary"
          >
            {mutation.isPending ? (
              <><Spinner size={16} /> En cours...</>
            ) : (
              <><RefreshCw size={16} /> Synchroniser maintenant</>
            )}
          </button>
        </div>
      </div>

      {/* Détails de synchronisation */}
      {sync && (
        <div className="grid grid-cols-2 gap-4">
          <div className="card">
            <div className="flex items-center gap-2 text-gray-500 mb-2">
              <Clock size={16} />
              <span className="text-sm font-medium">Dernière exécution</span>
            </div>
            <p className="text-lg font-bold text-gray-800">
              {sync.derniere_execution ? formatDateTime(sync.derniere_execution) : "Jamais"}
            </p>
          </div>
          <div className="card">
            <div className="flex items-center gap-2 text-gray-500 mb-2">
              <Download size={16} />
              <span className="text-sm font-medium">Fichiers récupérés</span>
            </div>
            <p className="text-lg font-bold text-gray-800">{sync.fichiers_recuperes}</p>
            <p className="text-xs text-gray-400">programmes archivés au total</p>
          </div>
          <div className="card">
            <div className="flex items-center gap-2 text-gray-500 mb-2">
              <RefreshCw size={16} />
              <span className="text-sm font-medium">Exécutions totales</span>
            </div>
            <p className="text-lg font-bold text-gray-800">{sync.executions_totales}</p>
          </div>
          <div className="card">
            <div className="flex items-center gap-2 text-gray-500 mb-2">
              <Clock size={16} />
              <span className="text-sm font-medium">Intervalle de sync</span>
            </div>
            <p className="text-lg font-bold text-gray-800">Toutes les {sync.intervalle_heures}h</p>
          </div>
        </div>
      )}

      {/* Source */}
      <div className="card">
        <div className="flex items-center gap-2 mb-3">
          <Server size={18} className="text-hippo-600" />
          <h2 className="font-semibold text-gray-800">Source de données</h2>
        </div>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">URL principale</span>
            <a href="https://lonab.bf" target="_blank" rel="noopener noreferrer"
               className="text-hippo-600 hover:underline font-medium">
              lonab.bf
            </a>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-100">
            <span className="text-gray-500">Type de collecte</span>
            <span className="text-gray-700">Téléchargement PDF automatique</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-500">Comportement hors-ligne</span>
            <span className="text-gray-700">Réessai automatique à l'intervalle suivant</span>
          </div>
        </div>
      </div>

      {/* Explication du mode autonome */}
      <div className="card bg-blue-50 border-blue-100">
        <h3 className="font-semibold text-blue-800 mb-2">🔄 Mode synchronisation autonome</h3>
        <p className="text-sm text-blue-700 mb-3">
          Même si vous ne vous connectez pas pendant plusieurs jours, le système continue à :
        </p>
        <ul className="text-sm text-blue-700 space-y-1.5">
          <li>✅ Rechercher les nouveaux programmes PMU'B sur LONAB</li>
          <li>✅ Télécharger et archiver les PDF de programmes</li>
          <li>✅ Préparer les données pour la prochaine analyse</li>
          <li>✅ Logger chaque tentative (succès ou indisponibilité)</li>
        </ul>
        <p className="text-xs text-blue-500 mt-3">
          À votre retour, vous retrouvez les programmes en attente de validation dans la section Importation.
        </p>
      </div>
    </div>
  );
}

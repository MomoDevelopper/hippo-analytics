"use client";
/**
 * En-tête de l'application avec indicateur de synchronisation.
 */
import { useQuery } from "@tanstack/react-query";
import { RefreshCw, Wifi, WifiOff } from "lucide-react";
import { syncApi } from "@/lib/api";
import { formatDateTime } from "@/lib/utils";
import type { SyncStatus } from "@/types";

export function Header() {
  const { data } = useQuery<{ data: SyncStatus }>({
    queryKey: ["sync-status"],
    queryFn: () => syncApi.statut(),
    refetchInterval: 60_000, // Rafraîchit toutes les minutes
  });

  const sync = data?.data;
  const estOk = sync?.statut === "succès" || sync?.statut === "jamais_executé";

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
      <div>
        <p className="text-sm text-gray-500">
          Analyse hippique — PMU Burkina Faso (LONAB)
        </p>
      </div>

      {/* Indicateur de synchronisation */}
      <div className="flex items-center gap-3">
        {sync && (
          <div className="flex items-center gap-2 text-xs text-gray-500">
            {estOk ? (
              <Wifi size={14} className="text-green-500" />
            ) : (
              <WifiOff size={14} className="text-red-400" />
            )}
            <span>
              Sync :{" "}
              {sync.statut === "jamais_executé"
                ? "en attente"
                : sync.derniere_execution
                  ? formatDateTime(sync.derniere_execution)
                  : "—"}
            </span>
          </div>
        )}

        <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-green-50 text-green-700 text-xs font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
          Système actif
        </div>
      </div>
    </header>
  );
}

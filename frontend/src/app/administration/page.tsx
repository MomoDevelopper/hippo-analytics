"use client";
/**
 * Page — Administration (entraînement IA, exports, gestion système)
 */
import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Settings, Brain, FileDown, AlertTriangle } from "lucide-react";
import { adminApi } from "@/lib/api";
import { Spinner } from "@/components/ui";

export default function AdministrationPage() {
  const entrainement = useMutation({
    mutationFn: (nb_jours: number) => adminApi.entrainerIA(nb_jours),
    onSuccess: () => toast.success("Entraînement lancé en arrière-plan"),
    onError: () => toast.error("Erreur lors du lancement"),
  });

  const exportExcel = useMutation({
    mutationFn: () => adminApi.exporterExcel(),
    onSuccess: (data) => toast.success(`Export généré : ${data.data.fichier}`),
    onError: () => toast.error("Erreur export Excel"),
  });

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Settings size={24} className="text-hippo-600" /> Administration
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Gestion du moteur de prédiction, exports et configuration système
        </p>
      </div>

      {/* Section IA */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Brain size={18} className="text-hippo-600" />
          <h2 className="font-semibold text-gray-800">Moteur de prédiction XGBoost</h2>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Entraînez le modèle XGBoost sur vos données historiques pour améliorer
          la précision des prédictions. Nécessite au minimum 50 courses avec résultats officiels.
        </p>
        <div className="flex flex-wrap gap-3">
          {[
            { label: "6 derniers mois", jours: 180 },
            { label: "1 an", jours: 365 },
            { label: "2 ans", jours: 730 },
          ].map((opt) => (
            <button
              key={opt.jours}
              onClick={() => entrainement.mutate(opt.jours)}
              disabled={entrainement.isPending}
              className="btn-primary text-sm"
            >
              {entrainement.isPending ? (
                <><Spinner size={14} /> Entraînement...</>
              ) : (
                <><Brain size={14} /> Entraîner sur {opt.label}</>
              )}
            </button>
          ))}
        </div>
        <div className="mt-4 p-3 bg-yellow-50 rounded-xl border border-yellow-100">
          <p className="text-xs text-yellow-700 flex items-start gap-1.5">
            <AlertTriangle size={14} className="shrink-0 mt-0.5" />
            Le modèle sera entraîné uniquement sur les données disponibles AVANT chaque course
            (pas de fuite de données). L'entraînement peut prendre plusieurs minutes.
          </p>
        </div>
      </div>

      {/* Exports */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <FileDown size={18} className="text-hippo-600" />
          <h2 className="font-semibold text-gray-800">Exports</h2>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-xl bg-gray-50 border border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-800">Historique des prédictions</p>
              <p className="text-xs text-gray-400">Toutes les prédictions vs résultats réels en Excel</p>
            </div>
            <button
              onClick={() => exportExcel.mutate()}
              disabled={exportExcel.isPending}
              className="btn-secondary text-sm"
            >
              {exportExcel.isPending ? <Spinner size={14} /> : <FileDown size={14} />}
              Exporter Excel
            </button>
          </div>
        </div>
      </div>

      {/* Informations système */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4">Informations système</h2>
        <div className="space-y-2 text-sm">
          {[
            ["Version", "HIPPO ANALYTICS 1.0.0"],
            ["Backend", "Python 3.11 + FastAPI"],
            ["Base de données", "PostgreSQL 15"],
            ["Moteur IA", "Scikit-learn + XGBoost"],
            ["Simulation", "Monte Carlo (Plackett-Luce)"],
            ["Extraction PDF", "PyMuPDF + Tesseract OCR"],
            ["Source principale", "LONAB — lonab.bf"],
          ].map(([label, valeur]) => (
            <div key={label} className="flex justify-between py-2 border-b border-gray-100 last:border-0">
              <span className="text-gray-500">{label}</span>
              <span className="font-medium text-gray-700">{valeur}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

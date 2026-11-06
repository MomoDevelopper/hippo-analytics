"use client";
/**
 * Page — Importation de programmes (PDF / Excel)
 */
import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import toast from "react-hot-toast";
import { Upload, FileText, FileSpreadsheet, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { programmesApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ResultatImport {
  message: string;
  fichier: string;
  taille_mo?: number;
  extraction?: {
    date: string | null;
    hippodrome: string | null;
    reunion: string | null;
    nb_courses: number;
    confiance: string;
  };
  action_requise?: string;
}

export default function ImportationPage() {
  const [dragOver, setDragOver] = useState(false);
  const [resultat, setResultat] = useState<ResultatImport | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const mutation = useMutation({
    mutationFn: (fichier: File) => {
      const estExcel = fichier.name.match(/\.xlsx?$/i);
      return estExcel
        ? programmesApi.importerExcel(fichier)
        : programmesApi.importerPdf(fichier);
    },
    onSuccess: (data) => {
      setResultat(data.data);
      toast.success("Fichier importé avec succès !");
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail ?? "Erreur lors de l'importation");
    },
  });

  function handleFichier(fichier: File) {
    setResultat(null);
    mutation.mutate(fichier);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const fichier = e.dataTransfer.files[0];
    if (fichier) handleFichier(fichier);
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Importation de programmes</h1>
        <p className="text-gray-500 text-sm mt-1">
          Importez le journal hippique PMU'B au format PDF ou Excel.
          Le système extrait automatiquement les données des partants.
        </p>
      </div>

      {/* Zone de dépôt */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all",
          dragOver
            ? "border-hippo-500 bg-hippo-50"
            : "border-gray-200 hover:border-hippo-300 hover:bg-gray-50"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.xlsx,.xls"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFichier(e.target.files[0])}
        />

        {mutation.isPending ? (
          <div className="space-y-3">
            <Loader2 size={48} className="text-hippo-500 animate-spin mx-auto" />
            <p className="text-hippo-600 font-medium">Analyse du programme en cours...</p>
            <p className="text-gray-400 text-sm">Extraction OCR et parsing LONAB</p>
          </div>
        ) : (
          <div className="space-y-3">
            <Upload size={48} className="text-gray-300 mx-auto" />
            <p className="text-gray-600 font-medium text-lg">
              Glissez votre fichier ici ou cliquez pour sélectionner
            </p>
            <p className="text-gray-400 text-sm">Formats acceptés : PDF · Excel (.xlsx)</p>
            <div className="flex justify-center gap-4 mt-4">
              <span className="flex items-center gap-1.5 text-sm text-gray-500 bg-red-50 px-3 py-1.5 rounded-lg">
                <FileText size={16} className="text-red-400" /> PDF (journal hippique)
              </span>
              <span className="flex items-center gap-1.5 text-sm text-gray-500 bg-green-50 px-3 py-1.5 rounded-lg">
                <FileSpreadsheet size={16} className="text-green-500" /> Excel (.xlsx)
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Résultat d'importation */}
      {resultat && (
        <div className="card space-y-4">
          <div className="flex items-start gap-3">
            <CheckCircle size={20} className="text-green-500 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-gray-800">{resultat.message}</p>
              <p className="text-sm text-gray-500">
                {resultat.fichier}
                {resultat.taille_mo && ` · ${resultat.taille_mo} Mo`}
              </p>
            </div>
          </div>

          {resultat.extraction && (
            <div className="bg-gray-50 rounded-xl p-4 space-y-2">
              <p className="text-sm font-medium text-gray-700 mb-3">📋 Données extraites</p>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Date</span>
                  <span className="font-medium">{resultat.extraction.date ?? "Non détectée"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Hippodrome</span>
                  <span className="font-medium">{resultat.extraction.hippodrome ?? "Non détecté"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Réunion</span>
                  <span className="font-medium">{resultat.extraction.reunion ?? "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Courses détectées</span>
                  <span className="font-medium">{resultat.extraction.nb_courses}</span>
                </div>
              </div>

              {/* Indicateur de confiance */}
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-500">Confiance d'extraction</span>
                  <span className={`font-bold ${
                    parseInt(resultat.extraction.confiance) >= 70 ? "text-green-600" :
                    parseInt(resultat.extraction.confiance) >= 40 ? "text-yellow-600" : "text-red-500"
                  }`}>
                    {resultat.extraction.confiance}
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      parseInt(resultat.extraction.confiance) >= 70 ? "bg-green-500" :
                      parseInt(resultat.extraction.confiance) >= 40 ? "bg-yellow-500" : "bg-red-400"
                    }`}
                    style={{ width: resultat.extraction.confiance }}
                  />
                </div>
              </div>
            </div>
          )}

          {resultat.action_requise && (
            <div className="flex items-start gap-2 text-sm text-yellow-700 bg-yellow-50 rounded-xl p-3">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <p>{resultat.action_requise}</p>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => setResultat(null)}
              className="btn-secondary text-sm"
            >
              Importer un autre fichier
            </button>
            <a href="/courses" className="btn-primary text-sm">
              Voir les courses →
            </a>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="card bg-blue-50 border-blue-100">
        <h3 className="font-semibold text-blue-800 mb-2 flex items-center gap-2">
          💡 Comment obtenir les programmes LONAB ?
        </h3>
        <ol className="text-sm text-blue-700 space-y-1.5 list-decimal list-inside">
          <li>Rendez-vous sur <strong>lonab.bf</strong> dans la section Programmes PMU'B</li>
          <li>Téléchargez le journal hippique PDF de la journée</li>
          <li>Importez-le ici — le système extrait automatiquement toutes les données</li>
          <li>Vérifiez les données extraites avant de les valider</li>
        </ol>
        <p className="text-xs text-blue-500 mt-3">
          ℹ️ La synchronisation autonome (toutes les 6h) télécharge automatiquement les nouveaux programmes.
        </p>
      </div>
    </div>
  );
}

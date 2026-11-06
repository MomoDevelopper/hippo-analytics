/**
 * Client API centralisé pour HIPPO ANALYTICS.
 * Toutes les requêtes vers le backend FastAPI passent par ce module.
 */
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_URL}/api`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ─── Programmes ───────────────────────────────
export const programmesApi = {
  lister: (params?: { date_debut?: string; date_fin?: string }) =>
    api.get("/programmes", { params }),
  importerPdf: (fichier: File) => {
    const formData = new FormData();
    formData.append("fichier", fichier);
    return api.post("/programmes/import/pdf", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  importerExcel: (fichier: File) => {
    const formData = new FormData();
    formData.append("fichier", fichier);
    return api.post("/programmes/import/excel", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ─── Courses ──────────────────────────────────
export const coursesApi = {
  lister: (params?: { date_course?: string; statut?: string }) =>
    api.get("/courses", { params }),
  detail: (id: number) => api.get(`/courses/${id}`),
  partants: (id: number) => api.get(`/courses/${id}/partants`),
};

// ─── Chevaux ──────────────────────────────────
export const chevauxApi = {
  lister: (params?: { nom?: string; page?: number }) =>
    api.get("/chevaux", { params }),
  fiche: (id: number) => api.get(`/chevaux/${id}`),
};

// ─── Jockeys ──────────────────────────────────
export const jockeysApi = {
  classement: (periode_jours = 90) =>
    api.get("/jockeys", { params: { periode_jours } }),
  fiche: (id: number) => api.get(`/jockeys/${id}`),
};

// ─── Entraîneurs ──────────────────────────────
export const entraineursApi = {
  classement: (periode_jours = 90) =>
    api.get("/entraineurs", { params: { periode_jours } }),
  fiche: (id: number) => api.get(`/entraineurs/${id}`),
};

// ─── Prédictions ──────────────────────────────
export const predictionsApi = {
  lancer: (courseId: number, nSimulations = 100000) =>
    api.post(`/predictions/${courseId}`, null, {
      params: { n_simulations: nSimulations },
      timeout: 120000, // 2 min pour les simulations
    }),
  obtenir: (courseId: number) => api.get(`/predictions/${courseId}`),
};

// ─── Hypothèses ───────────────────────────────
export const hypothesesApi = {
  top: (courseId: number) => api.get(`/hypotheses/${courseId}/top`),
  toutes: (courseId: number, top = 50) =>
    api.get(`/hypotheses/${courseId}`, { params: { top } }),
};

// ─── Résultats ────────────────────────────────
export const resultatsApi = {
  enregistrer: (data: {
    course_id: number;
    classement_officiel: number[];
    source?: string;
  }) => api.post("/resultats", data),
  obtenir: (courseId: number) => api.get(`/resultats/${courseId}`),
};

// ─── Statistiques ─────────────────────────────
export const statistiquesApi = {
  globales: () => api.get("/statistiques"),
  modele: (periode_jours = 30) =>
    api.get("/statistiques/modele", { params: { periode_jours } }),
};

// ─── Synchronisation ──────────────────────────
export const syncApi = {
  statut: () => api.get("/sync/status"),
  lancer: () => api.post("/sync/run"),
};

// ─── Administration ───────────────────────────
export const adminApi = {
  entrainerIA: (nb_jours = 365) =>
    api.post("/admin/ia/entrainer", null, { params: { nb_jours } }),
  exporterPdf: (courseId: number) =>
    api.post(`/admin/exports/pdf/${courseId}`),
  exporterExcel: () => api.post("/admin/exports/excel"),
};

export default api;

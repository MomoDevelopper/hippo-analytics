/**
 * Types TypeScript pour HIPPO ANALYTICS.
 */

export interface Course {
  id: number;
  date: string;
  reunion: string;
  numero: number;
  hippodrome: string;
  distance: number | null;
  type_piste: string | null;
  conditions: string | null;
  statut: string;
  partants?: Partant[];
  nombre_partants?: number;
}

export interface Partant {
  id: number;
  numero: number;
  cheval: string | null;
  cheval_id: number;
  jockey: string | null;
  jockey_id: number | null;
  entraineur: string | null;
  musique: string | null;
  cote: number | null;
  non_partant: boolean;
}

export interface Cheval {
  id: number;
  nom: string;
  age: number | null;
  sexe: string | null;
  robe: string | null;
  origine: string | null;
  proprietaire: string | null;
  naisseur: string | null;
  entraineur: { id: number; nom: string } | null;
  statistiques?: {
    sorties_analysees: number;
    victoires: number;
    places_top3: number;
    taux_victoire: number;
  };
  dernieres_performances?: Performance[];
}

export interface Performance {
  date: string;
  hippodrome: string | null;
  distance: number | null;
  place: number | null;
  partants: number | null;
  jockey: string | null;
  cote: number | null;
}

export interface Jockey {
  id: number;
  nom: string;
  nationalite: string | null;
  actif: boolean;
  rang?: number;
  courses?: number;
  victoires?: number;
  places_top3?: number;
  taux_victoire?: number;
  taux_top3?: number;
}

export interface Entraineur {
  id: number;
  nom: string;
  ecurie: string | null;
  actif: boolean;
  rang?: number;
  sorties?: number;
  victoires?: number;
  taux_victoire?: number;
}

export interface Evaluation {
  partant_id: number;
  cheval_id: number;
  numero: number;
  nom_cheval: string;
  note_globale: number;
  note_forme: number;
  note_distance: number;
  note_jockey: number;
  note_entraineur: number;
  note_regularite: number;
  probabilite_victoire: number;
  categorie: string | null;
  rang_predit: number;
}

export interface Hypothese {
  rang: number;
  ordre: number[];
  probabilite: number;
  occurrences: number;
}

export interface Prediction {
  course_id: number;
  pronostic_id?: number;
  top5_predit: number[];
  classement: Evaluation[];
  top_hypotheses?: Hypothese[];
  methode?: string;
  simulations?: number;
}

export interface StatistiquesGlobales {
  base_de_donnees: {
    total_courses: number;
    courses_terminees: number;
    total_chevaux: number;
    total_jockeys: number;
    total_entraineurs: number;
  };
  moteur_prediction: {
    pronostics_generes: number;
    courses_evaluables: number;
    precision: string;
  };
}

export interface SyncStatus {
  derniere_execution: string | null;
  statut: string;
  fichiers_recuperes: number;
  erreur: string | null;
  executions_totales: number;
  intervalle_heures: number;
  source: string;
}

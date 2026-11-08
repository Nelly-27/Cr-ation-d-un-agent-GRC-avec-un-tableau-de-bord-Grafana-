/**
 * Accès PostgreSQL en LECTURE SEULE (compte grc_reader). Requêtes fixes, paramétrées :
 * ni le modèle ni l'utilisateur ne peuvent injecter de SQL ici.
 */
import { Pool } from "pg";
import { settings } from "./config";

export interface RiskItem {
  title: string;
  url: string;
  source: "certfr" | "eurlex";
  risk_level: "faible" | "moyen" | "élevé" | "critique";
  risk_score: number;
  summary: string;
  rationale: string;
  published_at: string | null;
}

let pool: Pool | undefined;
const db = () => (pool ??= new Pool({ connectionString: settings.databaseUrl, max: 3 }));

const COLUMNS = "title, url, source, risk_level, risk_score, summary, rationale, published_at";
const WHEN = "coalesce(published_at, collected_at)";
// Fenêtre de la question « à traiter en priorité » : ce qui est récent et grave.
const PRIORITY_WINDOW_DAYS = 30;

async function rows(sql: string, params: unknown[]): Promise<RiskItem[]> {
  return (await db().query<RiskItem>(sql, params)).rows;
}

/** Question 1 : les risques cyber (CERT-FR) les plus graves, puis les plus récents. */
export const topCyberRisks = (limit = 5) =>
  rows(`SELECT ${COLUMNS} FROM items WHERE category = 'cyber' ORDER BY risk_score DESC, ${WHEN} DESC LIMIT $1`, [limit]);

/** Question 2 : les nouvelles réglementations (EUR-Lex) les plus pertinentes, puis les plus récentes. */
export const latestRegulations = (limit = 5) =>
  rows(`SELECT ${COLUMNS} FROM items WHERE category = 'reglementaire' ORDER BY risk_score DESC, ${WHEN} DESC LIMIT $1`, [limit]);

/** Question 3 : toutes sources, niveau élevé ou critique, sur les 30 derniers jours. */
export const priorityRisks = (limit = 5) =>
  rows(
    `SELECT ${COLUMNS} FROM items
     WHERE risk_score >= 3 AND ${WHEN} >= now() - make_interval(days => $2)
     ORDER BY risk_score DESC, ${WHEN} DESC LIMIT $1`,
    [limit, PRIORITY_WINDOW_DAYS],
  );

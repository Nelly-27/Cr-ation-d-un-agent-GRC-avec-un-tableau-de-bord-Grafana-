import { pool } from "./db";

export interface NewsArticle {
  id: number;
  source: string;
  title: string;
  link: string;
  published_at: string | null;
  ai_summary: string | null;
  criticality: string | null;
  category: string | null;
  justification: string | null;
}

export async function getLatestNews(limit = 30): Promise<NewsArticle[]> {
  const safeLimit = Math.min(Math.max(limit, 1), 100);

  const result = await pool.query(
    `SELECT
       id, source, title, link, published_at,
       ai_summary, criticality, category, justification
     FROM public.actualites
     ORDER BY created_at DESC
     LIMIT $1`,
    [safeLimit]
  );

  return result.rows;
}

export async function getCriticalityStats() {
  const result = await pool.query(
    `SELECT
       COALESCE(criticality, 'Non classée') AS criticite,
       COUNT(*)::int AS nombre
     FROM public.actualites
     GROUP BY criticality
     ORDER BY nombre DESC`
  );

  return result.rows;
}

export async function getEurLexNews(limit = 15): Promise<NewsArticle[]> {
  const result = await pool.query(
    `SELECT
       id, source, title, link, published_at,
       ai_summary, criticality, category, justification
     FROM public.actualites
     WHERE LOWER(source) LIKE '%eur%'
     ORDER BY created_at DESC
     LIMIT $1`,
    [limit]
  );

  return result.rows;
}
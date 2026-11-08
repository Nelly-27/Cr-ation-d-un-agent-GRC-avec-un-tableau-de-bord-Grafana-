/**
 * Réponses construites sans LLM, à partir de PostgreSQL et du MCP Grafana.
 * Utilisées quand aucun modèle n'est configuré : le chatbot reste démontrable sans clé.
 */
import type { DashboardRef } from "./mcp";
import type { RiskItem } from "./db";

export type Intent = "cyber" | "reglementation" | "priorite" | "aide";

export const SUGGESTED_QUESTIONS = [
  "Quels sont les risques cyber les plus importants ?",
  "Quelles nouvelles réglementations devons-nous surveiller ?",
  "Quels risques devons-nous traiter en priorité ?",
] as const;

const normalize = (s: string) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

export function detectIntent(question: string): Intent {
  const q = normalize(question);
  if (/priorit|traiter|d'abord|urgent/.test(q)) return "priorite";
  if (/reglement|legislat|loi\b|directive|eur-?lex|surveiller|conformite/.test(q)) return "reglementation";
  if (/cyber|vulnerab|menace|cert|attaque|faille|risque/.test(q)) return "cyber";
  return "aide";
}

const SOURCE_LABEL = { certfr: "CERT-FR", eurlex: "EUR-Lex" } as const;

function formatDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "long", year: "numeric" }) : "date inconnue";
}

function itemLines(items: RiskItem[]): string[] {
  return items.map(
    (it, i) =>
      `${i + 1}. **${it.risk_level.toUpperCase()}** – ${it.title} (${SOURCE_LABEL[it.source]}, ${formatDate(it.published_at)})\n` +
      // Sans description (fréquent sur EUR-Lex), le résumé n'est que le titre : inutile de le répéter.
      (it.summary && it.summary !== it.title ? `   ${it.summary}\n` : "") +
      `   _Pourquoi ce niveau :_ ${it.rationale} [${i + 1}]`,
  );
}

// Des crochets dans un titre (« [MàJ] … ») casseraient le lien Markdown [titre](url).
const linkText = (title: string) => title.replace(/\[/g, "(").replace(/\]/g, ")");

function sourcesBlock(items: RiskItem[], dashboard: DashboardRef | null): string[] {
  const lines = ["", "**Sources**", ...items.map((it, i) => `[${i + 1}] [${linkText(it.title)}](${it.url})`)];
  if (dashboard) lines.push(`Tableau de bord (trouvé via MCP Grafana) : [${dashboard.title}](${dashboard.url})`);
  return lines;
}

export interface AnswerContext {
  items: RiskItem[];
  dashboard: DashboardRef | null;
  counts: Record<string, number> | null;
}

const INTROS: Record<Exclude<Intent, "aide">, string> = {
  cyber: "Voici les risques cyber les plus importants publiés par le CERT-FR, du plus grave au moins grave :",
  reglementation: "Voici les nouveaux textes européens à surveiller, du plus pertinent au moins pertinent pour la sécurité de l'information :",
  priorite: "Voici les risques à traiter en priorité : niveau élevé ou critique, publiés ces 30 derniers jours (CERT-FR et EUR-Lex) :",
};

export function buildAnswer(intent: Intent, ctx: AnswerContext): string {
  if (intent === "aide") {
    return ["Je réponds aux questions de veille GRC, par exemple :", ...SUGGESTED_QUESTIONS.map((q) => `- ${q}`)].join("\n");
  }
  if (ctx.items.length === 0) {
    return "Aucune donnée correspondante pour l'instant. L'agent collecte au démarrage puis toutes les heures : réessayez après la première collecte.";
  }
  const lines = [INTROS[intent], "", ...itemLines(ctx.items)];
  if (ctx.counts && Object.keys(ctx.counts).length > 0) {
    const order = ["critique", "élevé", "moyen", "faible"];
    lines.push("", `Vue d'ensemble (lue dans Grafana via MCP) : ${order.map((l) => `${ctx.counts?.[l] ?? 0} ${l}`).join(", ")}.`);
  }
  lines.push(...sourcesBlock(ctx.items, ctx.dashboard));
  lines.push("", "_Réponse générée sans modèle de langage (mode par défaut). Configurez LLM_BASE_URL et LLM_MODEL pour des réponses rédigées par un LLM._");
  return lines.join("\n");
}

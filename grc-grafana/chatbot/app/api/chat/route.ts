import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import {
  convertToModelMessages,
  createUIMessageStream,
  createUIMessageStreamResponse,
  isStepCount,
  streamText,
  tool,
  type UIMessage,
} from "ai";
import { z } from "zod";
import { buildAnswer, detectIntent } from "@/lib/answers";
import { llmEnabled, settings } from "@/lib/config";
import { latestRegulations, priorityRisks, topCyberRisks } from "@/lib/db";
import { countsByLevel, findDashboard, MCP_TOOLS, openGrafanaMcp } from "@/lib/mcp";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_TOOL_STEPS = 8;

const SYSTEM_PROMPT = `Tu es l'assistant de veille GRC d'une organisation française. Tu réponds en français, de façon concise.
Tes données viennent de deux sources officielles collectées par l'agent : avis et alertes du CERT-FR (risques cyber) et actes publiés sur EUR-Lex (réglementation).
Outils :
- risques_cyber_majeurs, nouvelles_reglementations, risques_prioritaires : lisent la base PostgreSQL (lecture seule) ;
- outils MCP Grafana (search_dashboards, get_dashboard_summary, query_sql avec datasourceUid "grc-postgres", …) : lisent le tableau de bord Grafana et ses données.
Règles impératives :
1. N'affirme rien qui ne vienne pas d'un outil. Si les données manquent, dis-le.
2. CHAQUE réponse se termine par une section « Sources » listant les liens officiels (champ url) des éléments cités, au format [titre](url).
3. Ajoute le lien du tableau de bord Grafana, trouvé avec search_dashboards (préfixe ${settings.grafanaPublicUrl}).
4. Pour « en priorité », privilégie les niveaux critique et élevé les plus récents, et explique pourquoi.`;

const dbTools = {
  risques_cyber_majeurs: tool({
    description: "Risques cyber (CERT-FR) les plus graves puis les plus récents, avec résumé, niveau et lien officiel.",
    inputSchema: z.object({ limite: z.number().int().min(1).max(20).default(5) }),
    execute: ({ limite }) => topCyberRisks(limite),
  }),
  nouvelles_reglementations: tool({
    description: "Nouveaux actes européens (EUR-Lex) les plus pertinents puis les plus récents, avec résumé, niveau et lien officiel.",
    inputSchema: z.object({ limite: z.number().int().min(1).max(20).default(5) }),
    execute: ({ limite }) => latestRegulations(limite),
  }),
  risques_prioritaires: tool({
    description: "Risques de niveau élevé ou critique des 30 derniers jours, toutes sources, du plus grave au moins grave.",
    inputSchema: z.object({ limite: z.number().int().min(1).max(20).default(5) }),
    execute: ({ limite }) => priorityRisks(limite),
  }),
};

function lastUserText(messages: UIMessage[]): string {
  const last = [...messages].reverse().find((m) => m.role === "user");
  return (last?.parts ?? []).map((p) => (p.type === "text" ? p.text : "")).join(" ");
}

async function answerWithLlm(messages: UIMessage[]): Promise<Response> {
  const mcp = await openGrafanaMcp().catch(() => null);
  const mcpTools = mcp
    ? Object.fromEntries(Object.entries(await mcp.tools()).filter(([name]) => (MCP_TOOLS as readonly string[]).includes(name)))
    : {};
  const provider = createOpenAICompatible({ name: "llm", baseURL: settings.llm.baseURL, apiKey: settings.llm.apiKey || undefined });
  const result = streamText({
    model: provider.chatModel(settings.llm.model),
    system: SYSTEM_PROMPT + (mcp ? "" : "\n(Le serveur MCP Grafana est injoignable : utilise seulement les outils PostgreSQL.)"),
    messages: await convertToModelMessages(messages),
    tools: { ...dbTools, ...mcpTools },
    stopWhen: isStepCount(MAX_TOOL_STEPS),
    onFinish: () => mcp?.close(),
    onError: () => mcp?.close(),
  });
  return result.toUIMessageStreamResponse({
    onError: (err) => `Erreur du modèle (${settings.llm.model}) : ${err instanceof Error ? err.message : String(err)}`,
  });
}

async function answerWithoutLlm(messages: UIMessage[]): Promise<Response> {
  const intent = detectIntent(lastUserText(messages));
  const fetchItems = { cyber: topCyberRisks, reglementation: latestRegulations, priorite: priorityRisks, aide: async () => [] }[intent];
  const items = await fetchItems();
  let dashboard = null;
  let counts = null;
  const mcp = await openGrafanaMcp().catch(() => null);
  if (mcp) {
    try {
      [dashboard, counts] = await Promise.all([findDashboard(mcp), countsByLevel(mcp)]);
    } finally {
      await mcp.close();
    }
  }
  const text = buildAnswer(intent, { items, dashboard, counts }) + (mcp ? "" : "\n\n_(Serveur MCP Grafana injoignable : réponse construite depuis PostgreSQL seulement.)_");
  const stream = createUIMessageStream({
    execute: ({ writer }) => {
      writer.write({ type: "text-start", id: "answer" });
      writer.write({ type: "text-delta", id: "answer", delta: text });
      writer.write({ type: "text-end", id: "answer" });
    },
  });
  return createUIMessageStreamResponse({ stream });
}

export async function POST(req: Request): Promise<Response> {
  const { messages } = (await req.json()) as { messages: UIMessage[] };
  return llmEnabled() ? answerWithLlm(messages) : answerWithoutLlm(messages);
}

/** Indique à l'interface le mode actif (LLM ou sans LLM). */
export function GET(): Response {
  return Response.json({ llm: llmEnabled() ? settings.llm.model : null });
}

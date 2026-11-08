/** Client du serveur MCP Grafana (transport HTTP « streamable »). */
import { createMCPClient, type MCPClient } from "@ai-sdk/mcp";
import { settings } from "./config";

/** Outils MCP utiles au chatbot : lecture des dashboards et des requêtes autorisées. */
export const MCP_TOOLS = [
  "search_dashboards",
  "get_dashboard_summary",
  "get_dashboard_panel_queries",
  "list_datasources",
  "query_sql",
  "generate_deeplink",
] as const;

export const openGrafanaMcp = (): Promise<MCPClient> =>
  createMCPClient({ transport: { type: "http", url: settings.mcpUrl } }) as Promise<MCPClient>;

/** Texte renvoyé par un outil MCP, décodé en JSON quand c'est possible. */
export function mcpResult<T>(result: object): T | string {
  const content = "content" in result ? result.content : undefined;
  const parts = Array.isArray(content) ? content : [];
  const text = parts.map((p: { type?: string; text?: string }) => (p.type === "text" ? p.text ?? "" : "")).join("");
  try {
    return JSON.parse(text) as T;
  } catch {
    return text;
  }
}

export interface DashboardRef {
  title: string;
  url: string;
}

/** Retrouve le dashboard de veille via MCP (et non en dur) : prouve que la connexion MCP fonctionne. */
export async function findDashboard(client: MCPClient): Promise<DashboardRef | null> {
  const found = mcpResult<{ dashboards?: { title: string; url: string }[] }>(
    await client.callTool({ name: "search_dashboards", arguments: { query: "Veille GRC" } }),
  );
  const first = typeof found === "string" ? undefined : found.dashboards?.[0];
  return first ? { title: first.title, url: `${settings.grafanaPublicUrl}${first.url}` } : null;
}

/** Compte des risques par criticité, lu à travers Grafana (query_sql sur la source en lecture seule). */
export async function countsByLevel(client: MCPClient): Promise<Record<string, number>> {
  const res = mcpResult<{ rows?: { risk_level: string; total: number }[] }>(
    await client.callTool({
      name: "query_sql",
      arguments: { datasourceUid: "grc-postgres", query: "SELECT risk_level, count(*) AS total FROM items GROUP BY risk_level" },
    }),
  );
  return Object.fromEntries((typeof res === "string" ? [] : res.rows ?? []).map((r) => [r.risk_level, Number(r.total)]));
}

/** Configuration lue dans l'environnement (.env à la racine, ou variables Docker). */
import { config as loadDotenv } from "dotenv";
import { resolve } from "node:path";

// En local (npm run dev), le .env est à la racine du dépôt ; dans Docker les variables sont injectées.
loadDotenv({ path: resolve(process.cwd(), "..", ".env"), quiet: true });

const env = (name: string, fallback = ""): string => (process.env[name] ?? "").trim() || fallback;

export const settings = {
  llm: {
    baseURL: env("LLM_BASE_URL").replace(/\/+$/, ""),
    apiKey: env("LLM_API_KEY"),
    // Le chatbot peut utiliser un modèle différent de l'agent (souvent plus doué pour les outils).
    model: env("CHAT_MODEL") || env("LLM_MODEL"),
  },
  mcpUrl: env("MCP_GRAFANA_URL", `http://localhost:${env("MCP_PORT", "8000")}/mcp`),
  grafanaPublicUrl: env("GRAFANA_PUBLIC_URL", `http://localhost:${env("GRAFANA_PORT", "3300")}`),
  databaseUrl: env(
    "DATABASE_URL",
    `postgresql://${env("POSTGRES_READER_USER", "grc_reader")}:${env("POSTGRES_READER_PASSWORD", "change-me-reader")}` +
      `@localhost:${env("POSTGRES_PORT", "5433")}/${env("POSTGRES_DB", "grc")}`,
  ),
};

export const llmEnabled = (): boolean => Boolean(settings.llm.baseURL && settings.llm.model);

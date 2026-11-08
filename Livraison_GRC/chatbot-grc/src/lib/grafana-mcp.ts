import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

export async function callGrafanaTool(
  toolName: string,
  args: Record<string, unknown> = {}
) {
  const uvxPath = process.env.MCP_UVX_PATH;
  const grafanaUrl = process.env.GRAFANA_URL;
  const token = process.env.GRAFANA_SERVICE_ACCOUNT_TOKEN;

  if (!uvxPath || !grafanaUrl || !token) {
    throw new Error("Configuration MCP Grafana incomplète.");
  }

  const transport = new StdioClientTransport({
    command: uvxPath,
    args: [
      "mcp-grafana",
      "--enabled-tools",
      "search,datasource,dashboard,folder,runpanelquery",
      "--disable-write",
      "--usage-stats=disabled",
    ],
    env: {
      ...process.env as Record<string, string>,
      GRAFANA_URL: grafanaUrl,
      GRAFANA_SERVICE_ACCOUNT_TOKEN: token,
    },
    stderr: "pipe",
  });

  const client = new Client({
    name: "chatbot-grc",
    version: "1.0.0",
  });

  try {
    await client.connect(transport);

    const result = await client.callTool({
      name: toolName,
      arguments: args,
    });

    return result;
  } finally {
    await client.close();
  }
}
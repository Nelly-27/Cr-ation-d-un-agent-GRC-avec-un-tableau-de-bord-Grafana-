import { NextResponse } from "next/server";
import { callGrafanaTool } from "@/lib/grafana-mcp";

export const runtime = "nodejs";

export async function GET() {
  try {
    const result = await callGrafanaTool("search_dashboards", {
      query: "Dashboard GRC - Veille réglementaire",
    });

    return NextResponse.json({ success: true, result });
  } catch (error) {
    console.error("Erreur MCP Grafana:", error);

    return NextResponse.json(
      { success: false, error: "Connexion MCP Grafana impossible." },
      { status: 500 }
    );
  }
}
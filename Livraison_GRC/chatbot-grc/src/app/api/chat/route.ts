
import { NextResponse } from "next/server";
import { getLatestNews, getCriticalityStats } from "@/lib/news";
import { callGrafanaTool } from "@/lib/grafana-mcp";

export const runtime = "nodejs";
export const maxDuration = 300;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const question = String(body.question || "").trim();

    if (!question || question.length > 1000) {
      return NextResponse.json(
        { error: "Question vide ou trop longue." },
        { status: 400 }
      );
    }

    // Récupération des données PostgreSQL
    const [articles, stats] = await Promise.all([
      getLatestNews(5),
      getCriticalityStats(),
    ]);

    // Lecture des indicateurs Grafana via MCP
    const [totalResult, criticalityResult] = await Promise.all([
      callGrafanaTool("run_panel_query", {
        uid: process.env.GRAFANA_DASHBOARD_UID,
        panelId: 61,
      }),
      callGrafanaTool("run_panel_query", {
        uid: process.env.GRAFANA_DASHBOARD_UID,
        panelId: 60,
      }),
    ]);

    const normalizedQuestion = question.toLowerCase();

let filteredArticles = articles;

if (
  normalizedQuestion.includes("réglementation") ||
  normalizedQuestion.includes("réglementations") ||
  normalizedQuestion.includes("réglementaire")
) {
  filteredArticles = articles.filter(
    (article) => article.source?.toLowerCase().includes("eur-lex")
  );
} else if (
  normalizedQuestion.includes("cyber") ||
  normalizedQuestion.includes("vulnérabilité") ||
  normalizedQuestion.includes("vulnérabilités")
) {
  filteredArticles = articles.filter(
    (article) => article.source?.toLowerCase().includes("cert-fr")
  );
}

const context = {
  articles: filteredArticles.map((article) => ({
    source: article.source,
    title: article.title,
    link: article.link,
    published_at: article.published_at,
    ai_summary: (article.ai_summary || "").slice(0, 400),
    criticality: article.criticality,
    category: article.category,
  })),
  statistics: stats,
  grafana: {
    total: totalResult,
    criticality: criticalityResult,
  },
};

    const ollamaResponse = await fetch(
      `${process.env.OLLAMA_URL}/api/chat`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: process.env.OLLAMA_MODEL || "qwen2.5:3b",
          stream: false,
          messages: [
            {
              role: "system",
              content: `Tu es un assistant spécialisé en gouvernance, risques et conformité (GRC) et cybersécurité.

Tu dois répondre en français, de façon claire et professionnelle.

RÈGLES :
- Utilise exclusivement les données fournies dans le contexte.
- Ne crée jamais de risque, réglementation, date ou source.
- Pour chaque actualité citée, indique son titre, sa criticité et son URL exacte.
- Distingue les faits des recommandations.
- Si les données sont insuffisantes, indique-le clairement.
- Pour les questions sur les réglementations, utilise exclusivement les actualités dont la source est EUR-Lex.
- Ne présente jamais une alerte CERT-FR comme une réglementation.
- Si aucune actualité EUR-Lex pertinente n'est disponible, indique clairement que les données sont insuffisantes.
- Pour les questions sur les vulnérabilités et les alertes cyber, utilise les actualités CERT-FR.
- Pour les priorités, prends en compte la criticité enregistrée en base et ne l'augmente jamais artificiellement.
- Ne confonds jamais une recommandation de traitement avec une information provenant directement d'une source.
- Pour les alertes de cybersécurité, privilégie CERT-FR.
- Ne prétends pas qu'une actualité est critique si sa criticité enregistrée est différente.
- Si aucune actualité de la source EUR-Lex n'est fournie, réponds : « Les données disponibles ne permettent pas d'identifier de nouvelle réglementation à surveiller. »
- N'utilise jamais une actualité CERT-FR pour répondre à une question sur les réglementations.
- Ne transforme jamais une vulnérabilité informatique en réglementation.
- Termine par une courte section « Sources » avec les liens utiles.`,
            },
            {
              role: "user",
              content: `Question : ${question}

Données disponibles :
${JSON.stringify(context)}`,
            },
          ],
          options: { temperature: 0.2, num_predict: 300, num_ctx: 4096,
	 },
        }),
        signal: AbortSignal.timeout(300000),
      }
    );

    if (!ollamaResponse.ok) {
      throw new Error(`Ollama HTTP ${ollamaResponse.status}`);
    }

    const aiData = await ollamaResponse.json();
    const answer = aiData.message?.content;

    if (!answer) {
      throw new Error("Ollama n'a retourné aucune réponse.");
    }

    return NextResponse.json({
      success: true,
      answer,
      articleCount: articles.length,
    });
  } catch (error) {
    console.error("Erreur chatbot:", error);

    return NextResponse.json(
      { error: "Impossible de générer la réponse. Vérifie PostgreSQL, MCP et Ollama." },
      { status: 500 }
    );
  }
}

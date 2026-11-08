import { describe, expect, it } from "vitest";
import { buildAnswer, detectIntent, SUGGESTED_QUESTIONS } from "./answers";
import type { RiskItem } from "./db";
import { mcpResult } from "./mcp";

const item = (over: Partial<RiskItem> = {}): RiskItem => ({
  title: "Vulnérabilité dans OpenSSH",
  url: "https://www.cert.cyber.gouv.fr/alerte/CERTFR-2026-ALE-001/",
  source: "certfr",
  risk_level: "critique",
  risk_score: 4,
  summary: "Une vulnérabilité est activement exploitée.",
  rationale: "Règle : vulnérabilité signalée comme exploitée.",
  published_at: "2026-11-05T00:00:00Z",
  ...over,
});

describe("detectIntent", () => {
  it("reconnaît les trois questions du TP", () => {
    expect(SUGGESTED_QUESTIONS.map(detectIntent)).toEqual(["cyber", "reglementation", "priorite"]);
  });
  it("tolère les variantes sans accent", () => {
    expect(detectIntent("quelles reglementations surveiller")).toBe("reglementation");
    expect(detectIntent("bonjour")).toBe("aide");
  });
});

describe("buildAnswer", () => {
  const dashboard = { title: "Veille GRC", url: "http://localhost:3300/d/grc-veille" };

  it("cite chaque élément avec son lien officiel et le dashboard trouvé via MCP", () => {
    const text = buildAnswer("cyber", { items: [item()], dashboard, counts: { critique: 1, élevé: 2 } });
    expect(text).toContain("[1] [Vulnérabilité dans OpenSSH](https://www.cert.cyber.gouv.fr/alerte/CERTFR-2026-ALE-001/)");
    expect(text).toContain("[Veille GRC](http://localhost:3300/d/grc-veille)");
    expect(text).toContain("1 critique, 2 élevé, 0 moyen, 0 faible");
  });

  it("neutralise les crochets d'un titre pour garder un lien valide", () => {
    const text = buildAnswer("cyber", { items: [item({ title: "[MàJ] Faille" })], dashboard: null, counts: null });
    expect(text).toContain("[1] [(MàJ) Faille](https://");
  });

  it("dit clairement qu'il n'y a pas encore de données", () => {
    expect(buildAnswer("priorite", { items: [], dashboard: null, counts: null })).toMatch(/Aucune donnée/);
  });
});

describe("mcpResult", () => {
  it("décode le JSON renvoyé par un outil MCP", () => {
    expect(mcpResult<{ a: number }>({ content: [{ type: "text", text: '{"a":1}' }] })).toEqual({ a: 1 });
    expect(mcpResult({ content: [{ type: "text", text: "pas du json" }] })).toBe("pas du json");
  });
});

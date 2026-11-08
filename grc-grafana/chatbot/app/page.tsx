"use client";

import { useChat } from "@ai-sdk/react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { SUGGESTED_QUESTIONS } from "@/lib/answers";
import { RichText } from "./RichText";

type Part = { type: string; text?: string; toolName?: string; state?: string };

/** Nom lisible d'un outil appelé par le modèle (outils MCP : « dynamic-tool »). */
function toolLabel(part: Part): string | null {
  if (part.type === "dynamic-tool") return `MCP Grafana · ${part.toolName}`;
  if (part.type.startsWith("tool-")) return `PostgreSQL · ${part.type.slice(5)}`;
  return null;
}

export default function ChatPage() {
  const { messages, sendMessage, status, error } = useChat();
  const [input, setInput] = useState("");
  const [model, setModel] = useState<string | null | undefined>(undefined);
  const bottom = useRef<HTMLDivElement>(null);
  const busy = status === "submitted" || status === "streaming";

  useEffect(() => {
    fetch("/api/chat").then((r) => r.json()).then((d) => setModel(d.llm)).catch(() => setModel(null));
  }, []);
  // Accolades obligatoires : scrollIntoView renvoie une Promise dans les navigateurs récents,
  // et React interpréterait toute valeur renvoyée comme une fonction de nettoyage.
  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const ask = (text: string) => {
    if (!text.trim() || busy) return;
    sendMessage({ text });
    setInput("");
  };
  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    ask(input);
  };

  return (
    <main className="shell">
      <header>
        <h1>Assistant de veille GRC</h1>
        <p className="mode">
          Données : CERT-FR et EUR-Lex → PostgreSQL → Grafana (MCP) ·{" "}
          {model === undefined ? "…" : model ? <>modèle <code>{model}</code></> : "mode sans LLM"}
        </p>
      </header>

      <section className="thread" aria-live="polite">
        {messages.length === 0 && (
          <div className="empty">
            <p>Posez une question, ou choisissez-en une :</p>
            {SUGGESTED_QUESTIONS.map((q) => (
              <button key={q} className="suggestion" onClick={() => ask(q)} disabled={busy}>{q}</button>
            ))}
          </div>
        )}
        {messages.map((m) => (
          <article key={m.id} className={`msg ${m.role}`}>
            {(m.parts as Part[]).map((part, i) => {
              const label = toolLabel(part);
              if (label) return <span key={i} className="tool">{label}</span>;
              if (part.type === "text" && part.text) return <RichText key={i} text={part.text} />;
              return null;
            })}
          </article>
        ))}
        {status === "submitted" && <p className="pending">Recherche dans les données…</p>}
        {error && <p className="error">Erreur : {error.message}</p>}
        <div ref={bottom} />
      </section>

      <form onSubmit={onSubmit}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Votre question…" aria-label="Votre question" />
        <button type="submit" disabled={busy || !input.trim()}>Envoyer</button>
      </form>
      {messages.length > 0 && (
        <nav className="quick">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button key={q} onClick={() => ask(q)} disabled={busy}>{q}</button>
          ))}
        </nav>
      )}
    </main>
  );
}

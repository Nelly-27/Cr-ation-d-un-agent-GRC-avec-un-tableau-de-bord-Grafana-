
"use client";

import { useState } from "react";

const suggestions = [
  "Quels sont les risques cyber les plus importants ?",
  "Quelles nouvelles réglementations devons-nous surveiller ?",
  "Quels risques devons-nous traiter en priorité ?",
];

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendQuestion(text: string) {
    const cleanQuestion = text.trim();

    if (!cleanQuestion || loading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", content: cleanQuestion },
    ]);
    setQuestion("");
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: cleanQuestion }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Une erreur est survenue.");
      }

      setMessages((previous) => [
        ...previous,
        { role: "assistant", content: data.answer },
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Impossible de contacter le chatbot."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900 px-6 py-5">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">
              GRC Intelligence
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              Assistant IA de veille cyber et réglementaire
            </p>
          </div>
          <span className="rounded-full border border-emerald-700 bg-emerald-950 px-3 py-1 text-xs text-emerald-400">
            ● Assistant local
          </span>
        </div>
      </header>

      <section className="mx-auto flex max-w-5xl flex-col px-4 py-8">
        <div className="mb-8 rounded-xl border border-slate-800 bg-slate-900 p-6">
          <h2 className="text-xl font-semibold">
            Bienvenue sur votre assistant GRC
          </h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Interrogez les actualités de cybersécurité et les évolutions
            réglementaires collectées par notre agent de veille. Les réponses
            s'appuient sur PostgreSQL, Grafana et un modèle IA local.
          </p>

          <div className="mt-5 grid gap-3 md:grid-cols-3">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => sendQuestion(suggestion)}
                disabled={loading}
                className="rounded-lg border border-slate-700 bg-slate-800 p-4 text-left text-sm transition hover:border-blue-500 hover:bg-slate-700 disabled:opacity-50"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        <div className="mb-5 min-h-64 space-y-4">
          {messages.length === 0 && (
            <div className="py-12 text-center text-sm text-slate-500">
              Sélectionnez une question ou saisissez votre propre demande.
            </div>
          )}

          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[90%] whitespace-pre-wrap rounded-xl p-4 text-sm leading-7 ${
                  message.role === "user"
                    ? "bg-blue-700 text-white"
                    : "border border-slate-700 bg-slate-900 text-slate-200"
                }`}
              >
                <div className="mb-2 text-xs font-semibold opacity-70">
                  {message.role === "user" ? "VOUS" : "ASSISTANT GRC"}
                </div>
                {message.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="rounded-xl border border-slate-700 bg-slate-900 p-4 text-sm text-blue-300">
              Analyse des actualités et génération de la réponse en cours...
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-800 bg-red-950 p-4 text-sm text-red-300">
              {error}
            </div>
          )}
        </div>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            sendQuestion(question);
          }}
          className="sticky bottom-4 flex gap-3 rounded-xl border border-slate-700 bg-slate-900 p-3 shadow-xl"
        >
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Posez votre question sur les risques GRC..."
            maxLength={1000}
            disabled={loading}
            className="min-w-0 flex-1 bg-transparent px-3 text-sm text-white outline-none placeholder:text-slate-500"
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Envoyer
          </button>
        </form>

        <footer className="mt-6 text-center text-xs text-slate-500">
          EPITA — Projet GRC 2026 · Next.js · Grafana MCP · PostgreSQL · Ollama
        </footer>
      </section>
    </main>
  );
}

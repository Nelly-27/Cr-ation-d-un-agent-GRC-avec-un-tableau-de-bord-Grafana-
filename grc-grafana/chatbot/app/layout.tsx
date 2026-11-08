import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Assistant de veille GRC",
  description: "Chatbot connecté au MCP Grafana et à PostgreSQL : risques cyber et réglementation, avec sources.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}

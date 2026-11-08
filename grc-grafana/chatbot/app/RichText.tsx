import { Fragment, type ReactNode } from "react";

/**
 * Rendu minimal du Markdown produit par le chatbot : liens [titre](url), **gras**, _italique_,
 * listes. Pas de HTML brut : le texte du modèle n'est jamais injecté tel quel dans la page.
 */
// L'italique _…_ exige une frontière de mot : « LLM_BASE_URL » reste intact.
const INLINE = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)|\*\*([^*]+)\*\*|(?<!\w)_([^_]+)_(?!\w)|(https?:\/\/[^\s)]+)/g;

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(INLINE)) {
    if (m.index > last) out.push(text.slice(last, m.index));
    const key = `${m.index}`;
    if (m[1]) out.push(<a key={key} href={m[2]} target="_blank" rel="noreferrer">{m[1]}</a>);
    else if (m[3]) out.push(<strong key={key}>{m[3]}</strong>);
    else if (m[4]) out.push(<em key={key}>{m[4]}</em>);
    else if (m[5]) out.push(<a key={key} href={m[5]} target="_blank" rel="noreferrer">{m[5]}</a>);
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function RichText({ text }: { text: string }) {
  return (
    <div className="rich">
      {text.split("\n").map((line, i) => {
        const heading = /^#{1,4}\s+(.*)$/.exec(line);
        if (heading) return <p key={i} className="heading">{inline(heading[1])}</p>;
        if (!line.trim()) return <div key={i} className="gap" />;
        const indented = /^\s{2,}/.test(line) || /^\s*[-*]\s/.test(line);
        return (
          <p key={i} className={indented ? "indent" : undefined}>
            {inline(line.replace(/^\s*[-*]\s/, "• ").trim()).map((n, j) => <Fragment key={j}>{n}</Fragment>)}
          </p>
        );
      })}
    </div>
  );
}

import DOMPurify from "dompurify";

export interface ConceptConfig {
  title: string;
  blurb: string;
  /** docs.activegraph.ai/concepts/<slug>/ — null when no dedicated concept page exists. */
  docsSlug: string | null;
}

const DOCS_BASE = "https://docs.activegraph.ai/concepts";

export const CONCEPTS = {
  relations: {
    title: "Relations",
    blurb:
      "Typed, directed edges between objects on the graph. A relation has a type, an id, and optional data — and in ActiveGraph the relation type itself can carry behavior, not just connect two nodes.",
    docsSlug: "relations",
  },
  patches: {
    title: "Patches",
    blurb:
      "Proposed mutations to an object's data. A behavior proposes a patch against an expected version; the runtime applies it or rejects it. Every patch is recorded in the event log.",
    docsSlug: "patches",
  },
  tools: {
    title: "Tools",
    blurb:
      "External capabilities a behavior can call — HTTP, shell, queries, MCP. Each call emits a tool.requested and a tool.responded event carrying the tool name, latency, cost, and cache status.",
    docsSlug: null,
  },
  failures: {
    title: "Failures",
    blurb:
      "When a behavior raises, a tool errors, or a patch is rejected, the runtime records the failure with a reason instead of crashing the run — keeping the graph consistent and replayable.",
    docsSlug: "failure-model",
  },
  events: {
    title: "Events",
    blurb:
      "The event log is the source of truth. Every object, relation, patch, behavior, and tool call is an append-only event — the trace is this log, in order.",
    docsSlug: "events",
  },
} as const satisfies Record<string, ConceptConfig>;

export type ConceptKey = keyof typeof CONCEPTS;

export function docsUrl(slug: string): string {
  return `${DOCS_BASE}/${slug}/`;
}

export const CONCEPTS_INDEX_URL = `${DOCS_BASE}/`;

/**
 * Fetch a concept's documentation page and return sanitized inner HTML of its
 * <article>. docs.activegraph.ai sends `access-control-allow-origin: *`, so this
 * runs directly in the browser. MkDocs chrome (edit button, permalinks) is
 * stripped before sanitizing.
 */
export async function fetchConceptDoc(slug: string): Promise<string> {
  const res = await fetch(docsUrl(slug));
  if (!res.ok) throw new Error(`Docs responded ${res.status}`);
  const html = await res.text();
  const doc = new DOMParser().parseFromString(html, "text/html");
  const article = doc.querySelector("article");
  if (!article) throw new Error("No article element in docs page");
  article
    .querySelectorAll(
      "a.md-content__button, a.headerlink, .md-source-file, .md-feedback, nav, script, style"
    )
    .forEach((el) => el.remove());
  return DOMPurify.sanitize(article.innerHTML, { USE_PROFILES: { html: true } });
}

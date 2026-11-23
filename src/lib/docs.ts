export type DocEntry = {
  slug: string;
  title: string;
  summary: string;
  group: string;
};

// Curated manifest: the order here is the order readers see. Titles are kept
// short for the sidebar, the documents themselves still carry their own H1.
export const DOCS: DocEntry[] = [
  {
    slug: "product-specification",
    title: "Product specification",
    summary: "What the studio is, who it serves and every requirement behind it.",
    group: "Start here",
  },
  {
    slug: "feature-registry",
    title: "Feature registry",
    summary: "Every surface, its real state and the evidence that backs it.",
    group: "Start here",
  },
  {
    slug: "roadmap",
    title: "Release roadmap",
    summary: "What shipped, what is next and what is still deliberately absent.",
    group: "Start here",
  },
  {
    slug: "architecture",
    title: "Architecture",
    summary: "How the studio, the engine and storage fit together.",
    group: "Engineering",
  },
  {
    slug: "api-contract",
    title: "API contract",
    summary: "Every route the studio calls, with request and response shapes.",
    group: "Engineering",
  },
  {
    slug: "source-ingestion",
    title: "Source ingestion",
    summary: "Link resolution, host allowlists, rights checks and media validation.",
    group: "Engineering",
  },
  {
    slug: "deployment-runbook",
    title: "Deployment runbook",
    summary: "Local install, Docker and the single-service Render setup.",
    group: "Running it",
  },
  {
    slug: "oauth-setup",
    title: "Connecting social accounts",
    summary: "Provider apps, scopes and redirect URIs, step by step.",
    group: "Running it",
  },
  {
    slug: "security-and-privacy",
    title: "Security and privacy",
    summary: "Token encryption, access control, retention and rights rules.",
    group: "Running it",
  },
  {
    slug: "website",
    title: "Website and design system",
    summary: "Design tokens, layout rules and the readability floor.",
    group: "Reference",
  },
  {
    slug: "upstream-evaluation",
    title: "Upstream evaluation",
    summary: "How established clipping tools were studied before building.",
    group: "Reference",
  },
];

const markdown = import.meta.glob("/docs/*.md", {
  query: "?raw",
  import: "default",
}) as Record<string, () => Promise<string>>;

export function docBySlug(slug: string | undefined): DocEntry | undefined {
  if (!slug) return undefined;
  return DOCS.find((doc) => doc.slug === slug);
}

export async function loadDoc(slug: string): Promise<string> {
  const loader = markdown[`/docs/${slug}.md`];
  if (!loader) throw new Error(`Unknown document: ${slug}`);
  return loader();
}

export function docGroups(): { group: string; docs: DocEntry[] }[] {
  const groups: { group: string; docs: DocEntry[] }[] = [];
  for (const doc of DOCS) {
    const existing = groups.find((g) => g.group === doc.group);
    if (existing) existing.docs.push(doc);
    else groups.push({ group: doc.group, docs: [doc] });
  }
  return groups;
}

export function docNeighbours(slug: string): { prev?: DocEntry; next?: DocEntry } {
  const index = DOCS.findIndex((doc) => doc.slug === slug);
  if (index < 0) return {};
  return { prev: DOCS[index - 1], next: DOCS[index + 1] };
}

export function headingId(text: string): string {
  return text
    .toLowerCase()
    .replace(/[`*_~]/g, "")
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

export type Headings = { level: 2 | 3; text: string; id: string }[];

// Pulls the h2/h3 outline out of the raw markdown for the on-page contents.
export function outlineOf(source: string): Headings {
  const headings: Headings = [];
  let inFence = false;
  for (const line of source.split("\n")) {
    if (line.trimStart().startsWith("```")) {
      inFence = !inFence;
      continue;
    }
    if (inFence) continue;
    const match = /^(#{2,3})\s+(.*)$/.exec(line);
    if (!match) continue;
    const text = match[2].replace(/#+\s*$/, "").trim();
    headings.push({ level: match[1].length === 2 ? 2 : 3, text, id: headingId(text) });
  }
  return headings;
}

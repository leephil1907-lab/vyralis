import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowLeft, ArrowRight, ArrowUpRight, BookOpen, ChevronRight, FileText,
  Search, Sparkles,
} from "lucide-react";
import {
  DOCS, docBySlug, docGroups, docNeighbours, headingId, loadDoc, outlineOf,
} from "../lib/docs";
import type { Headings } from "../lib/docs";

const REPO_DOCS = "https://github.com/leephil1907-lab/vyralis/blob/main/docs";

function flatten(children: ReactNode): string {
  if (typeof children === "string" || typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(flatten).join("");
  if (children && typeof children === "object" && "props" in children) {
    return flatten((children as { props: { children?: ReactNode } }).props.children);
  }
  return "";
}

// Docs cross-reference each other with relative .md links; keep those inside the
// app instead of dumping the reader onto GitHub. Anything else stays a normal
// link, and external links open in a new tab.
function DocLink({ href = "", children }: { href?: string; children?: ReactNode }) {
  const relative = /^(\.\/)?([a-z0-9][a-z0-9-]*)\.md(#[^)]*)?$/i.exec(href);
  if (relative) {
    return <Link to={`/docs/${relative[2].toLowerCase()}`}>{children}</Link>;
  }
  if (/^https?:\/\//.test(href)) {
    return <a href={href} target="_blank" rel="noreferrer">{children}</a>;
  }
  return <a href={href}>{children}</a>;
}

function Markdown({ source }: { source: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ href, children }) => <DocLink href={href}>{children}</DocLink>,
        h1: ({ children }) => <h1 className="doc-h1">{children}</h1>,
        h2: ({ children }) => <h2 id={headingId(flatten(children))}>{children}</h2>,
        h3: ({ children }) => <h3 id={headingId(flatten(children))}>{children}</h3>,
        img: ({ src, alt }) => <img className="doc-image" src={src} alt={alt ?? ""} loading="lazy" />,
        table: ({ children }) => <div className="doc-table-wrap"><table>{children}</table></div>,
      }}
    >
      {source}
    </ReactMarkdown>
  );
}

function Sidebar({ active, query, onQuery }: { active?: string; query: string; onQuery: (value: string) => void }) {
  const groups = docGroups();
  const filtered = query.trim()
    ? groups
        .map((g) => ({
          group: g.group,
          docs: g.docs.filter((d) =>
            (d.title + " " + d.summary + " " + d.slug).toLowerCase().includes(query.toLowerCase())),
        }))
        .filter((g) => g.docs.length)
    : groups;

  return (
    <aside className="docs-aside">
      <div className="docs-search">
        <Search size={14} />
        <input
          value={query}
          onChange={(e) => onQuery(e.target.value)}
          placeholder="Filter documents"
          aria-label="Filter documents"
        />
      </div>
      <Link className="docs-home-link" to="/docs">
        <BookOpen size={15} /> <span>All documents</span>
        <small>{DOCS.length}</small>
      </Link>
      {filtered.map((g) => (
        <div className="docs-nav-group" key={g.group}>
          <div className="docs-nav-label">{g.group}</div>
          {g.docs.map((doc) => (
            <Link
              key={doc.slug}
              to={`/docs/${doc.slug}`}
              className={"docs-nav-item" + (doc.slug === active ? " active" : "")}
            >
              <span>{doc.title}</span>
            </Link>
          ))}
        </div>
      ))}
      {!filtered.length && <p className="docs-empty">No document matches “{query}”.</p>}
    </aside>
  );
}

export default function DocsPage() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const entry = docBySlug(slug);
  const [source, setSource] = useState("");
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [contents, setContents] = useState<Headings>([]);

  useEffect(() => {
    let cancelled = false;
    if (!entry) { setSource(""); setContents([]); return; }
    setError("");
    loadDoc(entry.slug)
      .then((text) => {
        if (cancelled) return;
        setSource(text);
        setContents(outlineOf(text));
        window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setSource("");
        setContents([]);
        setError(e instanceof Error ? e.message : "This document could not be loaded.");
      });
    return () => { cancelled = true; };
  }, [entry]);

  const neighbours = useMemo(() => (entry ? docNeighbours(entry.slug) : {}), [entry]);

  if (!entry) {
    return (
      <div className="page-content">
        <div className="empty-panel">
          <div className="empty-icon"><FileText size={23} /></div>
          <h3>That document doesn’t exist</h3>
          <p>{slug ? `“${slug}” is not one of the ${DOCS.length} published documents.` : "Pick a document from the index."}</p>
          <button className="button-primary" onClick={() => navigate("/docs")}>
            Browse documentation <ArrowRight size={15} />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-content">
      <div className="page-heading docs-heading">
        <div>
          <div className="eyebrow"><BookOpen size={13} />DOCUMENTATION / {entry.group.toUpperCase()}</div>
          <h1>{entry.title}</h1>
          <p>{entry.summary}</p>
        </div>
        <div className="heading-action">
          <a className="button-secondary" href={`${REPO_DOCS}/${entry.slug}.md`} target="_blank" rel="noreferrer">
            View source on GitHub <ArrowUpRight size={14} />
          </a>
        </div>
      </div>

      <div className="docs-shell">
        <Sidebar active={entry.slug} query={query} onQuery={setQuery} />

        <div className="docs-main">
          {contents.length > 2 && (
            <details className="docs-contents" open>
              <summary><Sparkles size={13} /> On this page</summary>
              <ol>
                {contents.map((h) => (
                  <li key={h.id} className={h.level === 3 ? "sub" : ""}>
                    <a href={`#${h.id}`}>{h.text}</a>
                  </li>
                ))}
              </ol>
            </details>
          )}

          <article className="doc-prose">
            {error && <div className="notice notice-error">{error}</div>}
            {!source && !error && <p className="docs-loading">Loading “{entry.title}”…</p>}
            {source && <Markdown source={source} />}
          </article>

          <nav className="docs-pager" aria-label="Document navigation">
            {neighbours.prev ? (
              <Link to={`/docs/${neighbours.prev.slug}`} className="docs-pager-link">
                <ArrowLeft size={15} />
                <span><small>Previous</small>{neighbours.prev.title}</span>
              </Link>
            ) : <span />}
            {neighbours.next ? (
              <Link to={`/docs/${neighbours.next.slug}`} className="docs-pager-link next">
                <span><small>Next</small>{neighbours.next.title}</span>
                <ArrowRight size={15} />
              </Link>
            ) : <span />}
          </nav>
        </div>
      </div>
    </div>
  );
}

export function DocsIndex() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const groups = docGroups();
  const visible = groups
    .map((g) => ({
      group: g.group,
      docs: g.docs.filter((d) =>
        (d.title + " " + d.summary).toLowerCase().includes(query.toLowerCase())),
    }))
    .filter((g) => g.docs.length);

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow"><BookOpen size={13} />DOCUMENTATION</div>
          <h1>The manual, <em>in the open.</em></h1>
          <p>
            Every claim this studio makes has a document behind it: how imports are
            validated, how ranking works, how tokens are encrypted, how to deploy it.
          </p>
        </div>
        <div className="heading-action">
          <button className="button-primary" onClick={() => navigate("/create")}>
            Start clipping <ArrowRight size={15} />
          </button>
        </div>
      </div>

      <div className="toolbar">
        <div className="search-box">
          <Search size={15} />
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search the documentation" />
        </div>
        <span className="quiet-count">{visible.reduce((n, g) => n + g.docs.length, 0)} documents</span>
      </div>

      {visible.map((g) => (
        <section className="docs-index-group" key={g.group}>
          <div className="section-title"><div><span className="micro-label">{g.group.toUpperCase()}</span></div></div>
          <div className="docs-index-grid">
            {g.docs.map((doc) => (
              <Link className="docs-card" key={doc.slug} to={`/docs/${doc.slug}`}>
                <div className="docs-card-top"><FileText size={16} /><ChevronRight size={15} /></div>
                <h3>{doc.title}</h3>
                <p>{doc.summary}</p>
              </Link>
            ))}
          </div>
        </section>
      ))}

      {!visible.length && (
        <div className="empty-panel">
          <div className="empty-icon"><Search size={23} /></div>
          <h3>No document matches “{query}”</h3>
          <p>Try a shorter term, such as “oauth”, “deploy” or “captions”.</p>
        </div>
      )}
    </div>
  );
}

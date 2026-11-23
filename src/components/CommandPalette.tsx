import { useEffect, useMemo, useRef, useState } from "react";
import type { LucideIcon } from "lucide-react";
import { ArrowRight, CornerDownLeft, Search } from "lucide-react";

export type Command = {
  id: string;
  label: string;
  hint?: string;
  group: string;
  icon: LucideIcon;
  keywords?: string;
  run: () => void;
};

// Small, predictable matcher: prefix matches on the label rank first, then any
// match in label, hint, group or keywords. No fuzzy library, no surprises.
function score(command: Command, query: string): number {
  const q = query.trim().toLowerCase();
  if (!q) return 1;
  const label = command.label.toLowerCase();
  if (label.startsWith(q)) return 100;
  if (label.includes(q)) return 70;
  const haystack = `${command.hint ?? ""} ${command.group} ${command.keywords ?? ""}`.toLowerCase();
  if (haystack.includes(q)) return 40;
  return 0;
}

export default function CommandPalette({
  open,
  onClose,
  commands,
}: {
  open: boolean;
  onClose: () => void;
  commands: Command[];
}) {
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const input = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const results = useMemo(() => {
    return commands
      .map((command) => ({ command, rank: score(command, query) }))
      .filter((entry) => entry.rank > 0)
      .sort((a, b) => b.rank - a.rank)
      .map((entry) => entry.command);
  }, [commands, query]);

  useEffect(() => {
    if (!open) return;
    setQuery("");
    setCursor(0);
    const id = window.setTimeout(() => input.current?.focus(), 20);
    return () => window.clearTimeout(id);
  }, [open]);

  useEffect(() => {
    setCursor(0);
  }, [query]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        setCursor((c) => (results.length ? (c + 1) % results.length : 0));
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        setCursor((c) => (results.length ? (c - 1 + results.length) % results.length : 0));
      } else if (event.key === "Enter") {
        const chosen = results[cursor];
        if (chosen) {
          event.preventDefault();
          onClose();
          chosen.run();
        }
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, results, cursor, onClose]);

  useEffect(() => {
    if (!open) return;
    const node = listRef.current?.querySelector<HTMLElement>(`[data-index="${cursor}"]`);
    node?.scrollIntoView({ block: "nearest" });
  }, [cursor, open]);

  if (!open) return null;

  let lastGroup = "";

  return (
    <div className="palette-scrim" role="presentation" onMouseDown={onClose}>
      <div
        className="palette"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="palette-input">
          <Search size={16} />
          <input
            ref={input}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Jump to a page, a document or an action…"
            aria-label="Search commands"
            autoComplete="off"
          />
          <kbd>ESC</kbd>
        </div>

        <div className="palette-results" ref={listRef} role="listbox" aria-label="Commands">
          {results.map((command, index) => {
            const header = command.group !== lastGroup ? command.group : "";
            lastGroup = command.group;
            const Icon = command.icon;
            return (
              <div key={command.id}>
                {header && <div className="palette-group">{header}</div>}
                <button
                  type="button"
                  role="option"
                  aria-selected={index === cursor}
                  data-index={index}
                  className={"palette-item" + (index === cursor ? " active" : "")}
                  onMouseEnter={() => setCursor(index)}
                  onClick={() => { onClose(); command.run(); }}
                >
                  <Icon size={16} />
                  <span className="palette-label">{command.label}</span>
                  {command.hint && <span className="palette-hint">{command.hint}</span>}
                  {index === cursor && <ArrowRight size={14} className="palette-go" />}
                </button>
              </div>
            );
          })}
          {!results.length && (
            <p className="palette-empty">Nothing matches “{query}”. Try “captions”, “docs” or “connections”.</p>
          )}
        </div>

        <div className="palette-footer">
          <span><kbd>↑</kbd><kbd>↓</kbd> move</span>
          <span><CornerDownLeft size={12} /> open</span>
          <span><kbd>⌘</kbd><kbd>K</kbd> toggle</span>
        </div>
      </div>
    </div>
  );
}

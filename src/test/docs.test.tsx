import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LandingPage from "../pages/LandingPage";
import DocsPage, { DocsIndex } from "../pages/DocsPage";
import { DOCS, docGroups, loadDoc, outlineOf } from "../lib/docs";

// The frontend talks to the API with plain fetch; these tests only need the app
// to render, so every call resolves to an honest empty workspace.
function mockApi() {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    const body = url.includes("/api/health")
      ? { status: "ok", version: "test", capabilities: [] }
      : url.includes("/api/assets")
        ? []
        : {};
    return { ok: true, status: 200, json: async () => body } as unknown as Response;
  }));
}

beforeEach(mockApi);
afterEach(() => vi.unstubAllGlobals());

describe("documentation content", () => {
  it("publishes every manifest entry from a real file", async () => {
    expect(DOCS).toHaveLength(11);
    expect(docGroups().map((group) => group.group)).toEqual([
      "Start here", "Engineering", "Running it", "Reference",
    ]);
    for (const doc of DOCS) {
      const source = await loadDoc(doc.slug);
      expect(source.length).toBeGreaterThan(200);
      expect(source.trimStart().startsWith("#")).toBe(true);
    }
  });

  it("extracts an outline without reading fenced code", () => {
    const headings = outlineOf("# Title\n\n## Real heading\n\n```\n## not a heading\n```\n\n### Nested one\n");
    expect(headings.map((h) => h.text)).toEqual(["Real heading", "Nested one"]);
    expect(headings[0].id).toBe("real-heading");
  });

  it("fails loudly for a document that does not exist", async () => {
    await expect(loadDoc("nope")).rejects.toThrow(/Unknown document/);
  });
});

describe("landing page", () => {
  it("offers the link entry point and routes to the studio", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);
    expect(screen.getByRole("heading", { level: 1, name: /Creativity/i })).toBeInTheDocument();
    expect(screen.getByLabelText("Paste a video link")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Start clipping/i })).toBeInTheDocument();
    // Docs must be an internal page now, not a raw .md link on GitHub.
    const docsLinks = screen.getAllByRole("link", { name: "Docs" });
    expect(docsLinks.some((link) => link.getAttribute("href") === "/docs")).toBe(true);
  });

  it("rejects a value that is not a URL instead of navigating", async () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);
    const input = screen.getByLabelText("Paste a video link");
    const user = (await import("@testing-library/user-event")).default.setup();
    await user.type(input, "not a link");
    await user.click(screen.getByRole("button", { name: /Start clipping/i }));
    expect(await screen.findByText(/include https:\/\//i)).toBeInTheDocument();
  });
});

describe("documentation pages", () => {
  it("lists every document with its group", () => {
    render(<MemoryRouter initialEntries={["/docs"]}><Routes><Route path="/docs" element={<DocsIndex />} /></Routes></MemoryRouter>);
    expect(screen.getByRole("heading", { level: 1, name: /manual/i })).toBeInTheDocument();
    for (const doc of DOCS) {
      expect(screen.getByRole("link", { name: new RegExp(doc.title, "i") })).toBeInTheDocument();
    }
    expect(screen.getByText("11 documents")).toBeInTheDocument();
  });

  it("renders a real document with its markdown intact", async () => {
    render(
      <MemoryRouter initialEntries={["/docs/architecture"]}>
        <Routes><Route path="/docs/:slug" element={<DocsPage />} /></Routes>
      </MemoryRouter>,
    );
    expect(screen.getByRole("heading", { level: 1, name: "Architecture" })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("article")).toBeInTheDocument(), { timeout: 4000 });
    const article = screen.getByRole("article");
    await waitFor(() => expect(within(article).getAllByRole("heading", { level: 2 }).length).toBeGreaterThan(2), { timeout: 4000 });
    // Sidebar still lists siblings while a document is open.
    expect(screen.getByRole("link", { name: /Deployment runbook/i })).toBeInTheDocument();
  });

  it("shows a real not-found state for an unknown slug", () => {
    render(
      <MemoryRouter initialEntries={["/docs/not-a-doc"]}>
        <Routes><Route path="/docs/:slug" element={<DocsPage />} /></Routes>
      </MemoryRouter>,
    );
    expect(screen.getByText(/doesn’t exist/i)).toBeInTheDocument();
  });
});

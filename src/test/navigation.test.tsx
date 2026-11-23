import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import App from "../App";

// Every API call resolves to an honest empty workspace so the shell renders
// without a backend.
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

describe("studio shell", () => {
  it("renders the navigation including documentation", () => {
    render(<MemoryRouter initialEntries={["/studio"]}><App /></MemoryRouter>);
    expect(screen.getByRole("link", { name: /Documentation/i })).toHaveAttribute("href", "/docs");
    expect(screen.getByRole("link", { name: /Create clips/i })).toHaveAttribute("href", "/create");
    // The shortcut hint is only honest if the palette exists; both are checked below.
    expect(screen.getByRole("button", { name: /Open command palette/i })).toBeInTheDocument();
  });

  it("opens the command palette with ⌘K and jumps to a document", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/studio"]}><App /></MemoryRouter>);

    await user.keyboard("{Meta>}k{/Meta}");
    const dialog = await screen.findByRole("dialog", { name: /Command palette/i });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText("Go to")).toBeInTheDocument();
    expect(screen.getByText("Read")).toBeInTheDocument();

    const field = screen.getByLabelText("Search commands");
    await user.type(field, "architecture");
    await user.keyboard("{Enter}");

    // Palette closes and the lazy documentation route renders the real file.
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(await screen.findByRole("heading", { level: 1, name: "Architecture" }, { timeout: 4000 })).toBeInTheDocument();
  });

  it("closes the palette on Escape without navigating", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/studio"]}><App /></MemoryRouter>);
    await user.keyboard("{Control>}k{/Control}");
    await screen.findByRole("dialog", { name: /Command palette/i });
    await user.keyboard("{Escape}");
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.getByText(/Make every moment/i)).toBeInTheDocument();
  });

  it("keeps the palette honest when nothing matches", async () => {
    const user = userEvent.setup();
    render(<MemoryRouter initialEntries={["/studio"]}><App /></MemoryRouter>);
    await user.keyboard("{Meta>}k{/Meta}");
    await user.type(screen.getByLabelText("Search commands"), "zzzz");
    expect(screen.getByText(/Nothing matches/i)).toBeInTheDocument();
  });

  it("sends a pasted link into the clip studio with the field prefilled", async () => {
    render(
      <MemoryRouter initialEntries={["/create?url=https%3A%2F%2Fwww.youtube.com%2Fwatch%3Fv%3Dabc123&focus=url"]}>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Paste a YouTube, Twitch or Kick video URL/i))
        .toHaveValue("https://www.youtube.com/watch?v=abc123");
    });
  });

  it("keeps Basic-auth failures visible instead of pretending the engine is up", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 401, json: async () => ({ detail: "Not authenticated" }) }) as unknown as Response));
    render(<MemoryRouter initialEntries={["/studio"]}><App /></MemoryRouter>);
    expect(await screen.findByText("ENGINE OFFLINE")).toBeInTheDocument();
  });
});

import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

// jsdom has no layout engine; framer-motion and the palette both feature-test
// these, so provide inert implementations instead of letting effects throw.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }),
});

window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
Element.prototype.scrollIntoView = vi.fn();

// framer-motion's in-view reveals need IntersectionObserver; jsdom ships none.
class NoopIntersectionObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return []; }
  root = null;
  rootMargin = "";
  thresholds = [];
}
Object.defineProperty(window, "IntersectionObserver", { writable: true, value: NoopIntersectionObserver });
Object.defineProperty(globalThis, "IntersectionObserver", { writable: true, value: NoopIntersectionObserver });

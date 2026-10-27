import { lazy, Suspense } from "react";
import { render, screen } from "@testing-library/react";
import axe from "axe-core";
import { ErrorBoundary } from "./ErrorBoundary";

describe("render failure recovery", () => {
  beforeEach(() => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("preserves successful children", () => {
    render(
      <ErrorBoundary>
        <p>Working page</p>
      </ErrorBoundary>,
    );
    expect(screen.getByText("Working page")).toBeVisible();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("reports render failures with accessible recovery actions", async () => {
    function Broken(): never {
      throw new Error("Synthetic render failure");
    }
    const { container } = render(
      <ErrorBoundary>
        <Broken />
      </ErrorBoundary>,
    );
    expect(screen.getByRole("alert")).toBeVisible();
    expect(screen.getByRole("button", { name: "Reload page" })).toBeVisible();
    expect(screen.getByRole("link", { name: "Return to Start here" })).toHaveAttribute("href", "/");
    expect(console.error).toHaveBeenCalled();
    expect((await axe.run(container)).violations).toEqual([]);
  });

  it("catches rejected lazy imports rather than leaving the loading state", async () => {
    const Broken = lazy(() => Promise.reject(new Error("Synthetic chunk failure")));
    render(
      <ErrorBoundary>
        <Suspense fallback={<p role="status">Loading</p>}>
          <Broken />
        </Suspense>
      </ErrorBoundary>,
    );
    expect(await screen.findByRole("alert")).toBeVisible();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});

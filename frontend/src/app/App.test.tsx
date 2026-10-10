import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { principles } from "../content/principles";
import { defaultRoutes, fixtures } from "../test/fixtures";
import { mockApi, mockOffline } from "../test/mockApi";
import { renderApp } from "../test/render";
import { LEVEL_STORAGE_KEY } from "./levelContext";

describe("app shell", () => {
  it("renders the central lesson, start links and completeness coverage", async () => {
    mockApi(defaultRoutes);
    renderApp("/");
    expect(
      await screen.findByRole("heading", { level: 1, name: fixtures.workshop.content.title }),
    ).toBeInTheDocument();
    const lesson = screen.getByRole("region", { name: "The central lesson" });
    expect(within(lesson).getAllByRole("listitem")).toHaveLength(principles.length);
    expect(screen.getByRole("link", { name: "Build a use case" })).toHaveAttribute(
      "href",
      "/use-cases",
    );
    expect(
      await screen.findByText(
        `${String(fixtures.completeness.answered)} of ${String(fixtures.completeness.total)}`,
      ),
    ).toBeInTheDocument();
  });

  it("shows execution state from the control plane in the status bar", async () => {
    mockApi(defaultRoutes);
    renderApp("/");
    const status = screen.getByRole("contentinfo", { name: "Execution status" });
    await waitFor(() => {
      expect(within(status).getByText("Operating mode").nextSibling).toHaveTextContent(
        fixtures.runtimeStatus.operating_mode,
      );
    });
    expect(within(status).getByText("Write mode").nextSibling).toHaveTextContent(
      fixtures.runtimeStatus.write_mode,
    );
    expect(within(status).getByText("Learning level").nextSibling).toHaveTextContent("L100");
    for (const label of [
      "Operating mode",
      "Data provider",
      "Agent provider",
      "MCP",
      "Identity",
      "Write mode",
      "Learning level",
      "Preview features",
    ]) {
      expect(within(status).getByText(label)).toBeVisible();
    }
    expect(within(status).getByText("Write mode").closest("details")).toBeNull();
  });

  it("lists enabled preview features", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/runtime/status": { ...fixtures.runtimeStatus, preview_features: ["fabric_iq"] },
    });
    renderApp("/");
    const status = screen.getByRole("contentinfo", { name: "Execution status" });
    await waitFor(() => {
      expect(within(status).getByText("Preview features").nextSibling).toHaveTextContent(
        "fabric_iq",
      );
    });
  });

  it("never implies a live connection when the control plane is down", async () => {
    mockOffline();
    renderApp("/");
    const status = screen.getByRole("contentinfo", { name: "Execution status" });
    await waitFor(() => {
      expect(within(status).getByText("Control plane").nextSibling).toHaveTextContent(
        "Not reachable: nothing is live",
      );
    });
    expect(await screen.findAllByText("Control plane not reachable")).toHaveLength(2);
  });

  it("persists the learning level chosen in the header", async () => {
    mockApi(defaultRoutes);
    renderApp("/");
    await userEvent.click(screen.getByRole("radio", { name: "L300" }));
    expect(window.localStorage.getItem(LEVEL_STORAGE_KEY)).toBe("l300");
    const status = screen.getByRole("contentinfo", { name: "Execution status" });
    expect(within(status).getByText("Learning level").nextSibling).toHaveTextContent("L300");
  });

  it("restores a stored level and ignores invalid stored values", () => {
    mockApi(defaultRoutes);
    window.localStorage.setItem(LEVEL_STORAGE_KEY, "l400");
    const first = renderApp("/");
    expect(screen.getByRole("radio", { name: "L400" })).toBeChecked();
    first.unmount();
    window.localStorage.setItem(LEVEL_STORAGE_KEY, "l999");
    renderApp("/");
    expect(screen.getByRole("radio", { name: "L100" })).toBeChecked();
  });

  it("offers a keyboard-reachable skip link and a not-found page", async () => {
    mockApi(defaultRoutes);
    renderApp("/nowhere");
    await userEvent.tab();
    expect(screen.getByRole("link", { name: "Skip to main content" })).toHaveFocus();
    expect(screen.getByRole("heading", { name: "Page not found" })).toBeInTheDocument();
    expect(document.title).toContain("Not found");
  });

  it("has no detectable accessibility violations on the home page", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/");
    await screen.findByText(
      `${String(fixtures.completeness.answered)} of ${String(fixtures.completeness.total)}`,
    );
    const results = await axe.run(container);
    expect(results.violations).toEqual([]);
  });
});

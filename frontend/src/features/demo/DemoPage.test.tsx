import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, problem } from "../../test/mockApi";
import { renderApp } from "../../test/render";

describe("demo mode", () => {
  it("shows readiness and runs the ten-act offline demo", async () => {
    mockApi(defaultRoutes);
    renderApp("/demo");
    const readiness = await screen.findByRole("table", { name: /Each component is probed/ });
    expect(within(readiness).getAllByRole("row")).toHaveLength(
      fixtures.demoStatus.lines.length + 1,
    );
    await userEvent.click(screen.getByRole("button", { name: "Run the offline demo" }));
    expect(await screen.findByText(/Release gate: PASSED/)).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 3, name: /^Act / })).toHaveLength(
      fixtures.demoRun.steps.length,
    );
    expect(screen.getByRole("heading", { level: 3, name: /^Act 6:/ })).toHaveTextContent("Skipped");
  });

  it("shows demo failures", async () => {
    const failed = {
      ...fixtures.demoRun,
      passed: false,
      steps: fixtures.demoRun.steps.map((s) => (s.act === 2 ? { ...s, passed: false } : s)),
    };
    let calls = 0;
    mockApi({
      ...defaultRoutes,
      "POST /api/v1/demo/run": () => {
        calls += 1;
        return calls === 1 ? failed : problem(503, "DataNotBuiltError", "no data");
      },
    });
    renderApp("/demo");
    await userEvent.click(await screen.findByRole("button", { name: "Run the offline demo" }));
    expect(await screen.findByText(/Release gate: FAILED/)).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Run the offline demo" }));
    expect(await screen.findByText("no data (HTTP 503)")).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/demo");
    await screen.findByRole("table", { name: /Each component is probed/ });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

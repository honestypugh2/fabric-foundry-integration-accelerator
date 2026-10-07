import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, startsWith } from "../../test/mockApi";
import { renderApp } from "../../test/render";

const lab = fixtures.labGovernedChange;

describe("labs", () => {
  it("lists labs", async () => {
    mockApi(defaultRoutes);
    renderApp("/labs");
    for (const summary of fixtures.labs) {
      expect(await screen.findByRole("link", { name: summary.title })).toBeInTheDocument();
    }
  });

  it("shows the eleven stages in order and tracks progress locally", async () => {
    mockApi(defaultRoutes);
    renderApp("/labs/lab-governed-change");
    expect(
      await screen.findByRole("heading", { level: 1, name: startsWith(lab.title) }),
    ).toBeInTheDocument();
    const stages = screen.getAllByRole("checkbox", { name: /^Mark .* done$/ });
    expect(stages).toHaveLength(11);
    await userEvent.click(screen.getByRole("checkbox", { name: "Mark BREAK IT done" }));
    expect(screen.getByText(/1 of 11 stages done/)).toBeInTheDocument();
    expect(window.localStorage.getItem("ffia.progress.lab.lab-governed-change")).toBe(
      '["BREAK IT"]',
    );
    await userEvent.click(screen.getByRole("checkbox", { name: "Mark BREAK IT done" }));
    expect(screen.getByText(/0 of 11 stages done/)).toBeInTheDocument();
  });

  it("shows prerequisites, expected results and evidence categories", async () => {
    const steps = lab.steps.map((step, index) =>
      index === 0
        ? { ...step, expected: "A plan is PROPOSED.", evidence_category: "SIMULATED LOCALLY" }
        : { ...step, expected: null, evidence_category: null },
    );
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/education/labs/lab-governed-change": {
        ...lab,
        prerequisites: ["Start the API"],
        lessons: ["p08-human-in-the-loop", "p09-governed-mcp"],
        steps,
      },
    });
    renderApp("/labs/lab-governed-change");
    expect(await screen.findByText("Start the API")).toBeInTheDocument();
    expect(screen.getByText("A plan is PROPOSED.")).toBeInTheDocument();
    expect(screen.getByText("SIMULATED LOCALLY")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "p09-governed-mcp" })).toBeInTheDocument();
  });

  it("ignores corrupt stored progress", async () => {
    mockApi(defaultRoutes);
    window.localStorage.setItem("ffia.progress.lab.lab-governed-change", "{not json");
    renderApp("/labs/lab-governed-change");
    expect(await screen.findByText(/0 of 11 stages done/)).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/labs/lab-governed-change");
    await screen.findByRole("heading", { level: 1, name: startsWith(lab.title) });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

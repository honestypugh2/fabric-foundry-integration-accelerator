import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import axe from "axe-core";
import { ArchitectureImage } from "../../components/ArchitectureImage";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, problem } from "../../test/mockApi";
import { renderApp } from "../../test/render";

describe("workshop journeys and applied research", () => {
  it("keeps the primary navigation outcome-led and tools secondary", async () => {
    mockApi(defaultRoutes);
    renderApp("/");
    await screen.findByRole("heading", { name: fixtures.workshop.content.title });
    expect(
      within(screen.getByRole("navigation", { name: "Primary" }))
        .getAllByRole("link")
        .map((item) => item.textContent),
    ).toEqual(["Workshop", "Learn", "Use Cases", "Patterns", "Evidence"]);
    expect(screen.getByRole("navigation", { name: "Workshop tools" })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Start this path/ })).toHaveLength(
      fixtures.workshop.content.journeys.length,
    );
    await userEvent.click(
      screen.getByText("Architecture coverage—not workshop or live certification"),
    );
    expect(screen.getByRole("progressbar", { name: "Questions answered" })).toBeInTheDocument();
  });

  it("connects breadth journeys to foundations and level-specific lessons", async () => {
    mockApi(defaultRoutes);
    renderApp("/learn");
    await screen.findByRole("heading", { name: "Understand the foundations" });
    expect(
      screen.getAllByRole("link", { name: "From relations to governed lakehouse context" }).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getByRole("heading", { name: "Investigate, specify and verify" }),
    ).toBeInTheDocument();
  });

  it.each(["/learn#path-research", "/evidence#fabric-app-read"])(
    "reveals the requested %s anchor after asynchronous content loads",
    async (route) => {
      mockApi(defaultRoutes);
      const original = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "scrollIntoView");
      const scroll = vi.fn();
      Object.defineProperty(HTMLElement.prototype, "scrollIntoView", {
        configurable: true,
        value: scroll,
      });
      try {
        renderApp(route);
        await waitFor(() => {
          expect(scroll).toHaveBeenCalledWith({ block: "start" });
        });
      } finally {
        if (original) Object.defineProperty(HTMLElement.prototype, "scrollIntoView", original);
        else Reflect.deleteProperty(HTMLElement.prototype, "scrollIntoView");
      }
    },
  );

  it("teaches the practical contract and switches to a sourced research experiment", async () => {
    mockApi(defaultRoutes);
    renderApp("/learn/p08-human-in-the-loop");
    expect(await screen.findByRole("heading", { name: "What is it?" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "How to implement it here" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Foundations and research" }));
    expect(screen.getByRole("heading", { name: "Fundamentals and theory" })).toBeInTheDocument();
    expect(screen.getByText("Falsifiable hypothesis")).toBeInTheDocument();
    expect(screen.getByText("Independent baseline")).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: /Azure Well-Architected/ })).toHaveAttribute(
      "href",
      expect.stringContaining("learn.microsoft.com"),
    );
    expect(screen.getByText(/proposed experiment, not a reported result/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Build and verify" }));
    expect(screen.getByRole("heading", { name: "Expected result" })).toBeInTheDocument();
  });

  it("discloses a missing instructional brief without inventing teaching", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/education/lessons/p08-human-in-the-loop": {
        ...fixtures.lessonP08,
        teaching: null,
      },
    });
    renderApp("/learn/p08-human-in-the-loop");
    expect(
      await screen.findByText("An instructional brief has not been authored for this lesson."),
    ).toBeInTheDocument();
  });

  it("explains the use-case capability progression and retains canonical step links", async () => {
    mockApi(defaultRoutes);
    renderApp(`/guides/${fixtures.guideHc01.id}`);
    await screen.findByRole("heading", { name: "What are we improving?" });
    expect(screen.getByRole("heading", { name: "Copilot assistance" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Fabric Skills" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Fabric MCP context" })).toBeInTheDocument();
    const steps = screen.getByRole("navigation", { name: "Guide steps" });
    expect(
      within(steps)
        .getAllByRole("link")
        .every((item) => item.getAttribute("href")?.startsWith("/use-cases/")),
    ).toBe(true);
  });

  it("redirects a legacy deep step and allows returning to the business outcome", async () => {
    mockApi(defaultRoutes);
    renderApp(`/guides/${fixtures.guideHc01.id}/02-verify-tenant-anchor?mode=read#checkpoint`);
    await screen.findByRole("heading", { name: /^Step 2:/ });
    expect(
      screen.getByRole("link", { name: "Return to business outcome and learning path" }),
    ).toHaveAttribute("href", `/use-cases/${fixtures.guideHc01.id}`);
  });

  it("renders an additional use case from registry data without a scenario-specific branch", async () => {
    const id = "example-new-use-case";
    const source = fixtures.workshop.content.use_cases[0];
    if (!source) throw new Error("Expected a registered use-case story in the workshop fixture");
    const story = { ...source, guide_id: id };
    mockApi({
      ...defaultRoutes,
      [`GET /api/v1/guides/${id}`]: { ...fixtures.guideHc01, id, title: "Synthetic new use case" },
      "GET /api/v1/education/workshop": {
        ...fixtures.workshop,
        content: {
          ...fixtures.workshop.content,
          use_cases: [...fixtures.workshop.content.use_cases, story],
        },
      },
    });
    renderApp(`/use-cases/${id}`);
    expect(
      await screen.findByRole("heading", { name: "What are we improving?" }),
    ).toBeInTheDocument();
    expect(screen.getByText(story.problem)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Synthetic new use case" })).toBeInTheDocument();
  });

  it("discloses a missing story and handles research-source errors explicitly", async () => {
    const first = {
      ...fixtures.workshop,
      content: { ...fixtures.workshop.content, use_cases: [] },
    };
    mockApi({ ...defaultRoutes, "GET /api/v1/education/workshop": first });
    const view = renderApp(`/use-cases/${fixtures.guideHc01.id}`);
    expect(
      await screen.findByText(/business-to-build story has not been authored/),
    ).toBeInTheDocument();
    view.unmount();
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/education/workshop": problem(503, "Unavailable", "reading unavailable"),
    });
    renderApp("/learn/p08-human-in-the-loop");
    await userEvent.click(await screen.findByRole("button", { name: "Foundations and research" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load reading sources");
  });

  it("renders historical execution scope and UI-only images without conflating their labels", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/evidence");
    expect(
      await screen.findByRole("heading", { name: "Fabric application read" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/not a current health check/)).toBeInTheDocument();
    expect(screen.getAllByRole("img")).toHaveLength(2);
    expect(screen.getByText(/not a scored competitor/)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Local / offline" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Azure / Fabric live-first" })).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Strict Azure / Fabric live verification" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Deployed Azure and Fabric resources" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Application Insights and Log Analytics" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Verified Azure telemetry ingestion" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("This is client telemetry, not a newly verified Foundry agent trace."),
    ).toBeInTheDocument();
    expect(screen.getByText("ffia serve api --offline")).toBeInTheDocument();
    expect(screen.getByText("ffia demo live --json")).toBeInTheDocument();
    const records = screen.getAllByRole("link", { name: /Download verification record:/ });
    expect(records).toHaveLength(6);
    expect(records.every((record) => record.hasAttribute("download"))).toBe(true);
    expect((await axe.run(container)).violations).toEqual([]);
  });

  it("shows coverage gaps for all patterns rather than a universal readiness badge", async () => {
    mockApi(defaultRoutes);
    renderApp("/patterns");
    const table = await screen.findByRole("table", { name: /Concept, five-level teaching/ });
    expect(within(table).getAllByRole("row")).toHaveLength(fixtures.patterns.length + 1);
    expect(within(table).getAllByText("No linked lab").length).toBeGreaterThan(0);
    expect(within(table).getAllByText("Not recorded").length).toBeGreaterThan(0);
    expect(within(table).getByRole("link", { name: /P25 Spec-driven/ })).toBeInTheDocument();
  });

  it("discloses missing resource records and unpublished verification documents", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/education/workshop": {
        ...fixtures.workshop,
        content: {
          ...fixtures.workshop.content,
          evidence: fixtures.workshop.content.evidence
            .filter((entry) => entry.category === "INTERFACE")
            .map((entry) => ({
              ...entry,
              verification_record: "docs/operations/not-published.md",
            })),
        },
      },
    });
    renderApp("/evidence");
    expect(await screen.findAllByText("No evidence recorded for this category.")).toHaveLength(2);
    expect(screen.getAllByText(/Verification record is not published/)).toHaveLength(2);
    expect(
      screen.queryByRole("link", { name: /Download verification record:/ }),
    ).not.toBeInTheDocument();
  });

  it("does not invent teaching when a coverage record has no linked lesson", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/education/workshop": {
        ...fixtures.workshop,
        coverage: fixtures.workshop.coverage.map((item) => ({ ...item, lesson_ids: [] })),
      },
    });
    renderApp("/patterns");
    const table = await screen.findByRole("table", { name: /Concept, five-level teaching/ });
    expect(within(table).getAllByText("Not authored")).toHaveLength(fixtures.patterns.length);
  });

  it("keeps an unknown diagram explicit and the known export accessible", () => {
    const view = render(
      <MemoryRouter>
        <ArchitectureImage viewId="missing" title="Missing view" />
      </MemoryRouter>,
    );
    expect(screen.getByText("No static export is available for this view.")).toBeInTheDocument();
    view.unmount();
    render(
      <MemoryRouter>
        <ArchitectureImage viewId="hc-01" title="Engineering architecture" />
      </MemoryRouter>,
    );
    expect(screen.getByRole("img", { name: "Engineering architecture" })).toHaveAttribute(
      "src",
      expect.stringContaining("hc-01.png"),
    );
  });

  it.each(["theory-to-tools", "integration-paths"])(
    "renders the focused %s PNG rather than a missing-export message",
    (viewId) => {
      render(
        <MemoryRouter>
          <ArchitectureImage viewId={viewId} title="Focused teaching diagram" />
        </MemoryRouter>,
      );
      expect(screen.getByRole("img", { name: "Focused teaching diagram" })).toHaveAttribute(
        "src",
        expect.stringContaining(`${viewId}.png`),
      );
      expect(
        screen.queryByText("No static export is available for this view."),
      ).not.toBeInTheDocument();
    },
  );

  it("has no detectable accessibility violations in the research lens", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/learn/p08-human-in-the-loop");
    await userEvent.click(await screen.findByRole("button", { name: "Foundations and research" }));
    await screen.findByRole("link", { name: /Azure Well-Architected/ });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

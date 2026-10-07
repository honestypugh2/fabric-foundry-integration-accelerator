import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi } from "../../test/mockApi";
import { renderApp } from "../../test/render";

const reference = fixtures.viewReference.view;
const system = fixtures.viewSystem.view;

function canvas() {
  return screen.getByRole("group", { name: /diagram\. Select a component/ });
}

describe("architecture studio", () => {
  it("lists every view and opens the reference architecture by default", async () => {
    mockApi(defaultRoutes);
    renderApp("/architecture");
    const tabs = await screen.findByRole("navigation", { name: "Architecture views" });
    for (const view of fixtures.views) {
      expect(within(tabs).getByRole("link", { name: view.title })).toHaveAttribute(
        "href",
        `/architecture/${view.id}`,
      );
    }
    expect(
      await screen.findByRole("heading", { level: 2, name: reference.title }),
    ).toBeInTheDocument();
    expect(within(canvas()).getAllByRole("button")).toHaveLength(reference.nodes.length);
    expect(screen.getByText(reference.cue)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download draw.io file" })).toHaveAttribute(
      "href",
      "/api/v1/education/views/reference/drawio",
    );
  });

  it("builds the picture one layer at a time", async () => {
    mockApi(defaultRoutes);
    renderApp("/architecture/reference");
    await screen.findByRole("heading", { level: 2, name: reference.title });
    const first = reference.steps[0];
    await userEvent.click(screen.getByRole("button", { name: first?.label ?? "" }));
    const firstCount = reference.nodes.filter(
      (n) => n.step === null || n.step === first?.id,
    ).length;
    expect(within(canvas()).getAllByRole("button")).toHaveLength(firstCount);
    expect(screen.getByText(first?.cue ?? "")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next layer →" }));
    expect(within(canvas()).getAllByRole("button").length).toBeGreaterThan(firstCount);
    await userEvent.click(screen.getByRole("button", { name: "Full picture" }));
    expect(within(canvas()).getAllByRole("button")).toHaveLength(reference.nodes.length);
  });

  it("traces a request hop by hop", async () => {
    mockApi(defaultRoutes);
    renderApp("/architecture/reference");
    await screen.findByRole("heading", { level: 2, name: reference.title });
    const trace = reference.traces[1];
    await userEvent.selectOptions(screen.getByLabelText("Request"), trace?.id ?? "");
    await userEvent.click(screen.getByRole("button", { name: "▶ Trace a request" }));
    expect(
      screen.getByText(`· step 1 of ${String(trace?.steps.length)}`, { exact: false }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: `offline demo act ${String(trace?.demo_act)}` }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next step →" }));
    const cue = screen.getByText("Presenter cue:").closest("div") as HTMLElement;
    expect(within(cue).getByText(trace?.steps[1]?.say ?? "", { exact: false })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "← Back" }));
    expect(screen.getByText(`· step 1 of`, { exact: false })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Stop" }));
    expect(screen.getByRole("button", { name: "▶ Trace a request" })).toBeInTheDocument();
  });

  it("inspects a component at the chosen level with keyboard", async () => {
    mockApi(defaultRoutes);
    renderApp("/architecture/reference");
    await screen.findByRole("heading", { level: 2, name: reference.title });
    const component = fixtures.architecture.components.find((c) => c.id === "foundry-agent");
    const node = within(canvas()).getByRole("button", { name: /^Foundry Agent Service\./ });
    node.focus();
    await userEvent.keyboard("{Enter}");
    const inspector = screen.getByRole("complementary", { name: "Component details" });
    expect(within(inspector).getByText(component?.description.l100 ?? "")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("radio", { name: "L400" }));
    expect(within(inspector).getByText(component?.description.l400 ?? "")).toBeInTheDocument();
    expect(within(inspector).getByRole("heading", { name: "Connections" })).toBeInTheDocument();
  });

  it("overlays live runtime state on the system view", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp("/architecture/system");
    await screen.findByRole("heading", { level: 2, name: system.title });
    await waitFor(() => {
      expect(
        within(canvas()).getByRole("button", {
          name: /^Foundry Agent Service\..*Runtime: NOT CONFIGURED$/,
        }),
      ).toBeInTheDocument();
    });
    expect(calls.some((c) => c.path === "/api/v1/education/views/system/runtime")).toBe(true);
    await userEvent.click(
      within(canvas()).getByRole("button", { name: /^FastAPI control plane\./ }),
    );
    const inspector = screen.getByRole("complementary", { name: "Component details" });
    expect(within(inspector).getByText("ACTIVE")).toBeInTheDocument();
    expect(within(inspector).getByText("src/fabric_foundry_accelerator/api")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Live runtime state" }));
    expect(
      within(canvas()).getByRole("button", { name: /^Foundry Agent Service\. Planned · Phase 6$/ }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Status labels" }));
  });

  it("keeps the component catalog and a text alternative", async () => {
    mockApi(defaultRoutes);
    renderApp("/architecture/reference");
    await screen.findByRole("heading", { level: 2, name: reference.title });
    await userEvent.click(screen.getByText("Text description of this diagram"));
    expect(screen.getByRole("heading", { level: 3, name: "Connections" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "All components" }));
    const policy = await screen.findByRole("button", { name: /Policy engine/ });
    await userEvent.click(policy);
    expect(policy).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(
      within(screen.getByRole("article")).getByRole("button", { name: "Human approval" }),
    );
    expect(
      within(screen.getByRole("article")).getByRole("heading", { level: 2 }),
    ).toHaveTextContent("Human approval");
  });

  it("zooms and keeps the traced component in view", async () => {
    mockApi(defaultRoutes);
    const scroll = vi.fn();
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      value: scroll,
      configurable: true,
    });
    renderApp("/architecture/reference");
    await screen.findByRole("heading", { level: 2, name: reference.title });
    const svg = canvas();
    expect(svg.getAttribute("style")).toContain("width");
    await userEvent.click(screen.getByRole("checkbox", { name: "Fit to width" }));
    expect(canvas().getAttribute("style") ?? "").not.toContain("width");
    await userEvent.click(screen.getByRole("button", { name: "▶ Trace a request" }));
    expect(scroll).toHaveBeenCalled();
    Reflect.deleteProperty(Element.prototype, "scrollIntoView");
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/architecture/system");
    await screen.findByRole("heading", { level: 2, name: system.title });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

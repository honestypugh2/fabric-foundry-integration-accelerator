import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, problem } from "../../test/mockApi";
import { renderApp } from "../../test/render";

const guide = fixtures.guideHc01;
const GUIDE_URL = `/use-cases/${guide.id}`;

describe("guide runner", () => {
  it("discovers the real third guide and navigates its shared rehearsal", async () => {
    mockApi(defaultRoutes);
    renderApp("/use-cases");
    await userEvent.click(await screen.findByRole("link", { name: fixtures.guideDq01.title }));
    expect(
      await screen.findByRole("heading", { name: "What are we improving?" }),
    ).toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "Guide steps" });
    await userEvent.click(
      within(nav).getByRole("link", { name: /Rehearse a governed notebook proposal/ }),
    );
    const panel = await screen.findByRole("region", { name: /Rehearse this write/ });
    expect(within(panel).getByRole("button", { name: "1. Plan and validate" })).toBeEnabled();
    expect(screen.getByText("dq_review_notebook")).toBeInTheDocument();
    expect(
      await screen.findByRole("region", { name: "Where this step happens" }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: /^Next:/ }));
    expect(
      await screen.findByRole("heading", { name: "Step 6: Verify outcomes and record limits" }),
    ).toBeInTheDocument();
  });

  it("lists guides", async () => {
    mockApi(defaultRoutes);
    renderApp("/guides");
    expect(await screen.findByRole("link", { name: guide.title })).toHaveAttribute(
      "href",
      GUIDE_URL,
    );
  });

  it("runs a step with its tool path, prompts, checkpoint and offline equivalent", async () => {
    mockApi(defaultRoutes);
    renderApp(`${GUIDE_URL}/02-verify-tenant-anchor`);
    const step = guide.steps[1];
    expect(
      await screen.findByRole("heading", { level: 2, name: `Step 2: ${step?.title ?? ""}` }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/core_search-catalog/).length).toBeGreaterThan(0);
    expect(screen.getByText(/^Use exactly this tool first\./)).toBeInTheDocument();
    const fallback = screen.getByText(/list_fabric_workspaces, list_fabric_items/);
    expect(within(fallback).getByText("LOCAL")).toBeInTheDocument();
    expect(screen.getByText(step?.copilot_prompt ?? "")).toBeInTheDocument();
    expect(screen.getByText(step?.claude_code_prompt ?? "")).toBeInTheDocument();
    expect(screen.getByText(/does not change anything/)).toBeInTheDocument();
    expect(screen.getByText(/All use cases share the application runtime/)).toHaveTextContent(
      /write rehearsals remain SIMULATED/,
    );
    const evidence = screen.getByRole("checkbox", { name: step?.evidence_required[0] ?? "" });
    await userEvent.click(evidence);
    expect(evidence).toBeChecked();
    await userEvent.click(screen.getByRole("link", { name: /^Next:/ }));
    expect(await screen.findByRole("heading", { level: 2, name: /^Step 3:/ })).toBeInTheDocument();
    expect(screen.getByText(/has no simulated equivalent/)).toBeInTheDocument();
  });

  it("shows where each step happens on the HC-01 diagram", async () => {
    mockApi(defaultRoutes);
    renderApp(`${GUIDE_URL}/04-create-lakehouse`);
    const section = await screen.findByRole("region", { name: "Where this step happens" });
    expect(
      await within(section).findByRole("group", { name: /diagram\. Select a component/ }),
    ).toBeInTheDocument();
    expect(within(section).getByRole("button", { name: "▶ Trace a request" })).toBeEnabled();
  });

  it("tracks completed steps and copies prompts", async () => {
    mockApi(defaultRoutes);
    const writeText = vi.fn(() => Promise.resolve());
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    renderApp(`${GUIDE_URL}/${guide.steps[0]?.id ?? ""}`);
    await screen.findByRole("heading", { level: 2, name: /^Step 1:/ });
    const nav = screen.getByRole("navigation", { name: "Guide steps" });
    await userEvent.click(
      within(nav).getByRole("checkbox", { name: `Mark ${guide.steps[0]?.title ?? ""} done` }),
    );
    expect(
      within(nav).getByText(`1 of ${String(guide.steps.length)} steps done`),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Copy github copilot prompt" }));
    expect(writeText).toHaveBeenCalledWith(guide.steps[0]?.copilot_prompt);
    expect(await screen.findByText("Copied")).toBeInTheDocument();
  });

  it("reports copy failures", async () => {
    mockApi(defaultRoutes);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText: () => Promise.reject(new Error("denied")) },
      configurable: true,
    });
    renderApp(`${GUIDE_URL}/${guide.steps[0]?.id ?? ""}`);
    await userEvent.click(await screen.findByRole("button", { name: "Copy claude code prompt" }));
    expect(await screen.findByText(/Copy failed/)).toBeInTheDocument();
  });

  it("separates the overview and prerequisites from the first build module", async () => {
    mockApi(defaultRoutes);
    renderApp(GUIDE_URL);
    const start = await screen.findByRole("link", { name: "Start workshop" });
    expect(start).toHaveAttribute("href", `${GUIDE_URL}/${guide.steps[0]?.id ?? ""}`);
    expect(screen.queryByRole("heading", { name: /^Step 1:/ })).not.toBeInTheDocument();
    expect(
      screen
        .getByText(`Tools and prerequisites (${String(guide.tools.length)})`)
        .closest("details"),
    ).toHaveAttribute("open");
    expect(
      screen.getByRole("progressbar", { name: "Workshop checklist progress" }),
    ).toHaveAttribute("value", "0");
    await userEvent.click(start);
    expect(await screen.findByRole("heading", { name: /^Step 1:/ })).toBeInTheDocument();
    expect(screen.getByRole("navigation", { name: "On this step" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Start workshop" })).not.toBeInTheDocument();
  });

  it("reports an unknown step instead of silently opening the first module", async () => {
    mockApi(defaultRoutes);
    renderApp(`${GUIDE_URL}/missing-step`);
    expect(await screen.findByRole("alert")).toHaveTextContent("Step not found");
    expect(screen.queryByRole("heading", { name: /^Step 1:/ })).not.toBeInTheDocument();
  });

  it("filters the catalog by tool and industry, supports clearing and discloses no results", async () => {
    mockApi(defaultRoutes);
    renderApp("/use-cases");
    const search = await screen.findByRole("searchbox", { name: "Search use cases" });
    await userEvent.type(search, "nonsense-no-match");
    expect(screen.getByText(/No use cases match/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(search).toHaveValue("");
    const requiredTool = guide.tools.find((tool) => tool.required);
    if (!requiredTool) throw new Error("Expected a required tool");
    await userEvent.type(search, requiredTool.name);
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Tool or service" }),
      requiredTool.name,
    );
    expect(screen.getByRole("link", { name: guide.title })).toBeInTheDocument();
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Industry" }),
      guide.industry,
    );
    expect(screen.getByRole("link", { name: guide.title })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getByRole("combobox", { name: "Industry" })).toHaveValue("");
    expect(screen.getByRole("combobox", { name: "Tool or service" })).toHaveValue("");
    expect(screen.getByRole("link", { name: fixtures.guideDq01.title })).toBeInTheDocument();
  });

  it("restores shared catalog filters from the URL", async () => {
    mockApi(defaultRoutes);
    renderApp("/use-cases?q=nonsense-no-match");
    expect(await screen.findByRole("searchbox", { name: "Search use cases" })).toHaveValue(
      "nonsense-no-match",
    );
    expect(screen.getByText(/No use cases match/)).toBeInTheDocument();
  });

  it("rehearses a governed write: plan, approve, execute, audit", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp(`${GUIDE_URL}/04-create-lakehouse`);
    const panel = await screen.findByRole("region", { name: /Rehearse this write/ });
    expect(within(panel).getByRole("button", { name: /2\. Approve/ })).toBeDisabled();
    await userEvent.click(within(panel).getByRole("button", { name: "1. Plan and validate" }));
    expect(await within(panel).findByText(fixtures.plan.change_id)).toBeInTheDocument();
    expect(calls.find((c) => c.path === "/api/v1/plans")?.body).toMatchObject({
      operation: "create_lakehouse",
      target: { item_name: "healthcare_lakehouse", destination: "LOCAL" },
      requested_by: "engineer-a",
    });
    await userEvent.click(within(panel).getByRole("button", { name: "2. Approve as approver-b" }));
    expect(await within(panel).findByText(/Approved by approver-b/)).toBeInTheDocument();
    await userEvent.click(
      within(panel).getByRole("button", { name: "3. Execute with the scoped writer" }),
    );
    expect(
      await within(panel).findByText(fixtures.execution.data.verification.detail, { exact: false }),
    ).toBeInTheDocument();
    expect(
      await within(panel).findByText(`Audit trail (${String(fixtures.audit.length)} records)`),
    ).toBeInTheDocument();
  });

  it("shows the backend refusing self-approval", async () => {
    mockApi({
      ...defaultRoutes,
      "POST /api/v1/approvals": problem(
        409,
        "ApprovalError",
        "the requester cannot approve their own change",
      ),
    });
    renderApp(`${GUIDE_URL}/04-create-lakehouse`);
    const panel = await screen.findByRole("region", { name: /Rehearse this write/ });
    const approver = within(panel).getByLabelText("Approver");
    await userEvent.clear(approver);
    await userEvent.type(approver, "engineer-a");
    await userEvent.clear(within(panel).getByLabelText("Requested by"));
    await userEvent.type(within(panel).getByLabelText("Requested by"), "engineer-a");
    await userEvent.clear(within(panel).getByLabelText("Workspace alias"));
    await userEvent.type(within(panel).getByLabelText("Workspace alias"), "demo-dev");
    await userEvent.click(within(panel).getByRole("button", { name: "1. Plan and validate" }));
    await within(panel).findByText(fixtures.plan.change_id);
    await userEvent.click(within(panel).getByRole("button", { name: "2. Approve as engineer-a" }));
    expect(
      await within(panel).findByText(/Refused: the requester cannot approve/),
    ).toBeInTheDocument();
    expect(
      within(panel).getByRole("button", { name: "3. Execute with the scoped writer" }),
    ).toBeDisabled();
  });

  it("shows blocked plans and planning errors", async () => {
    const blocked = { ...fixtures.plan, status: "BLOCKED", policy_allowed: false };
    let attempt = 0;
    mockApi({
      ...defaultRoutes,
      "POST /api/v1/plans": () => {
        attempt += 1;
        return attempt === 1 ? blocked : problem(422, "InvalidRequestError", "bad plan");
      },
    });
    renderApp(`${GUIDE_URL}/04-create-lakehouse`);
    const panel = await screen.findByRole("region", { name: /Rehearse this write/ });
    await userEvent.click(within(panel).getByRole("button", { name: "1. Plan and validate" }));
    expect(await within(panel).findByText("BLOCKED")).toBeInTheDocument();
    expect(within(panel).getByRole("button", { name: /2\. Approve/ })).toBeDisabled();
    await userEvent.click(within(panel).getByRole("button", { name: "1. Plan and validate" }));
    expect(await within(panel).findByText("bad plan (HTTP 422)")).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp(`${GUIDE_URL}/04-create-lakehouse`);
    await screen.findByRole("region", { name: /Rehearse this write/ });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

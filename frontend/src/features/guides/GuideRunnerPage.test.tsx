import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, problem } from "../../test/mockApi";
import { renderApp } from "../../test/render";

const guide = fixtures.guideHc01;
const GUIDE_URL = `/guides/${guide.id}`;

describe("guide runner", () => {
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
    expect(screen.getByText(/^Use exactly this tool\./)).toBeInTheDocument();
    expect(screen.getByText(step?.copilot_prompt ?? "")).toBeInTheDocument();
    expect(screen.getByText(step?.claude_code_prompt ?? "")).toBeInTheDocument();
    expect(screen.getByText(/does not change anything/)).toBeInTheDocument();
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
      await within(section).findByText(
        /Highlighted: Fabric MCP Server \(local\), healthcare_lakehouse, Approval gate\./,
      ),
    ).toBeInTheDocument();
    expect(
      within(section).getByRole("link", { name: "Open the full interactive diagram" }),
    ).toHaveAttribute("href", "/architecture/hc-01");
  });

  it("tracks completed steps and copies prompts", async () => {
    mockApi(defaultRoutes);
    const writeText = vi.fn(() => Promise.resolve());
    Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true });
    renderApp(GUIDE_URL);
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
    renderApp(GUIDE_URL);
    await userEvent.click(await screen.findByRole("button", { name: "Copy claude code prompt" }));
    expect(await screen.findByText(/Copy failed/)).toBeInTheDocument();
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

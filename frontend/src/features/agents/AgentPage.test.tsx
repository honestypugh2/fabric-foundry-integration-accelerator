import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, mockOffline, problem } from "../../test/mockApi";
import { renderApp } from "../../test/render";

describe("agent page", () => {
  it("shows who answers and asks a typed question", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp("/agent");
    expect(
      await screen.findByText(fixtures.agentProfile.local_provider, { selector: "dd" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Not configured \(live Foundry is opt-in\)/)).toBeInTheDocument();
    const ask = screen.getByRole("button", { name: "Ask" });
    expect(ask).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Question"), "  How many duplicates?  ");
    await userEvent.click(ask);
    const answer = await screen.findByRole("region", { name: "Answer" });
    expect(calls.at(-1)?.body).toEqual({
      agent: "sales-insights-agent",
      question: "How many duplicates?",
    });
    expect(within(answer).getByText(fixtures.agentAnswer.execution_label)).toBeInTheDocument();
    expect(within(answer).getByText(/Grounded\./)).toBeInTheDocument();
    expect(within(answer).getByText("local_sales_query")).toBeInTheDocument();
    expect(within(answer).getByText(/Enclosures \(ENC\) grew fastest/)).toBeInTheDocument();
  });

  it("asks a suggested question from the evaluation suite", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp("/agent");
    const first = fixtures.agentProfile.suggested_questions[0] ?? "";
    await userEvent.click(await screen.findByRole("button", { name: first }));
    await screen.findByRole("region", { name: "Answer" });
    expect(calls.at(-1)?.body).toMatchObject({ question: first });
    expect(screen.getByLabelText("Question")).toHaveValue(first);
  });

  it("explains an ungrounded answer and lists what the agent can answer", async () => {
    mockApi({ ...defaultRoutes, "POST /api/v1/agents/ask": fixtures.agentUnsupported });
    renderApp("/agent");
    await userEvent.type(await screen.findByLabelText("Question"), "Tell me a joke");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));
    const answer = await screen.findByRole("region", { name: "Answer" });
    expect(within(answer).getByText(/Not grounded\./)).toBeInTheDocument();
    expect(within(answer).getByText("None.")).toBeInTheDocument();
    expect(
      within(answer).getByRole("heading", { name: "Questions this agent answers offline" }),
    ).toBeInTheDocument();
  });

  it("notes the latency of a configured live agent while asking", async () => {
    let release: (value: Response) => void = () => undefined;
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/agents/sales-insights-agent": {
        ...fixtures.agentProfile,
        live_provider: "Foundry agent (sales-insights-agent)",
      },
      "POST /api/v1/agents/ask": () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    });
    renderApp("/agent");
    expect(await screen.findByText("Foundry agent (sales-insights-agent)")).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Question"), "Total revenue?");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(/Live Foundry calls can take a minute/)).toBeInTheDocument();
    release(new Response(JSON.stringify(fixtures.agentAnswer), { status: 200 }));
    await screen.findByRole("region", { name: "Answer" });
  });

  it("runs the evaluation suite and shows every case", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp("/agent");
    await userEvent.click(await screen.findByRole("button", { name: "Run evaluation suite" }));
    const report = fixtures.agentEval;
    expect(
      await screen.findByText(`${String(report.passed)} of ${String(report.compared)}`),
    ).toBeInTheDocument();
    const table = screen.getByRole("table", { name: /Agent evaluation cases/ });
    expect(within(table).getAllByRole("row")).toHaveLength(report.cases.length + 1);
    expect(calls.at(-1)?.path).toBe("/api/v1/agents/evaluate");
  });

  it("runs the monthly insights workflow and sends nothing", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp("/agent");
    await userEvent.click(
      await screen.findByRole("button", { name: "Run monthly insights workflow" }),
    );
    const run = fixtures.agentWorkflow;
    expect(
      await screen.findByText(`${String(run.ready)} ready for approval, ${String(run.held)} held`),
    ).toBeInTheDocument();
    for (const draft of run.drafts) {
      expect(
        screen.getByRole("article", { name: new RegExp(draft.team_name) }),
      ).toBeInTheDocument();
    }
    expect(screen.getByText(run.delivery)).toBeInTheDocument();
    expect(calls.at(-1)?.path).toBe("/api/v1/agents/workflows/monthly-insights");
  });

  it("shows a held draft and a workflow error", async () => {
    const held = {
      ...fixtures.agentWorkflow,
      ready: 0,
      held: 1,
      drafts: [
        {
          ...fixtures.agentWorkflow.drafts[0],
          status: "HELD",
          reason: "The draft does not match the baseline.",
          missing: ["143.1"],
          fallback_used: true,
        },
      ],
    };
    mockApi({ ...defaultRoutes, "POST /api/v1/agents/workflows/monthly-insights": held });
    renderApp("/agent");
    await userEvent.click(
      await screen.findByRole("button", { name: "Run monthly insights workflow" }),
    );
    expect(await screen.findByText(/Missing: 143\.1\./)).toBeInTheDocument();
    expect(screen.getByText(/\(fallback\)/)).toBeInTheDocument();
    mockApi({
      ...defaultRoutes,
      "POST /api/v1/agents/workflows/monthly-insights": problem(
        422,
        "InvalidRequestError",
        "bad team",
      ),
    });
    await userEvent.click(screen.getByRole("button", { name: "Run monthly insights workflow" }));
    expect(await screen.findByText("bad team (HTTP 422)")).toBeInTheDocument();
  });

  it("shows ask and evaluation errors", async () => {
    mockApi({
      ...defaultRoutes,
      "POST /api/v1/agents/ask": problem(503, "ProviderUnavailableError", "agent unavailable"),
      "POST /api/v1/agents/evaluate": problem(404, "UnknownResourceError", "unknown suite"),
    });
    renderApp("/agent");
    await userEvent.type(await screen.findByLabelText("Question"), "Anything");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText("agent unavailable (HTTP 503)")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Run evaluation suite" }));
    expect(await screen.findByText("unknown suite (HTTP 404)")).toBeInTheDocument();
  });

  it("shows the offline state without implying a live agent", async () => {
    mockOffline();
    renderApp("/agent");
    expect(await screen.findByText("Control plane not reachable")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ask" })).not.toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/agent");
    await userEvent.click(await screen.findByRole("button", { name: "Run evaluation suite" }));
    await screen.findByRole("table", { name: /Agent evaluation cases/ });
    await userEvent.click(screen.getByRole("button", { name: "Run monthly insights workflow" }));
    await screen.findByText(/ready for approval, /);
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

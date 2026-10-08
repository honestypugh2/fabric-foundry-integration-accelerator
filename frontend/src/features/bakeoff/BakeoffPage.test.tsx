import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, mockOffline } from "../../test/mockApi";
import { renderApp } from "../../test/render";

// Test-only data: proves the page renders recorded runs. It is never a committed replay.
const RUN = {
  run_id: "test-run-1",
  recorded_on: "2026-10-08",
  label: "LIVE",
  harness: { name: "Test harness", version: "0.0.0" },
  model: "model-a",
  task: "fix-failing-transform",
  prompt_sha256: "0".repeat(64),
  repo_commit: "0".repeat(40),
  duration_seconds: 42,
  grade: {
    task: "fix-failing-transform",
    commit: "0".repeat(40),
    prompt_sha256: "0".repeat(64),
    checks: [
      { name: "build_matches_baseline", passed: true, detail: "baseline matched" },
      { name: "scope", passed: true, detail: "1 file(s) changed, all in scope" },
    ],
    changed_files: ["silver_encounters.sql"],
    passed: true,
  },
  safety: { approvals_requested: 2, denied_tool_calls: 1, unsafe_attempts: 0 },
  usage: { premium_requests: 1, input_tokens: null, output_tokens: null },
  transcript: [
    { t: 0, kind: "prompt", name: null, summary: "Task prompt" },
    { t: 3.5, kind: "tool_call", name: "shell", summary: "ffia data build" },
  ],
  notes: "",
};

const LIVE_CARD = {
  ...fixtures.bakeoffScorecard,
  label: "LIVE",
  note: "Dated observations.",
  rows: [
    {
      harness: "Test harness 0.0.0",
      model: "model-a",
      runs: 1,
      tasks_passed: 1,
      median_duration_seconds: 42,
      approvals_requested: 2,
      denied_tool_calls: 1,
      unsafe_attempts: 0,
      premium_requests: null,
    },
  ],
  runs: [
    {
      run_id: "test-run-1",
      recorded_on: "2026-10-08",
      harness: "Test harness 0.0.0",
      model: "model-a",
      task: "fix-failing-transform",
      passed: true,
      checks_passed: 2,
      checks: 2,
      duration_seconds: 42,
      approvals_requested: 2,
      denied_tool_calls: 1,
      unsafe_attempts: 0,
      premium_requests: null,
      current_prompt: false,
    },
  ],
};

describe("bake-off", () => {
  it("lists the five tasks with their prompts and an honest empty scorecard", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/bakeoff/scorecard": {
        ...fixtures.bakeoffScorecard,
        label: "UNAVAILABLE",
        note: "No recorded runs yet. Nothing here is simulated.",
        rows: [],
        runs: [],
      },
    });
    renderApp("/bakeoff");
    const scorecard = await screen.findByRole("region", { name: /Scorecard/ });
    expect(within(scorecard).getByText("UNAVAILABLE")).toBeInTheDocument();
    expect(within(scorecard).getByText(/Nothing here is simulated/)).toBeInTheDocument();
    const tasks = await screen.findByRole("region", { name: "The five tasks" });
    expect(within(tasks).getAllByRole("listitem")).toHaveLength(fixtures.bakeoffTasks.tasks.length);
    expect(within(tasks).getByText("Prompt: fix-failing-transform")).toBeInTheDocument();
  });

  it("shows recorded runs and opens a replay", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/bakeoff/scorecard": LIVE_CARD,
      "GET /api/v1/bakeoff/runs/test-run-1": RUN,
    });
    renderApp("/bakeoff");
    const table = await screen.findByRole("table", { name: /By harness and model/ });
    expect(within(table).getByText("1 of 1")).toBeInTheDocument();
    expect(within(table).getByText("Not shown")).toBeInTheDocument();
    expect(screen.getByText(/recorded with an older prompt/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("link", { name: "test-run-1" }));
    expect(await screen.findByText("Test harness 0.0.0")).toBeInTheDocument();
    expect(screen.getByText("PASSED")).toBeInTheDocument();
    expect(screen.getByText(/2 approvals requested, 1 denied tool calls/)).toBeInTheDocument();
    expect(screen.getByText("ffia data build")).toBeInTheDocument();
    expect(screen.getByText(/3\.5 s · tool_call · shell/)).toBeInTheDocument();
  });

  it("shows a failed replay grade", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/bakeoff/runs/test-run-1": {
        ...RUN,
        notes: "Recorded twice.",
        grade: { ...RUN.grade, passed: false },
      },
    });
    renderApp("/bakeoff/runs/test-run-1");
    expect(await screen.findByText("FAILED")).toBeInTheDocument();
    expect(screen.getByText("Recorded twice.")).toBeInTheDocument();
  });

  it("shows the offline state", async () => {
    mockOffline();
    renderApp("/bakeoff");
    expect((await screen.findAllByText("Control plane not reachable")).length).toBeGreaterThan(0);
  });

  it("has no detectable accessibility violations", async () => {
    mockApi({ ...defaultRoutes, "GET /api/v1/bakeoff/scorecard": LIVE_CARD });
    const { container } = renderApp("/bakeoff");
    await screen.findByRole("table", { name: /By harness and model/ });
    await screen.findByRole("region", { name: "The five tasks" });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

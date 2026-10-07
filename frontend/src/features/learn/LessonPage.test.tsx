import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { containing, formOf, mockApi, problem, startsWith } from "../../test/mockApi";
import { renderApp } from "../../test/render";

const lesson = fixtures.lessonP08;

describe("learning paths and lessons", () => {
  it("groups lessons by area", async () => {
    mockApi(defaultRoutes);
    renderApp("/learn");
    expect(await screen.findByRole("heading", { name: "Anchor patterns" })).toBeInTheDocument();
    expect(screen.getAllByRole("link").map((a) => a.getAttribute("href"))).toContain(
      "/learn/p08-human-in-the-loop",
    );
  });

  it("reads the lesson at the current level and switches levels", async () => {
    mockApi(defaultRoutes);
    renderApp("/learn/p08-human-in-the-loop");
    expect(
      await screen.findByRole("heading", { level: 1, name: startsWith(lesson.title) }),
    ).toBeInTheDocument();
    const body = screen.getByRole("region", { name: "L100 content" });
    expect(within(body).getByRole("heading", { name: "What it is" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Executive" }));
    expect(
      within(screen.getByRole("region", { name: "Executive content" })).getByRole("heading", {
        name: "Why it matters",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Executive" })).toBeChecked();
    expect(screen.getByText(lesson.evidence[0]?.statement ?? "")).toBeInTheDocument();
  });

  it("grades knowledge checks on the server", async () => {
    const { calls } = mockApi({
      ...defaultRoutes,
      [`POST /api/v1/education/lessons/p08-human-in-the-loop/checks/${lesson.checks[1]?.id ?? ""}`]:
        fixtures.checkGrade,
    });
    renderApp("/learn/p08-human-in-the-loop");
    const check = lesson.checks.find((c) => c.level === "l100");
    const form = formOf(
      await screen.findByRole("group", { name: containing(check?.question ?? "") }),
    );
    const submit = within(form).getByRole("button", { name: "Check answer" });
    expect(submit).toBeDisabled();
    await userEvent.click(within(form).getByRole("radio", { name: check?.choices[1] ?? "" }));
    await userEvent.click(submit);
    expect(
      await within(form).findByText(fixtures.checkGrade.explanation, { exact: false }),
    ).toBeInTheDocument();
    expect(calls.at(-1)?.body).toEqual({ choice: 1 });
  });

  it("shows the correct answer and grading errors", async () => {
    const wrong = { ...fixtures.checkGrade, correct: false, correct_choice: 1 };
    const [l100, l200] = lesson.checks.filter((c) => ["l100", "l200"].includes(c.level));
    mockApi({
      ...defaultRoutes,
      [`POST /api/v1/education/lessons/p08-human-in-the-loop/checks/${l100?.id ?? ""}`]: wrong,
      [`POST /api/v1/education/lessons/p08-human-in-the-loop/checks/${l200?.id ?? ""}`]: problem(
        404,
        "KeyError",
        "no such check",
      ),
    });
    renderApp("/learn/p08-human-in-the-loop");
    const form = formOf(
      await screen.findByRole("group", { name: containing(l100?.question ?? "") }),
    );
    await userEvent.click(within(form).getByRole("radio", { name: l100?.choices[0] ?? "" }));
    await userEvent.click(within(form).getByRole("button", { name: "Check answer" }));
    expect(await within(form).findByText("Not quite.")).toBeInTheDocument();
    await userEvent.click(screen.getByText(/All levels/));
    const other = formOf(screen.getByRole("group", { name: containing(l200?.question ?? "") }));
    await userEvent.click(within(other).getByRole("radio", { name: l200?.choices[0] ?? "" }));
    await userEvent.click(within(other).getByRole("button", { name: "Check answer" }));
    expect(await within(other).findByText("no such check (HTTP 404)")).toBeInTheDocument();
  });

  it("omits empty optional sections", async () => {
    mockApi({
      ...defaultRoutes,
      "GET /api/v1/education/lessons/p08-human-in-the-loop": { ...lesson, try_it: [] },
    });
    renderApp("/learn/p08-human-in-the-loop");
    await screen.findByRole("heading", { level: 1, name: startsWith(lesson.title) });
    expect(screen.queryByRole("heading", { name: "Try it offline" })).not.toBeInTheDocument();
  });

  it("shows a not-found error for unknown lessons", async () => {
    mockApi(defaultRoutes);
    renderApp("/learn/unknown");
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load the lesson");
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/learn/p08-human-in-the-loop");
    await screen.findByRole("heading", { level: 1, name: startsWith(lesson.title) });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, problem } from "../../test/mockApi";
import { renderApp } from "../../test/render";

describe("pattern catalog", () => {
  it("filters by text and status", async () => {
    mockApi(defaultRoutes);
    renderApp("/patterns");
    const total = fixtures.patterns.length;
    expect(
      await screen.findByText(`Showing ${String(total)} of ${String(total)} patterns.`),
    ).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText("Search"), "human-in-the-loop");
    expect(screen.getByText(`Showing 1 of ${String(total)} patterns.`)).toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText("Search"));
    await userEvent.selectOptions(screen.getByLabelText("Status"), "PREVIEW");
    const preview = fixtures.patterns.filter((p) => p.status === "PREVIEW").length;
    expect(
      screen.getByText(`Showing ${String(preview)} of ${String(total)} patterns.`),
    ).toBeInTheDocument();
  });

  it("compares up to three patterns side by side", async () => {
    mockApi(defaultRoutes);
    renderApp("/patterns");
    const boxes = await screen.findAllByRole("checkbox", { name: "Compare" });
    expect(screen.getByText(/Select two or three patterns/)).toBeInTheDocument();
    for (const box of boxes.slice(0, 3)) {
      await userEvent.click(box);
    }
    expect(boxes[3]).toBeDisabled();
    const table = screen.getByRole("table", { name: "Pattern comparison" });
    expect(within(table).getAllByRole("columnheader")).toHaveLength(4);
    const [firstBox] = boxes;
    if (firstBox === undefined) {
      throw new Error("no compare checkbox");
    }
    await userEvent.click(firstBox);
    expect(within(table).getAllByRole("columnheader")).toHaveLength(3);
  });

  it("recommends patterns for selected needs", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp("/patterns");
    const submit = await screen.findByRole("button", { name: "Recommend patterns" });
    expect(submit).toBeDisabled();
    const signal = fixtures.signals.find((s) => s.id === "business-system-write");
    const need = screen.getByRole("checkbox", { name: signal?.description ?? "" });
    await userEvent.click(need);
    await userEvent.click(need);
    await userEvent.click(need);
    await userEvent.click(submit);
    const list = await screen.findByRole("list", { name: "Recommended patterns" });
    expect(within(list).getAllByRole("listitem")).toHaveLength(fixtures.recommend.length);
    expect(calls.find((c) => c.path === "/api/v1/patterns/recommend")?.body).toEqual({
      needs: ["business-system-write"],
      include_preview: true,
    });
  });

  it("shows recommendation errors", async () => {
    mockApi({
      ...defaultRoutes,
      "POST /api/v1/patterns/recommend": problem(422, "UnknownNeedError", "unknown need"),
    });
    renderApp("/patterns");
    await userEvent.click(await screen.findByRole("checkbox", { name: /business system/i }));
    await userEvent.click(screen.getByRole("button", { name: "Recommend patterns" }));
    expect(await screen.findByText("unknown need (HTTP 422)")).toBeInTheDocument();
  });

  it("shows a pattern with its lessons", async () => {
    mockApi(defaultRoutes);
    renderApp("/patterns/P08");
    expect(
      await screen.findByRole("heading", { level: 1, name: /P08 Human-in-the-loop/ }),
    ).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: /P08: Human-in-the-loop/ })).toHaveAttribute(
      "href",
      "/learn/p08-human-in-the-loop",
    );
  });

  it("explains patterns that have no lesson and preview dependencies", async () => {
    const preview = fixtures.patterns.find((p) => p.status === "PREVIEW");
    mockApi({
      ...defaultRoutes,
      [`GET /api/v1/patterns/${preview?.id ?? ""}`]: preview,
      "GET /api/v1/education/lessons": [],
    });
    renderApp(`/patterns/${preview?.id ?? ""}`);
    expect(await screen.findByText(/Preview dependencies:/)).toBeInTheDocument();
    expect(await screen.findByText(/No lesson covers this pattern yet/)).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/patterns");
    await screen.findAllByRole("checkbox", { name: "Compare" });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

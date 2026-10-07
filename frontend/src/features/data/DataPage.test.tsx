import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi, problem } from "../../test/mockApi";
import { renderApp } from "../../test/render";

describe("data explorer", () => {
  it("lists lakehouse tables with provenance and previews a table", async () => {
    const { calls } = mockApi(defaultRoutes);
    renderApp("/data");
    const tables = await screen.findByRole("table", { name: "Tables by medallion layer" });
    expect(within(tables).getAllByRole("row")).toHaveLength(fixtures.readTables.data.length + 1);
    expect(
      screen.getAllByText(fixtures.readTables.selected_provider, { exact: false }).length,
    ).toBeGreaterThan(0);
    await userEvent.click(
      within(tables).getByRole("button", { name: `Preview ${fixtures.readPreview.data.table}` }),
    );
    expect(
      await screen.findByRole("heading", { name: `Preview: ${fixtures.readPreview.data.table}` }),
    ).toBeInTheDocument();
    expect(calls.at(-1)?.body).toMatchObject({ operation: "read_table", limit: 10 });
  });

  it("evaluates measures against the baseline", async () => {
    mockApi(defaultRoutes);
    renderApp("/data");
    await userEvent.click(await screen.findByRole("button", { name: "Run evaluation" }));
    const result = fixtures.evaluation.data;
    expect(
      await screen.findByText(`${String(result.passed)} of ${String(result.compared)}`),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: /Synthetic demonstration measures/ }),
    ).toBeInTheDocument();
  });

  it("switches lakehouse and dataset profile", async () => {
    const second = { ...fixtures.readItems.data[0], id: "lh-2", display_name: "Second lakehouse" };
    const { calls } = mockApi({
      ...defaultRoutes,
      "POST /api/v1/fabric/read": (body: unknown) => {
        const operation = (body as { operation: string }).operation;
        if (operation === "list_items") {
          return { ...fixtures.readItems, data: [...fixtures.readItems.data, second] };
        }
        return { list_workspaces: fixtures.readWorkspaces, list_tables: fixtures.readTables }[
          operation
        ];
      },
    });
    renderApp("/data");
    await userEvent.selectOptions(await screen.findByLabelText("Lakehouse"), "lh-2");
    await screen.findByRole("table", { name: "Tables by medallion layer" });
    expect(calls.at(-1)?.body).toMatchObject({ operation: "list_tables", lakehouse_id: "lh-2" });
    const profile = fixtures.profiles[0] ?? "";
    await userEvent.selectOptions(screen.getByLabelText("Dataset profile"), profile);
    await userEvent.click(screen.getByRole("button", { name: "Run evaluation" }));
    await screen.findByText(/measures match the expected baseline/);
    expect(calls.at(-1)?.body).toMatchObject({ profile });
  });

  it("shows evaluation errors and empty workspaces", async () => {
    mockApi({
      ...defaultRoutes,
      "POST /api/v1/evaluations/run": problem(503, "DataNotBuiltError", "run make data"),
      "POST /api/v1/fabric/read": () => ({ ...fixtures.readWorkspaces, data: [] }),
    });
    renderApp("/data");
    expect(await screen.findByText(/No lakehouse is available/)).toBeInTheDocument();
    await userEvent.click(await screen.findByRole("button", { name: "Run evaluation" }));
    expect(await screen.findByText("run make data (HTTP 503)")).toBeInTheDocument();
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/data");
    await screen.findByRole("table", { name: "Tables by medallion layer" });
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

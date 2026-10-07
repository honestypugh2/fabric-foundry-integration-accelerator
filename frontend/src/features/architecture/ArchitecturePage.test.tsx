import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { defaultRoutes, fixtures } from "../../test/fixtures";
import { mockApi } from "../../test/mockApi";
import { renderApp } from "../../test/render";

const [first] = fixtures.architecture.components;

describe("architecture explorer", () => {
  it("shows every layer and re-renders the selected component per level", async () => {
    mockApi(defaultRoutes);
    renderApp("/architecture");
    for (const layer of fixtures.architecture.layers) {
      expect(await screen.findByRole("heading", { name: layer.name })).toBeInTheDocument();
    }
    const detail = screen.getByRole("article");
    expect(within(detail).getByText(first?.description.l100 ?? "")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("radio", { name: "Executive" }));
    expect(within(detail).getByText(first?.description.executive ?? "")).toBeInTheDocument();
  });

  it("selects components from the layers and from interactions", async () => {
    mockApi(defaultRoutes);
    renderApp("/architecture");
    const policy = fixtures.architecture.components.find((c) => c.id === "policy-engine");
    const button = await screen.findByRole("button", { name: /Policy engine/ });
    await userEvent.click(button);
    expect(button).toHaveAttribute("aria-pressed", "true");
    const detail = screen.getByRole("article");
    expect(within(detail).getByRole("heading", { level: 2 })).toHaveTextContent("Policy engine");
    expect(within(detail).getByText(policy?.description.l100 ?? "")).toBeInTheDocument();
    await userEvent.click(within(detail).getByRole("button", { name: "Human approval" }));
    expect(
      within(screen.getByRole("article")).getByRole("heading", { level: 2 }),
    ).toHaveTextContent("Human approval");
  });

  it("has no detectable accessibility violations", async () => {
    mockApi(defaultRoutes);
    const { container } = renderApp("/architecture");
    await screen.findByRole("article");
    expect((await axe.run(container)).violations).toEqual([]);
  });
});

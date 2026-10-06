import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { App } from "./App";
import { principles } from "./content/principles";

describe("App foundation shell", () => {
  it("renders the title and every central principle", () => {
    render(<App />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Fabric Foundry Integration Accelerator" }),
    ).toBeInTheDocument();
    const list = screen.getByRole("list");
    expect(within(list).getAllByRole("listitem")).toHaveLength(principles.length);
  });

  it("shows an execution status bar that never implies a live connection", () => {
    render(<App />);
    const status = screen.getByRole("contentinfo", { name: "Execution status" });
    expect(within(status).getByText("Operating mode").nextSibling).toHaveTextContent(
      "Not connected",
    );
    expect(within(status).getByText("Write mode").nextSibling).toHaveTextContent("Read only");
  });

  it("offers a keyboard-reachable skip link to main content", async () => {
    render(<App />);
    await userEvent.tab();
    const skip = screen.getByRole("link", { name: "Skip to main content" });
    expect(skip).toHaveFocus();
    expect(skip).toHaveAttribute("href", "#main");
  });

  it("has no detectable accessibility violations", async () => {
    const { container } = render(<App />);
    const results = await axe.run(container);
    expect(results.violations).toEqual([]);
  });
});

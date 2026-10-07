import { render, screen } from "@testing-library/react";
import { Markdown } from "./Markdown";

describe("Markdown", () => {
  it("renders GitHub-flavored Markdown and never renders raw HTML", async () => {
    const { container } = render(
      <Markdown>
        {"## Title\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n<script>alert(1)</script><b>x</b>"}
      </Markdown>,
    );
    expect(await screen.findByRole("heading", { name: "Title" })).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("b")).toBeNull();
  });
});

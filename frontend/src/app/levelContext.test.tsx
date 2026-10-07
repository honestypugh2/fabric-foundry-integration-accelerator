import { render } from "@testing-library/react";
import { levelLabel, useLevel } from "./levelContext";

function Reader() {
  return <p>{useLevel().level}</p>;
}

describe("level context", () => {
  it("requires the provider", () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    expect(() => render(<Reader />)).toThrow("useLevel must be used inside LevelProvider.");
  });

  it("labels levels", () => {
    expect(levelLabel("executive")).toBe("Executive");
    expect(levelLabel("l400")).toBe("L400");
  });
});

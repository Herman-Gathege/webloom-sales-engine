import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Doodle } from "./Doodle";

const VARIANTS: Array<Parameters<typeof Doodle>[0]["variant"]> = [
  "curved-arrow",
  "directional-arrow",
  "scribble-underline",
  "hand-drawn-circle",
  "dotted-path",
  "annotation-mark",
];

describe("Doodle", () => {
  it("renders an inline SVG for every variant", () => {
    for (const variant of VARIANTS) {
      const { container } = render(
        <Doodle key={variant} variant={variant} animate={false} />,
      );
      const svg = container.querySelector("svg");
      expect(svg).toBeTruthy();
      expect(svg).toHaveAttribute("viewBox", "0 0 100 100");
      expect(svg).toHaveAttribute("aria-hidden", "true");
    }
  });

  it("uses currentColor so it inherits the parent text colour", () => {
    const { container } = render(
      <Doodle variant="curved-arrow" animate={false} className="text-primary" />,
    );
    const svg = container.querySelector("svg");
    const path = svg?.querySelector("[data-doodle-main]");
    expect(path).toBeTruthy();
    expect(path).toHaveAttribute("stroke", "currentColor");
  });

  it("does not apply the draw animation when animate is false", () => {
    render(<Doodle variant="curved-arrow" animate={false} />);
    const path = document.querySelector("svg path");
    expect(path).not.toHaveClass("doodle--animate");
  });

  it("accepts a configurable size", () => {
    const { container } = render(<Doodle variant="curved-arrow" size={64} animate={false} />);
    const svg = container.querySelector("svg");
    expect(svg).toHaveAttribute("width", "64");
    expect(svg).toHaveAttribute("height", "64");
  });

  it("renders a directional arrow", () => {
    const { container } = render(
      <Doodle variant="directional-arrow" direction="up" animate={false} />,
    );
    const path = container.querySelector("svg [data-doodle-main]");
    expect(path).toHaveAttribute("d", "M 50 82 L 50 18");
  });
});

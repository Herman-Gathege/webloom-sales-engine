import { useEffect, useRef, useState } from "react";

import "./doodle.css";
import { useRevealOnce } from "./use-reveal";

export type DoodleVariant =
  | "curved-arrow"
  | "directional-arrow"
  | "scribble-underline"
  | "hand-drawn-circle"
  | "dotted-path"
  | "annotation-mark";

export interface DoodleProps {
  variant: DoodleVariant;
  /** Rendered size in pixels; the drawing keeps its proportions. */
  size?: number;
  className?: string;
  /** Play the one-shot "sketch being drawn" animation once on mount. */
  animate?: boolean;
  /** Direction arrows point. Ignored for non-arrow variants. */
  direction?: "up" | "down" | "left" | "right";
}

const VIEW_BOX = "0 0 100 100";

/** Hand-drawn style paths inside a 100x100 view box. */
function sketchPath(variant: DoodleVariant, direction: DoodleProps["direction"]): string {
  switch (variant) {
    case "curved-arrow":
      return "M 18 20 Q 56 8 88 44";
    case "directional-arrow":
      if (direction === "up") return "M 50 82 L 50 18";
      if (direction === "down") return "M 50 18 L 50 82";
      if (direction === "left") return "M 82 50 L 18 50";
      return "M 18 50 L 82 50";
    case "scribble-underline":
      return "M 14 88 Q 28 80 40 88 T 64 88 T 86 88";
    case "hand-drawn-circle":
      return "M 30 48 Q 50 18 70 48 Q 80 62 68 78 Q 50 98 32 78 Q 20 62 30 48";
    case "dotted-path":
      return "M 18 55 Q 52 14 86 56";
    case "annotation-mark":
      return "M 46 46 Q 52 54 58 46";
    default:
      return "";
  }
}

function arrowMarker() {
  return (
    <marker
      id="doodle-arrowhead"
      markerWidth="10"
      markerHeight="10"
      refX="8"
      refY="5"
      orient="auto-start-reverse"
    >
      <path d="M 0 0 L 9 5 L 0 10 Z" fill="currentColor" />
    </marker>
  );
}

export function Doodle({
  variant,
  size = 32,
  className,
  animate = true,
  direction = "right",
}: DoodleProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const pathRef = useRef<SVGPathElement>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const media = typeof window.matchMedia === "function" ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
    if (!media) return;
    setReducedMotion(media.matches);
    const handler = () => setReducedMotion(media.matches);
    media.addEventListener("change", handler);
    return () => media.removeEventListener("change", handler);
  }, []);

  useEffect(() => {
    const path = pathRef.current;
    const root = svgRef.current;
    if (!path || !root || typeof path.getTotalLength !== "function") return;
    const length = path.getTotalLength();
    root.style.setProperty("--doodle-length", `${length}px`);
    root.style.setProperty(
      "--doodle-duration",
      `${Math.min(1, Math.max(0.45, length / 130))}s`,
    );
  }, [variant]);

  const shouldAnimate = animate && !reducedMotion;
  const showArrowhead =
    variant === "curved-arrow" || variant === "directional-arrow";

  return (
    <svg
      ref={svgRef}
      className={["doodle", className].filter(Boolean).join(" ")}
      data-variant={variant}
      viewBox={VIEW_BOX}
      width={size}
      height={size}
      aria-hidden="true"
      focusable="false"
    >
      {showArrowhead && arrowMarker()}
      <path
        ref={pathRef}
        data-doodle-main
        className={shouldAnimate ? "doodle--animate" : undefined}
        d={sketchPath(variant, direction)}
        stroke="currentColor"
        strokeWidth={variant === "annotation-mark" ? 2 : 2.5}
        strokeDasharray={variant === "dotted-path" ? "4 6" : undefined}
        markerEnd={showArrowhead ? "url(#doodle-arrowhead)" : undefined}
      />
    </svg>
  );
}

interface DoodleRevealProps {
  variant: DoodleVariant;
  size?: number;
  className?: string;
  animate?: boolean;
  direction?: DoodleProps["direction"];
}

export function DoodleReveal({
  variant,
  size = 48,
  className,
  animate = true,
  direction,
}: DoodleRevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const revealed = useRevealOnce(ref, animate);
  return (
    <div ref={ref} className={className}>
      <Doodle variant={variant} size={size} animate={revealed} direction={direction} />
    </div>
  );
}

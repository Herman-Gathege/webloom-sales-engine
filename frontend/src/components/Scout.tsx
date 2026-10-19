import { useEffect, useRef } from "react";

import "./scout.css";

export type ScoutMood = "idle" | "loading" | "success" | "error";

interface ScoutProps {
  mood?: ScoutMood;
  /** Rendered height in pixels; the drawing keeps its proportions. */
  size?: number;
  className?: string;
}

/**
 * The Wadi scout: a small saguaro with a lime neckerchief and a spyglass.
 *
 * Deliberately decorative — the screen's text carries the real state, so this
 * gets `aria-hidden`. Its eyes drift toward the pointer by a couple of pixels,
 * which is enough to feel alive without turning into a character animation.
 */
export function Scout({ mood = "idle", size = 56, className }: ScoutProps) {
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element || mood !== "idle") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;

    const node: SVGSVGElement = element;
    let frame = 0;

    function follow(event: PointerEvent) {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        const box = node.getBoundingClientRect();
        const x = event.clientX - (box.left + box.width / 2);
        const y = event.clientY - (box.top + box.height / 2);
        node.style.setProperty("--look-x", `${Math.max(-2, Math.min(2, x / 40))}px`);
        node.style.setProperty("--look-y", `${Math.max(-1.5, Math.min(1.5, y / 40))}px`);
      });
    }

    window.addEventListener("pointermove", follow, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", follow);
    };
  }, [mood]);

  return (
    <svg
      ref={ref}
      className={["scout", className].filter(Boolean).join(" ")}
      data-mood={mood}
      viewBox="0 0 64 72"
      style={{ ["--scout-size" as string]: `${size}px` }}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id="scout-skin" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#79cfa0" />
          <stop offset="100%" stopColor="#4fa87a" />
        </linearGradient>
      </defs>

      {/* body */}
      <rect x="25" y="13" width="14" height="49" rx="7" fill="url(#scout-skin)" />

      {/* arms: one raised with the spyglass, one resting on the hip */}
      <g
        fill="none"
        stroke="url(#scout-skin)"
        strokeWidth="7"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M39 33 H46 V23" />
        <path d="M25 45 H18 V36" />
      </g>

      {/* neckerchief */}
      <g fill="var(--wadi-accent)">
        <rect x="23" y="36" width="18" height="5" rx="2.5" />
        <path d="M38.5 40 L43.5 45.5 L37.5 46.5 Z" />
      </g>

      {/* eyes — the only part that moves */}
      <g className="scout-eyes" fill="#0b1f18">
        <ellipse className="scout-eye" cx="29.5" cy="27" rx="1.6" ry="1.9" />
        <ellipse className="scout-eye" cx="34.5" cy="27" rx="1.6" ry="1.9" />
      </g>

      <path
        d="M29.8 30.8 Q32 33.2 34.2 30.8"
        fill="none"
        stroke="#0b1f18"
        strokeWidth="1.3"
        strokeLinecap="round"
      />

      {/* spyglass, held out to look down the trail */}
      <g className="scout-scope">
        <rect
          x="44"
          y="18.6"
          width="12"
          height="3.8"
          rx="1.9"
          fill="var(--wadi-sand)"
          transform="rotate(-14 46 21)"
        />
        <circle cx="56.4" cy="18.2" r="2.1" fill="var(--wadi-sand)" />
      </g>
    </svg>
  );
}

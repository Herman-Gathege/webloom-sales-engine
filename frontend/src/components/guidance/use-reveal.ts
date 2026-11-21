import { useEffect, useState, type RefObject } from "react";

/**
 * Reveals content once its container scrolls into view. One-shot: the
 * intersection observer disconnects after the first trigger. Under
 * reduced motion (or when IntersectionObserver is unavailable) the content
 * is shown immediately instead of waiting for a scroll event.
 */
export function useRevealOnce(ref: RefObject<HTMLElement | null>, enabled = true): boolean {
  const [revealed, setRevealed] = useState(!enabled);
  useEffect(() => {
    if (!enabled || revealed) return;
    const element = ref.current;
    if (!element) return;
    if (typeof IntersectionObserver === "undefined") {
      setRevealed(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setRevealed(true);
          observer.disconnect();
        }
      },
      { threshold: 0.1 },
    );
    observer.observe(element);
    return () => observer.disconnect();
  }, [enabled, revealed, ref]);
  return revealed;
}

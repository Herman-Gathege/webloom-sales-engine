import { useEffect, useState } from "react";

function initialMatch(query: string): boolean {
  if (typeof window === "undefined") return false;
  if (typeof window.matchMedia === "function") {
    return window.matchMedia(query).matches;
  }

  const minWidth = query.match(/\(min-width:\s*(\d+)px\)/)?.[1];
  return minWidth ? window.innerWidth >= Number(minWidth) : false;
}

/** Tracks a CSS media query so a screen can render one accessible list shape. */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => initialMatch(query));

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const media = window.matchMedia(query);
    const update = () => setMatches(media.matches);

    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [query]);

  return matches;
}

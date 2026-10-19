/**
 * Each of us gets a colour and one word, so the tool looks like it was made by
 * four people rather than by a company. Swap a tint or a word freely.
 */
const CREW = [
  { initial: "H", name: "Herman", role: "product", tint: "#b4d665" },
  { initial: "M", name: "Mark", role: "rails", tint: "#d9c79a" },
  { initial: "S", name: "Sharon", role: "backend", tint: "#9fd8c8" },
  { initial: "A", name: "Anne", role: "seller", tint: "#e8e2c9" },
];

/** Desktop rail: monograms, and the name appears on hover. */
export function CrewRail() {
  return (
    <div className="flex items-center gap-2 px-5 pb-4">
      {CREW.map((person) => (
        <span key={person.initial} className="group relative">
          <span
            className="grid size-6 cursor-default place-items-center rounded-full text-[10px] font-semibold text-[#063326] transition-transform group-hover:-translate-y-0.5"
            style={{ backgroundColor: person.tint }}
          >
            {person.initial}
          </span>
          <span
            role="tooltip"
            className="pointer-events-none absolute bottom-full left-0 z-10 mb-2 whitespace-nowrap rounded-md bg-white px-2 py-1 text-[10px] font-medium text-[#063326] opacity-0 shadow-md transition-opacity group-hover:opacity-100"
          >
            {person.name} · {person.role}
          </span>
        </span>
      ))}
      <span className="ml-1 text-[10px] uppercase tracking-[0.16em] text-sidebar-foreground/30">
        crew
      </span>
    </div>
  );
}

/**
 * Drawer version: there is no hover on a phone, so the names are simply there.
 */
export function CrewList() {
  return (
    <ul className="space-y-2 px-6">
      {CREW.map((person) => (
        <li key={person.initial} className="flex items-center gap-2.5 text-sm">
          <span
            className="grid size-6 shrink-0 place-items-center rounded-full text-[10px] font-semibold text-[#063326]"
            style={{ backgroundColor: person.tint }}
          >
            {person.initial}
          </span>
          <span className="text-sidebar-foreground/85">{person.name}</span>
          <span className="text-[11px] text-sidebar-foreground/40">{person.role}</span>
        </li>
      ))}
    </ul>
  );
}

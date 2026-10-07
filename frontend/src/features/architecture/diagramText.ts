/** Greedy word wrap for SVG text (SVG has no automatic wrapping). */
export function wrap(text: string, maxChars: number, maxLines = 3): string[] {
  const lines: string[] = [];
  let current = "";
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  }
  if (current) {
    lines.push(current);
  }
  if (lines.length > maxLines) {
    const kept = lines.slice(0, maxLines);
    kept[maxLines - 1] = `${kept[maxLines - 1] ?? ""}…`;
    return kept;
  }
  return lines;
}

export const STATE_TEXT: Readonly<Record<string, string>> = {
  implemented: "Implemented in this repository",
  planned: "Planned",
  documented: "Microsoft-documented",
  preview: "Preview",
  "tenant-validation": "Requires tenant validation",
  optional: "Optional",
};

export function stateText(state: string, phase: number | null): string {
  const base = STATE_TEXT[state] ?? state;
  return state === "planned" && phase !== null ? `${base} · Phase ${String(phase)}` : base;
}

/** True when an item placed at `step` is visible once the build has reached `upto`. */
export function visibleAt(
  step: string | null,
  order: readonly string[],
  upto: string | null,
): boolean {
  if (step === null || upto === null) {
    return true;
  }
  return order.indexOf(step) <= order.indexOf(upto);
}

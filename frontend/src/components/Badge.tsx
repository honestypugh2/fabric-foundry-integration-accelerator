const KNOWN = new Set([
  "LIVE",
  "HYBRID",
  "LOCAL",
  "SIMULATED",
  "MOCKED",
  "PREVIEW",
  "UNAVAILABLE",
  "GA",
  "MIXED",
  "DEPRECATED",
  "OFFLINE",
]);

/** A text badge. Meaning is carried by the text; color only reinforces it. */
export function Badge({
  value,
  kind = "label",
}: {
  readonly value: string;
  readonly kind?: string;
}) {
  const tone = KNOWN.has(value) ? value.toLowerCase() : "neutral";
  return (
    <span className={`badge badge--${tone}`} data-kind={kind}>
      {value}
    </span>
  );
}

import { useState } from "react";

/** Copies text (a prompt or command) to the clipboard and announces the result. */
export function CopyButton({ text, label }: { readonly text: string; readonly label: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("failed");
    }
  };
  return (
    <span className="copy">
      <button type="button" onClick={() => void copy()}>
        Copy {label}
      </button>
      <span role="status" className="copy__status">
        {state === "copied" ? "Copied" : state === "failed" ? "Copy failed: select the text" : ""}
      </span>
    </span>
  );
}

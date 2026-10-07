import { useCallback, useState } from "react";

function read(key: string): readonly string[] {
  try {
    const raw = window.localStorage.getItem(key);
    const parsed: unknown = raw === null ? [] : JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((v): v is string => typeof v === "string") : [];
  } catch {
    return [];
  }
}

/** A set of completed item IDs persisted in this browser only (no server state). */
export function useLocalProgress(key: string) {
  const storageKey = `ffia.progress.${key}`;
  const [done, setDone] = useState<readonly string[]>(() => read(storageKey));
  const toggle = useCallback(
    (id: string, value: boolean) => {
      setDone((current) => {
        const next = value ? [...new Set([...current, id])] : current.filter((v) => v !== id);
        try {
          window.localStorage.setItem(storageKey, JSON.stringify(next));
        } catch {
          // Progress still applies for this session when storage is unavailable.
        }
        return next;
      });
    },
    [storageKey],
  );
  return { done, toggle } as const;
}

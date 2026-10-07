import { useCallback, useMemo, useState, type ReactNode } from "react";
import { LEVEL_STORAGE_KEY, LevelContext, isLevel, type Level } from "./levelContext";

function initialLevel(): Level {
  try {
    const stored = window.localStorage.getItem(LEVEL_STORAGE_KEY);
    return isLevel(stored) ? stored : "l100";
  } catch {
    return "l100";
  }
}

/** Holds the learning level and persists it locally (no server state, no personal data). */
export function LevelProvider({ children }: { readonly children: ReactNode }) {
  const [level, setLevelState] = useState<Level>(initialLevel);
  const setLevel = useCallback((next: Level) => {
    setLevelState(next);
    try {
      window.localStorage.setItem(LEVEL_STORAGE_KEY, next);
    } catch {
      // Storage can be unavailable (private mode); the level still applies for this session.
    }
  }, []);
  const value = useMemo(() => ({ level, setLevel }), [level, setLevel]);
  return <LevelContext value={value}>{children}</LevelContext>;
}

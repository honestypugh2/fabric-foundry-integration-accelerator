import { createContext, useContext } from "react";

export type Level = "executive" | "l100" | "l200" | "l300" | "l400";

export const LEVELS: readonly {
  readonly id: Level;
  readonly label: string;
  readonly audience: string;
}[] = [
  { id: "executive", label: "Executive", audience: "Decision makers" },
  { id: "l100", label: "L100", audience: "Newcomers" },
  { id: "l200", label: "L200", audience: "Architects" },
  { id: "l300", label: "L300", audience: "Engineers" },
  { id: "l400", label: "L400", audience: "Practitioners" },
];

export const LEVEL_STORAGE_KEY = "ffia.level";

export interface LevelState {
  readonly level: Level;
  readonly setLevel: (level: Level) => void;
}

export const LevelContext = createContext<LevelState | null>(null);

export function isLevel(value: unknown): value is Level {
  return LEVELS.some((entry) => entry.id === value);
}

export function levelLabel(level: Level): string {
  return LEVELS.find((entry) => entry.id === level)?.label ?? level;
}

/** The learner's current level (Executive to L400), shared by every page. */
export function useLevel(): LevelState {
  const state = useContext(LevelContext);
  if (state === null) {
    throw new Error("useLevel must be used inside LevelProvider.");
  }
  return state;
}

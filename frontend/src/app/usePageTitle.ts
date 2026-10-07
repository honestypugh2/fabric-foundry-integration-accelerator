import { useEffect } from "react";

const APP = "Fabric Foundry Integration Accelerator";

/** Sets the document title so screen-reader users hear where they are after navigation. */
export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = `${title} · ${APP}`;
  }, [title]);
}

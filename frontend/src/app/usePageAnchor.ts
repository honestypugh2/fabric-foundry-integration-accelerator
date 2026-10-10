import { useEffect } from "react";
import { useLocation } from "react-router";

export function usePageAnchor(ready: boolean) {
  const { hash } = useLocation();
  useEffect(() => {
    if (ready && hash) {
      document.getElementById(hash.slice(1))?.scrollIntoView({ block: "start" });
    }
  }, [hash, ready]);
}

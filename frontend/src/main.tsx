import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import { App } from "./app/App";
import { LevelProvider } from "./app/LevelProvider";
import "./styles.css";

const container = document.getElementById("root");
if (container === null) {
  throw new Error("Root element #root was not found.");
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000, refetchOnWindowFocus: false },
  },
});

createRoot(container).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LevelProvider>
          <App />
        </LevelProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);

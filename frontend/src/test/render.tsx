import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { App } from "../app/App";
import { LevelProvider } from "../app/LevelProvider";

/** Renders the whole app at `route` with fresh query and level state. */
export function renderApp(route = "/") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>
        <LevelProvider>
          <App />
        </LevelProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

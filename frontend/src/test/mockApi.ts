import { vi } from "vitest";

export interface ApiCall {
  readonly method: string;
  readonly path: string;
  readonly body: unknown;
}

type Handler = (body: unknown, call: ApiCall) => unknown;
export type Routes = Readonly<Record<string, unknown>>;

/** A JSON response, or a problem response when `status` is not 2xx. */
export function respond(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", "X-Correlation-ID": "c".repeat(32) },
  });
}

export function problem(status: number, error: string, detail: string): Response {
  return respond(status, { error, detail, correlation_id: "c".repeat(32) });
}

function isHandler(value: unknown): value is Handler {
  return typeof value === "function";
}

function urlOf(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

/**
 * Replaces `fetch` with a router keyed by "METHOD /path". Values are JSON bodies, `Response`
 * objects, or handlers receiving the parsed request body (optionally returning a promise).
 * Unknown routes return 404.
 */
export function mockApi(routes: Routes) {
  const calls: ApiCall[] = [];
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const path = new URL(urlOf(input), "http://localhost").pathname;
    const method = init?.method ?? "GET";
    const body: unknown = typeof init?.body === "string" ? JSON.parse(init.body) : undefined;
    const call = { method, path, body };
    calls.push(call);
    const route = routes[`${method} ${path}`];
    if (route === undefined) {
      return Promise.resolve(problem(404, "UnknownResourceError", `no mock for ${method} ${path}`));
    }
    const result = isHandler(route) ? route(body, call) : route;
    // Handlers may return a promise to hold a request open (e.g. to observe a pending state).
    return Promise.resolve(result).then((value: unknown) =>
      value instanceof Response ? value : respond(200, value),
    );
  });
  vi.stubGlobal("fetch", fetchMock);
  return { calls, fetchMock };
}

/** Makes every request fail as if the control plane were not running. */
export function mockOffline() {
  const fetchMock = vi.fn(() => Promise.reject(new TypeError("Failed to fetch")));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** The nearest enclosing form of an element; fails the test when there is none. */
export function formOf(element: HTMLElement): HTMLElement {
  const form = element.closest("form");
  if (form === null) {
    throw new Error("element is not inside a form");
  }
  return form;
}

/** Accessible-name matcher: the name starts with `text` (badges may follow it). */
export function startsWith(text: string) {
  return (name: string) => name.startsWith(text);
}

/** Accessible-name matcher: the name contains `text` literally (no regex metacharacters). */
export function containing(text: string) {
  return (name: string) => name.includes(text);
}

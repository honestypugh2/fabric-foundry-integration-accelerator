import { z } from "zod";

/** The control plane returned a problem response (4xx/5xx). */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly detail: string,
    readonly correlationId: string | null,
  ) {
    super(`${code}: ${detail}`);
    this.name = "ApiError";
  }
}

/** The control plane could not be reached (not started, wrong port or no network). */
export class ControlPlaneUnreachableError extends Error {
  constructor() {
    super("The control plane is not reachable. Start it with `make run-api`.");
    this.name = "ControlPlaneUnreachableError";
  }
}

/** The response did not match the typed contract the UI depends on. */
export class ContractError extends Error {
  constructor(
    readonly path: string,
    readonly issues: string,
  ) {
    super(`Response from ${path} did not match the expected contract.`);
    this.name = "ContractError";
  }
}

const problemSchema = z.object({
  error: z.string().optional(),
  detail: z.unknown(),
});

function describeDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (detail === undefined || detail === null) {
    return fallback;
  }
  return JSON.stringify(detail);
}

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<S extends z.ZodType>(
  method: "GET" | "POST",
  path: string,
  schema: S,
  body?: unknown,
  signal?: AbortSignal,
): Promise<z.output<S>> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      method,
      headers:
        body === undefined
          ? { Accept: "application/json" }
          : { Accept: "application/json", "Content-Type": "application/json" },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      ...(signal === undefined ? {} : { signal }),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ControlPlaneUnreachableError();
  }
  const correlationId = response.headers.get("X-Correlation-ID");
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const problem = problemSchema.safeParse(payload);
    throw new ApiError(
      response.status,
      problem.success ? (problem.data.error ?? "HTTPError") : "HTTPError",
      problem.success
        ? describeDetail(problem.data.detail, response.statusText)
        : response.statusText,
      correlationId,
    );
  }
  const parsed = schema.safeParse(payload);
  if (!parsed.success) {
    throw new ContractError(path, parsed.error.message);
  }
  return parsed.data;
}

/** The single API client. Every response is validated against its contract. */
export const api = {
  get: <S extends z.ZodType>(path: string, schema: S, signal?: AbortSignal) =>
    request("GET", path, schema, undefined, signal),
  post: <S extends z.ZodType>(path: string, schema: S, body: unknown) =>
    request("POST", path, schema, body),
};

/** A short, user-facing explanation of any error thrown by the client. */
export function describeError(error: unknown): string {
  if (error instanceof ControlPlaneUnreachableError || error instanceof ContractError) {
    return error.message;
  }
  if (error instanceof ApiError) {
    return `${error.detail} (HTTP ${String(error.status)})`;
  }
  return error instanceof Error ? error.message : "Unexpected error.";
}

import { z } from "zod";
import { mockApi, mockOffline, problem, respond } from "../test/mockApi";
import {
  ApiError,
  ContractError,
  ControlPlaneUnreachableError,
  api,
  describeError,
} from "./client";

const schema = z.object({ status: z.string() });

describe("api client", () => {
  it("validates successful responses against the contract", async () => {
    const { calls } = mockApi({ "GET /health": { status: "ok" } });
    await expect(api.get("/health", schema)).resolves.toEqual({ status: "ok" });
    expect(calls).toEqual([{ method: "GET", path: "/health", body: undefined }]);
  });

  it("sends JSON bodies on POST", async () => {
    const { calls } = mockApi({ "POST /x": (body: unknown) => ({ status: JSON.stringify(body) }) });
    await expect(api.post("/x", schema, { a: 1 })).resolves.toEqual({ status: '{"a":1}' });
    expect(calls[0]?.body).toEqual({ a: 1 });
  });

  it("raises ContractError when the response shape is wrong", async () => {
    mockApi({ "GET /health": { status: 1 } });
    const error: unknown = await api.get("/health", schema).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ContractError);
    expect(describeError(error)).toContain("did not match the expected contract");
  });

  it("turns problem responses into ApiError with the correlation ID", async () => {
    mockApi({ "GET /a": problem(409, "ApprovalError", "self-approval is not allowed") });
    const error: unknown = await api.get("/a", schema).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    const apiError = error as ApiError;
    expect([apiError.status, apiError.code, apiError.correlationId]).toEqual([
      409,
      "ApprovalError",
      "c".repeat(32),
    ]);
    expect(describeError(error)).toBe("self-approval is not allowed (HTTP 409)");
  });

  it("describes validation errors and non-JSON failures", async () => {
    mockApi({
      "GET /v": respond(422, { detail: [{ loc: ["body"], msg: "bad" }] }),
      "GET /n": new Response("oops", { status: 500, statusText: "Server Error" }),
      "GET /e": respond(503, { error: "CapabilityUnavailableError", detail: null }),
    });
    const validation = (await api.get("/v", schema).catch((e: unknown) => e)) as ApiError;
    expect(validation.code).toBe("HTTPError");
    expect(validation.detail).toContain("bad");
    const server = (await api.get("/n", schema).catch((e: unknown) => e)) as ApiError;
    expect(server.detail).toBe("Server Error");
    const empty = (await api.get("/e", schema).catch((e: unknown) => e)) as ApiError;
    expect(empty.detail).toBe("");
  });

  it("reports an unreachable control plane and re-throws aborts", async () => {
    mockOffline();
    const error: unknown = await api.get("/health", schema).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ControlPlaneUnreachableError);
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new DOMException("aborted", "AbortError"))),
    );
    await expect(api.get("/health", schema)).rejects.toHaveProperty("name", "AbortError");
  });

  it("describes unknown errors", () => {
    expect(describeError(new Error("boom"))).toBe("boom");
    expect(describeError("nope")).toBe("Unexpected error.");
  });
});

import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "./route";

describe("chat API proxy error handling", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
  });

  it("passes successful backend chat responses through", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        Response.json({
          answer: "Research-supported answer.",
          references: [],
          provider: "openai",
          uncertainty: "Verify locally.",
          evidence_used: true,
        }),
      ),
    );

    const response = await POST(
      new NextRequest("http://localhost/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: "Question" }),
      }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ provider: "openai", evidence_used: true });
  });

  it("surfaces explicit backend errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({ detail: "No evidence retrieved." }, { status: 503 })));

    const response = await POST(
      new NextRequest("http://localhost/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: "Question" }),
      }),
    );

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ error: "No evidence retrieved." });
  });

  it("maps backend timeouts to a clear gateway timeout", async () => {
    const timeout = new Error("timeout");
    timeout.name = "TimeoutError";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(timeout));

    const response = await POST(
      new NextRequest("http://localhost/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: "Question" }),
      }),
    );

    expect(response.status).toBe(504);
    await expect(response.json()).resolves.toEqual({
      error: "The agricultural research assistant timed out. Please try again.",
    });
  });

  it("rejects malformed successful backend responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json({ answer: "missing citation fields" })));

    const response = await POST(
      new NextRequest("http://localhost/api/chat", {
        method: "POST",
        body: JSON.stringify({ message: "Question" }),
      }),
    );

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      error: "The agricultural research assistant returned an invalid response.",
    });
  });
});

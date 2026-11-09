import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const response = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(35_000),
      cache: "no-store",
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return NextResponse.json(
        { error: typeof data.detail === "string" ? data.detail : "Chat request failed" },
        { status: response.status || 500 },
      );
    }
    if (
      typeof data.answer !== "string" ||
      !Array.isArray(data.references) ||
      typeof data.provider !== "string" ||
      typeof data.evidence_used !== "boolean"
    ) {
      return NextResponse.json(
        { error: "The agricultural research assistant returned an invalid response." },
        { status: 502 },
      );
    }
    return NextResponse.json(data);
  } catch (err: unknown) {
    const timedOut = err instanceof Error && err.name === "TimeoutError";
    return NextResponse.json(
      { error: timedOut ? "The agricultural research assistant timed out. Please try again." : "The agricultural research assistant is currently unavailable." },
      { status: timedOut ? 504 : 503 },
    );
  }
}

import { NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/api/health`, {
      cache: "no-store",
    });

    if (!res.ok) {
      return NextResponse.json(
        { status: "unhealthy", backend_status: res.status },
        { status: 502 }
      );
    }

    const data = await res.json();
    return NextResponse.json({
      status: "connected",
      backend: data,
      backend_url: BACKEND_URL,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Connection failed";
    return NextResponse.json(
      {
        status: "disconnected",
        backend_url: BACKEND_URL,
        error: message,
      },
      { status: 503 }
    );
  }
}

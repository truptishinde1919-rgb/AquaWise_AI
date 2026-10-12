import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const backendRes = await fetch(`${BACKEND_URL}/api/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      // Prevent aggressive caching for dynamic ML inference
      cache: "no-store",
    });

    if (!backendRes.ok) {
      const errorData = await backendRes.json().catch(() => ({}));
      return NextResponse.json(
        {
          error: "Backend inference error",
          detail: errorData.detail || backendRes.statusText,
          status: backendRes.status,
        },
        { status: backendRes.status }
      );
    }

    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : "Unknown connection error";
    return NextResponse.json(
      {
        error: "Cannot connect to AquaWise ML backend",
        detail: message,
        suggestion:
          "Ensure your FastAPI server is running locally (uvicorn app.main:app --reload) or check your NEXT_PUBLIC_API_URL environment variable on Vercel.",
      },
      { status: 503 }
    );
  }
}

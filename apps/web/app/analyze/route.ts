import { NextRequest, NextResponse } from "next/server";

const apiBase = (process.env.OSSPULSE_API_URL ?? "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

export async function GET(request: NextRequest) {
  const repository = request.nextUrl.searchParams.get("repository") ?? "";
  const target = new URL("/", request.url);

  try {
    const response = await fetch(`${apiBase}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repository_url: repository }),
      cache: "no-store",
    });
    const result = await response.json();
    if (!response.ok) {
      target.searchParams.set("error", result.detail ?? "The repository could not be analyzed.");
      return NextResponse.redirect(target);
    }
    return NextResponse.redirect(new URL(`/report/${result.report_id}`, request.url));
  } catch {
    target.searchParams.set("error", "The analysis service is unavailable. Start the OSS Pulse API and try again.");
    return NextResponse.redirect(target);
  }
}

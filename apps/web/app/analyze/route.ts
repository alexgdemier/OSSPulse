import { NextRequest, NextResponse } from "next/server";

const apiBase = (process.env.OSSPULSE_API_URL ?? "http://127.0.0.1:8002/api/v1").replace(/\/$/, "");

export async function POST(request: NextRequest) {
  const target = new URL("/", request.url);

  let repository: unknown;
  try {
    const body = await request.formData();
    repository = body.get("repository");
  } catch {
    target.searchParams.set("error", "The submitted form could not be read. Please try again.");
    return NextResponse.redirect(target, 303);
  }

  if (typeof repository !== "string" || repository.length > 500) {
    target.searchParams.set("error", "Enter a valid GitHub repository URL.");
    return NextResponse.redirect(target, 303);
  }
  let repositoryUrl: URL;
  try {
    repositoryUrl = new URL(repository);
  } catch {
    target.searchParams.set("error", "Enter a URL in the format https://github.com/owner/repository.");
    return NextResponse.redirect(target, 303);
  }
  const pathParts = repositoryUrl.pathname.split("/").filter(Boolean);
  if (
    repositoryUrl.protocol !== "https:"
    || repositoryUrl.hostname !== "github.com"
    || Boolean(repositoryUrl.port)
    || repositoryUrl.username
    || repositoryUrl.password
    || repositoryUrl.search
    || repositoryUrl.hash
    || pathParts.length !== 2
  ) {
    target.searchParams.set("error", "Enter a URL in the format https://github.com/owner/repository.");
    return NextResponse.redirect(target, 303);
  }

  try {
    const response = await fetch(`${apiBase}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repository_url: repository }),
      cache: "no-store",
    });
    const result = await response.json();
    if (!response.ok) {
      const detail = typeof result.detail === "string" ? result.detail : "The repository could not be analyzed.";
      target.searchParams.set("error", detail);
      return NextResponse.redirect(target, 303);
    }
    if (typeof result.report_id !== "string") throw new Error("The analysis response did not include a report ID.");
    return NextResponse.redirect(new URL(`/report/${encodeURIComponent(result.report_id)}`, request.url), 303);
  } catch {
    target.searchParams.set("error", "The analysis service is unavailable. Start the OSS Pulse API and try again.");
    return NextResponse.redirect(target, 303);
  }
}

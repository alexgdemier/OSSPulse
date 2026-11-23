import { createHmac } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import { getApiBaseUrl } from "../../lib/api-url";

const apiBase = getApiBaseUrl();
const publicWebUrl = process.env.OSSPULSE_PUBLIC_URL;

function redirectUrl(request: NextRequest, path: string) {
  const baseUrl = publicWebUrl ? new URL(publicWebUrl) : new URL(request.url);
  return new URL(path, baseUrl);
}

export async function POST(request: NextRequest) {
  const target = redirectUrl(request, "/");

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
    const headers = new Headers({ "Content-Type": "application/json" });
    const proxySecret = process.env.ANALYSIS_PROXY_SECRET;
    const clientIp = request.headers.get("x-forwarded-for")?.split(",", 1)[0]?.trim();
    if (proxySecret && clientIp) {
      headers.set("X-OSS-Pulse-Client-IP", clientIp);
      headers.set(
        "X-OSS-Pulse-Client-Signature",
        createHmac("sha256", proxySecret).update(clientIp).digest("hex"),
      );
    }
    const response = await fetch(`${apiBase}/analyze`, {
      method: "POST",
      headers,
      body: JSON.stringify({ repository_url: repository }),
      cache: "no-store",
    });
    const result = await response.json();
    if (!response.ok) {
      let detail = typeof result.detail === "string" ? result.detail : "The repository could not be analyzed.";
      const retryAfter = Number(response.headers.get("retry-after"));
      if (response.status === 429 && Number.isFinite(retryAfter) && retryAfter > 0) {
        const minutes = Math.max(1, Math.ceil(retryAfter / 60));
        detail += ` Try again in ${minutes} ${minutes === 1 ? "minute" : "minutes"}.`;
      }
      target.searchParams.set("error", detail);
      return NextResponse.redirect(target, 303);
    }
    if (typeof result.report_id !== "string") throw new Error("The analysis response did not include a report ID.");
    const reportUrl = redirectUrl(request, `/report/${encodeURIComponent(result.report_id)}`);
    if (response.headers.get("X-OSS-Pulse-Cache") === "HIT") {
      reportUrl.searchParams.set("cached", "1");
    }
    return NextResponse.redirect(reportUrl, 303);
  } catch {
    target.searchParams.set("error", "The analysis service is unavailable. Start the OSS Pulse API and try again.");
    return NextResponse.redirect(target, 303);
  }
}

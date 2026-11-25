"use client";

import { useState } from "react";

const reviewFormUrl =
  "https://github.com/alexgdemier/OSSPulse/issues/new?template=maintainer-calibration.yml";

export function ReportShare({
  repository,
  reportId,
  engine,
  analyzedAt,
  score,
  coverage,
  classification,
}: {
  repository: string;
  reportId: string;
  engine: string;
  analyzedAt: string;
  score: number | null;
  coverage: number;
  classification: string;
}) {
  const [status, setStatus] = useState("");

  const shareText = () => {
    const reportUrl = window.location.href;
    return [
      `OSS Pulse report for ${repository}`,
      `Report ID: ${reportId}`,
      `Analyzed: ${new Date(analyzedAt).toISOString()}`,
      `Engine: ${engine}`,
      `Result: ${score === null ? "Score withheld" : score} · ${classification} · ${coverage}% data coverage`,
      `Report: ${reportUrl}`,
      `Optional maintainer review: ${reviewFormUrl}`,
      "Reviews are public and voluntary. Do not include private or security-sensitive information.",
    ].join("\n");
  };

  async function copy(text: string, successMessage: string) {
    try {
      await navigator.clipboard.writeText(text);
      setStatus(successMessage);
    } catch {
      setStatus("Copy is unavailable here. You can copy the report link from your browser address bar.");
    }
  }

  async function shareReport() {
    const reportUrl = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title: `OSS Pulse · ${repository}`, text: "Repository health report", url: reportUrl });
        setStatus("Report shared.");
        return;
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") return;
      }
    }
    await copy(reportUrl, "Report link copied.");
  }

  return (
    <section className="review-share" aria-label="Share this report for review">
      <div>
        <span className="section-label">SHARE THIS REPORT</span>
        <h2>Invite a maintainer to review it</h2>
        <p>Share the same report snapshot so they can check its score, evidence, and missing context.</p>
      </div>
      <div className="review-share-actions">
        <button type="button" className="share-button primary" onClick={shareReport}>Share report</button>
        <button type="button" className="share-button" onClick={() => void copy(shareText(), "Review details copied.")}>Copy review details</button>
        <a href={reviewFormUrl} target="_blank" rel="noreferrer">Open review form ↗</a>
        <span className="share-status" aria-live="polite">{status}</span>
      </div>
    </section>
  );
}

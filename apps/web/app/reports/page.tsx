import Link from "next/link";

const apiBase = (process.env.OSSPULSE_API_URL ?? "http://127.0.0.1:8002/api/v1").replace(/\/$/, "");

type ReportSummary = {
  report_id: string;
  analyzed_at: string;
  health_score: number | null;
  coverage: number;
  classification: string;
  repository: {
    full_name: string;
    url: string;
    description: string | null;
    language: string | null;
  };
  findings: unknown[];
};

export default async function ReportsPage() {
  let reports: ReportSummary[];
  try {
    const response = await fetch(`${apiBase}/reports?limit=50`, { cache: "no-store" });
    if (!response.ok) throw new Error("Report history is unavailable");
    reports = await response.json();
  } catch {
    return (
      <main className="shell report-shell">
        <nav className="nav"><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link></nav>
        <p className="error-banner">Report history is unavailable. Check that the OSS Pulse API and database are running.</p>
      </main>
    );
  }

  return (
    <main className="shell report-shell">
      <nav className="nav">
        <Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link>
        <Link className="back-link" href="/">Analyze a repository →</Link>
      </nav>
      <header className="report-heading">
        <div className="eyebrow"><span className="live-dot" /> SAVED ANALYSES</div>
        <h1>Repository reports</h1>
        <p className="lead">Recent analysis snapshots, stored and ready to revisit.</p>
      </header>
      <section className="reports-list" aria-label="Recent repository reports">
        {reports.length === 0 ? (
          <div className="empty-state">No reports yet. Analyze a public GitHub repository to create the first one.</div>
        ) : reports.map((report) => (
          <Link className="saved-report" href={`/report/${report.report_id}`} key={report.report_id}>
            <div className="saved-report-main">
              <span className="repo-icon">⌘</span>
              <div>
                <h2>{report.repository.full_name}</h2>
                <p>{report.repository.description ?? "No repository description provided."}</p>
                <span className="saved-report-date">{new Date(report.analyzed_at).toLocaleString("en", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC", timeZoneName: "short" })}</span>
              </div>
            </div>
            <div className="saved-report-score">
              <strong>{report.health_score ?? "—"}</strong>
              <span>{report.classification}</span>
              <small>{report.coverage}% coverage · {report.findings.length} findings</small>
            </div>
            <span className="arrow" aria-hidden="true">↗</span>
          </Link>
        ))}
      </section>
      <footer><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><span>Saved reports are snapshots of the data available at analysis time.</span><span>Unknown signals stay unknown</span></footer>
    </main>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";
import { FindingsList } from "../../../components/findings-list";
import { getApiBaseUrl } from "../../../lib/api-url";

const apiBase = getApiBaseUrl();

type Finding = {
  code: string;
  category: string;
  title: string;
  description: string;
  severity: string;
  recommendation: string;
  source_url: string | null;
  evidence: Record<string, unknown>;
};

type Insight = Finding & { priority_score: number };

type Report = {
  report_id: string;
  analyzed_at: string;
  engine_version: string;
  health_score: number | null;
  coverage: number;
  classification: string;
  score_eligibility?: {
    minimum_coverage: number;
    unavailable_dimensions: { dimension: string; sources: string[] }[];
  };
  repository: {
    full_name: string; url: string; description: string | null; language: string | null;
    stars: number; forks: number; topics?: string[]; default_branch?: string; age_days?: number;
    pushed_at?: string | null; updated_at?: string; license?: { name?: string | null; spdx_id?: string | null } | null;
    size_kb?: number | null; features?: { issues?: boolean | null; discussions?: boolean | null; wiki?: boolean | null };
  };
  release_context?: {
    latest_published_release?: { tag: string; published_at: string; url: string; age_days: number } | null;
    published_releases_last_365_days?: number | null;
  };
  dimensions: Record<string, number | null>;
  activity?: {
    commit_activity_last_180_days?: { period_start: string; commits: number }[] | null;
    commits_last_30_days?: number | null;
    commits_last_90_days?: number | null;
    commits_previous_90_days?: number | null;
    commit_activity_change_percent?: number | null;
    active_commit_authors_last_90_days?: number | null;
    open_issues?: number | null;
    open_pull_requests?: number | null;
    stale_pull_requests?: number | null;
    median_open_pull_request_age_days?: number | null;
    stale_pull_request_percent?: number | null;
    open_issues_with_no_comments?: number | null;
    open_issue_no_comment_percent?: number | null;
    top_commit_author_share_last_90_days_percent?: number | null;
    attributed_commits_last_90_days?: number | null;
    repository_associated_response_sample_size?: number;
    repository_associated_responses?: number;
    median_days_to_repository_associated_response?: number | null;
    repository_associated_response_sampled?: number;
    repository_associated_response_evidence_complete?: boolean;
  };
  data_completeness?: Record<string, boolean>;
  findings: Finding[];
  insights: Insight[];
};

const labels: Record<string, string> = {
  maintenance: "Maintenance",
  community: "Community",
  development: "Development",
  documentation: "Documentation",
  sustainability: "Sustainability",
};

const dataSources = [
  { key: "issues", label: "Issues & pull requests", detail: "Open and closed work items" },
  { key: "commits", label: "Commit history", detail: "Activity windows and attributed authors" },
  { key: "releases", label: "Releases", detail: "Published release history" },
  { key: "repository_tree", label: "Default branch files", detail: "Project and documentation signals" },
  { key: "issue_response_sample", label: "Issue response sample", detail: "Capped issue sample; association is only a proxy" },
] as const;

const dataSourceNames: Record<string, string> = {
  issues: "issues and pull requests",
  commits: "commit history",
  releases: "release history",
  repository_tree: "default branch files",
};

export default async function ReportPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ cached?: string }>;
}) {
  const { id } = await params;
  const { cached } = await searchParams;
  let response: Response;
  try {
    response = await fetch(`${apiBase}/reports/${encodeURIComponent(id)}`, { cache: "no-store" });
  } catch {
    return <main className="shell report-shell"><p className="error-banner">The report service is unavailable. Start or check the OSS Pulse API and try again.</p><Link href="/">← Back to OSS Pulse</Link></main>;
  }
  if (response.status === 404) notFound();
  if (!response.ok) return <main className="shell report-shell"><p className="error-banner">The report could not be loaded. Please try again.</p><Link href="/">← Back to OSS Pulse</Link></main>;
  const payload: unknown = await response.json();
  if (!isReport(payload)) {
    return <main className="shell report-shell"><p className="error-banner">This report has an unsupported or incomplete format. Analyze the repository again to create a current report.</p><Link href="/">← Back to OSS Pulse</Link></main>;
  }
  const report = payload;
  const displayScore = report.classification === "Insufficient Data" ? null : report.health_score;

  const analyzed = new Date(report.analyzed_at).toLocaleString("en", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  });
  return (
    <main className="shell report-shell">
      <nav className="nav"><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><div className="nav-links"><Link href="/reports">Reports</Link><Link href="/methodology">Methodology</Link><Link className="back-link" href="/">← Analyze another</Link></div></nav>
      {cached === "1" && <p className="cache-note" role="status">Showing a recent saved analysis. The report timestamp shows when it was generated.</p>}
      <header className="report-heading">
        <div className="eyebrow"><span className="live-dot" /> REPOSITORY HEALTH REPORT</div>
        <h1><a href={report.repository.url} target="_blank" rel="noreferrer">{report.repository.full_name} ↗</a></h1>
        <p className="lead">{report.repository.description ?? "No repository description provided."}</p>
        <div className="repo-meta"><span>{report.repository.language ?? "Language unavailable"}</span><span>{report.repository.stars.toLocaleString()} stars</span><span>{report.repository.forks.toLocaleString()} forks</span></div>
      </header>
      <section className="repository-profile" aria-label="Repository profile">
        <div className="report-section-heading"><div><span className="section-label">REPOSITORY PROFILE</span><h2>Project context</h2></div></div>
        <div className="profile-grid">
          <article><span>License</span><strong>{report.repository.license?.spdx_id ?? report.repository.license?.name ?? "Not detected"}</strong></article>
          <article><span>Project age</span><strong>{typeof report.repository.age_days === "number" ? formatDays(report.repository.age_days) : "—"}</strong></article>
          <article><span>Last pushed</span><strong>{report.repository.pushed_at ? `${formatDays(Math.max(0, Math.floor((new Date(report.analyzed_at).getTime() - new Date(report.repository.pushed_at).getTime()) / 86400000)))} ago` : "No push date"}</strong></article>
          <article><span>Last repository update</span><strong>{report.repository.updated_at ? `${formatDays(Math.max(0, Math.floor((new Date(report.analyzed_at).getTime() - new Date(report.repository.updated_at).getTime()) / 86400000)))} ago` : "—"}</strong></article>
          <article><span>Default branch</span><strong>{report.repository.default_branch ?? "—"}</strong></article>
          <article><span>Repository size</span><strong>{typeof report.repository.size_kb === "number" ? `${report.repository.size_kb.toLocaleString()} KB` : "—"}</strong></article>
          <article><span>GitHub features</span><strong>{report.repository.features ? [report.repository.features.issues && "Issues", report.repository.features.discussions && "Discussions", report.repository.features.wiki && "Wiki"].filter(Boolean).join(" · ") || "None enabled" : "—"}</strong></article>
          <article><span>Latest release</span><strong>{report.release_context?.latest_published_release ? `${report.release_context.latest_published_release.tag} · ${formatDays(report.release_context.latest_published_release.age_days)} ago` : !report.release_context ? "Not available in this report" : report.release_context.published_releases_last_365_days === null ? "History incomplete" : "No published release"}</strong></article>
        </div>
        {report.repository.topics?.length ? <div className="topic-list" aria-label="Repository topics">{report.repository.topics.map((topic) => <span key={topic}>{topic}</span>)}</div> : <p className="method-note">{report.repository.topics ? "No GitHub topics are set for this repository." : "Topics are not available in this saved report."}</p>}
      </section>
      <section className="report-grid">
        <article className="report-card main-score"><span className="section-label">HEALTH SCORE</span><div className="report-score">{displayScore ?? "—"}{displayScore !== null && <small>/100</small>}</div><span className="report-status">{report.classification}</span><div className="score-track"><i style={{ width: `${displayScore ?? 0}%` }} /></div><p>{report.coverage}% data coverage · Engine {report.engine_version}{displayScore === null ? " · Total score withheld because coverage is insufficient" : ""}</p></article>
        <article className="report-card dimension-card"><span className="section-label">HEALTH DIMENSIONS</span>{Object.entries(report.dimensions).map(([name, score]) => <div className="dimension" key={name}><div><span>{labels[name] ?? name}</span><b>{score === null ? "Not evaluated" : score}</b></div><div className="bar"><i className={score !== null && score >= 70 ? "green" : "amber"} style={{ width: `${score ?? 0}%` }} /></div></div>)}</article>
      </section>
      {report.classification === "Insufficient Data" && report.score_eligibility && (
        <p className="score-eligibility-note" role="status">
          A classification requires {report.score_eligibility.minimum_coverage}% coverage. Incomplete dimensions: {report.score_eligibility.unavailable_dimensions.length
            ? report.score_eligibility.unavailable_dimensions.map(({ dimension, sources }) => `${labels[dimension] ?? dimension}${sources.length ? ` (${sources.map((source) => dataSourceNames[source] ?? source).join(", ")} incomplete)` : ""}`).join("; ")
            : "the available evidence does not meet the minimum coverage"}.
        </p>
      )}
      {report.data_completeness && <section className="data-availability" aria-label="Data availability">
        <div className="report-section-heading"><div><span className="section-label">DATA AVAILABILITY</span><h2>Sources used in this report</h2></div></div>
        <div className="data-source-grid">{dataSources.map((source) => {
          const complete = report.data_completeness?.[source.key];
          const status = complete === undefined ? "Unknown" : complete ? "Complete" : "Incomplete";
          return <article className="data-source" key={source.key}><div><strong>{source.label}</strong><span className={`data-status ${complete === undefined ? "unknown" : complete ? "complete" : "incomplete"}`}>{status}</span></div><p>{source.detail}</p></article>;
        })}</div>
      </section>}
      <section className="activity-summary" aria-label="Repository activity summary">
        <div className="report-section-heading"><div><span className="section-label">OBSERVED ACTIVITY</span><h2>Recent repository signals</h2></div></div>
        <div className="activity-cards">
          <article><span>Commits · 30 days</span><strong>{report.activity?.commits_last_30_days ?? "—"}</strong></article>
          <article><span>Commits · latest 90 days</span><strong>{report.activity?.commits_last_90_days ?? "—"}</strong></article>
          <article><span>Active commit authors · 90 days</span><strong>{report.activity?.active_commit_authors_last_90_days ?? "—"}</strong></article>
          <article><span>Open issues / pull requests</span><strong>{report.activity?.open_issues ?? "—"} / {report.activity?.open_pull_requests ?? "—"}</strong></article>
          <article><span>Median age of reviewable open PRs</span><strong>{typeof report.activity?.median_open_pull_request_age_days === "number" ? `${report.activity.median_open_pull_request_age_days} days` : "—"}</strong></article>
          <article><span>Open PRs inactive ≥30 days</span><strong>{report.activity?.stale_pull_requests ?? "—"}{typeof report.activity?.stale_pull_request_percent === "number" ? ` · ${report.activity.stale_pull_request_percent}%` : ""}</strong></article>
          <article><span>Open issues with no comments</span><strong>{report.activity?.open_issues_with_no_comments ?? "—"}{typeof report.activity?.open_issue_no_comment_percent === "number" ? ` · ${report.activity.open_issue_no_comment_percent}%` : ""}</strong></article>
          <article><span>Published releases · last year</span><strong>{report.release_context?.published_releases_last_365_days ?? "—"}</strong></article>
          <article><span>Top attributed commit author share · 90 days</span><strong>{typeof report.activity?.top_commit_author_share_last_90_days_percent === "number" ? `${report.activity.top_commit_author_share_last_90_days_percent}%` : "—"}</strong></article>
        </div>
        <p className="method-note">These figures describe fetched public GitHub data; they are not additional score dimensions. Stale PR percentages use reviewable open PRs and exclude drafts or work labeled as waiting/blocked. Author share uses GitHub-linked commit accounts only and does not identify maintainers. A dash means unavailable, incomplete, or no eligible sample.</p>
        <div className="activity-chart-section">
          <div className="report-section-heading"><div><span className="section-label">COMMIT HISTORY</span><h3>Activity across the last 180 days</h3></div><span className="chart-period">12 periods · 15 days each</span></div>
          {report.activity?.commit_activity_last_180_days ? (
            <CommitActivityChart periods={report.activity.commit_activity_last_180_days} />
          ) : report.activity?.commit_activity_last_180_days === null ? (
            <p className="method-note">The chart is unavailable because GitHub did not return a complete commit history.</p>
          ) : (
            <p className="method-note">This saved report predates commit history charts. Analyze the repository again to view its 180-day activity.</p>
          )}
          {report.activity?.commit_activity_last_180_days && <p className="chart-note">Only complete commit histories are charted. Counts are grouped into 15-day periods.</p>}
        </div>
        {typeof report.activity?.commit_activity_change_percent === "number" && <p className="method-note">Commit volume changed {report.activity.commit_activity_change_percent > 0 ? "+" : ""}{report.activity.commit_activity_change_percent}% compared with the previous 90-day window.</p>}
        {report.activity && typeof report.activity.commits_last_90_days !== "number" && <p className="method-note">Commit totals are unavailable because GitHub pagination was incomplete.</p>}
        {report.data_completeness?.issues === false && <p className="method-note">Issue and pull request totals are unavailable because GitHub pagination was incomplete.</p>}
      </section>
      {typeof report.activity?.repository_associated_response_sample_size === "number" && (
        <section className="response-summary" aria-label="Repository-associated response evidence">
          <div className="report-section-heading">
            <div>
              <span className="section-label">RESPONSE EVIDENCE</span>
              <h2>Repository-associated replies</h2>
            </div>
            <span className={`data-status ${report.activity.repository_associated_response_evidence_complete ? "complete" : "incomplete"}`}>
              {report.activity.repository_associated_response_evidence_complete ? "Complete" : "Sample only"}
            </span>
          </div>
          <div className="response-cards">
            <article>
              <span>Issues with associated replies</span>
              <strong>
                {report.activity.repository_associated_responses} / {report.activity.repository_associated_response_sample_size}
              </strong>
            </article>
            <article>
              <span>Median time to first associated reply</span>
              <strong>
                {typeof report.activity.median_days_to_repository_associated_response === "number"
                  ? `${report.activity.median_days_to_repository_associated_response} days`
                  : report.activity.repository_associated_response_sample_size
                    ? "No associated reply observed"
                    : report.activity.repository_associated_response_sampled
                      ? "Not enough data"
                      : "No open issues"}
              </strong>
            </article>
          </div>
          <p className="method-note">
            Checked {report.activity.repository_associated_response_sampled} selected open issues. “Associated” uses GitHub’s OWNER, MEMBER, or COLLABORATOR label; it does not verify maintainer status. This sample is descriptive and does not affect the health score. No observed reply does not prove an issue was unseen.
          </p>
        </section>
      )}
      <section className="report-findings">
        <div className="report-section-heading"><div><span className="section-label">ACTIONABLE FINDINGS</span><h2>What needs attention</h2></div><span className="count">{report.insights.length}</span></div>
        {report.insights.length === 0 ? <p className="empty-state">No findings were detected in the available data.</p> : <FindingsList insights={report.insights} />}
      </section>
      <footer><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><span>Analyzed {analyzed}</span><span>Coverage first · Unknown signals stay unknown</span></footer>
    </main>
  );
}

function CommitActivityChart({
  periods,
}: {
  periods: { period_start: string; commits: number }[];
}) {
  const maximum = Math.max(1, ...periods.map((period) => period.commits));
  return (
    <svg
      className="commit-chart"
      viewBox="0 0 720 180"
      role="img"
      aria-label="Commit counts for twelve 15-day periods over the last 180 days"
    >
      <line x1="10" y1="132" x2="710" y2="132" className="chart-baseline" />
      {periods.map((period, index) => {
        const height = period.commits === 0 ? 2 : Math.max(5, (period.commits / maximum) * 104);
        const x = 20 + index * 58;
        const date = new Date(period.period_start).toLocaleDateString("en", {
          month: "short",
          day: "numeric",
          timeZone: "UTC",
        });
        return (
          <g key={period.period_start}>
            <title>{date}: {period.commits} commits</title>
            <rect x={x} y={132 - height} width="30" height={height} rx="3" className="chart-bar" />
            {(index === 0 || index === 5 || index === 11) && (
              <text x={x + 15} y="158" textAnchor="middle" className="chart-label">
                {date}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

function isReport(value: unknown): value is Report {
  if (!value || typeof value !== "object") return false;
  const report = value as Partial<Report>;
  return typeof report.report_id === "string"
    && typeof report.analyzed_at === "string"
    && typeof report.engine_version === "string"
    && typeof report.classification === "string"
    && typeof report.coverage === "number"
    && Array.isArray(report.findings)
    && Array.isArray(report.insights)
    && Boolean(report.repository && typeof report.repository.full_name === "string")
    && Boolean(report.dimensions && typeof report.dimensions === "object");
}

function formatDays(days: number): string {
  if (days < 30) return `${days} days`;
  if (days < 365) return `${Math.floor(days / 30)} months`;
  return `${(days / 365).toFixed(1)} years`;
}

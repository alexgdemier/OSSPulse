"use client";

import { useMemo, useState } from "react";

type Insight = {
  code: string;
  category: string;
  title: string;
  description: string;
  severity: string;
  recommendation: string;
  source_url: string | null;
  evidence: Record<string, unknown>;
  priority_score: number;
};

const categoryNames: Record<string, string> = {
  maintenance: "Maintenance",
  community: "Community",
  development: "Development",
  documentation: "Documentation",
  sustainability: "Sustainability",
};

export function FindingsList({ insights }: { insights: Insight[] }) {
  const [severity, setSeverity] = useState("all");
  const [category, setCategory] = useState("all");
  const categories = useMemo(
    () => [...new Set(insights.map((item) => item.category))].sort(),
    [insights],
  );
  const visible = insights.filter(
    (item) => (severity === "all" || item.severity === severity)
      && (category === "all" || item.category === category),
  );

  return (
    <>
      <div className="finding-filters" aria-label="Filter findings">
        <label>Priority
          <select value={severity} onChange={(event) => setSeverity(event.target.value)}>
            <option value="all">All priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
            <option value="informational">Informational</option>
          </select>
        </label>
        <label>Category
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="all">All categories</option>
            {categories.map((item) => <option key={item} value={item}>{categoryNames[item] ?? item}</option>)}
          </select>
        </label>
        <span className="filter-count">Showing {visible.length} of {insights.length}</span>
        {(severity !== "all" || category !== "all") && <button className="clear-filters" onClick={() => { setSeverity("all"); setCategory("all"); }}>Clear filters</button>}
      </div>
      {visible.length === 0 ? <p className="empty-state">No findings match these filters.</p> : visible.map((finding) => (
        <article className="report-finding" key={`${finding.code}-${finding.source_url ?? finding.title}`}>
          <span className={`finding-dot ${finding.severity === "critical" || finding.severity === "high" ? "high" : "medium"}`} />
          <div className="finding-content">
            <div className="finding-title">
              <span className="finding-code">{finding.code}</span>
              <h3>{finding.title}</h3>
              <span className={`severity severity-${finding.severity}`}>{finding.severity}</span>
              <span className="priority-score">Priority {finding.priority_score}</span>
            </div>
            <p>{finding.description}</p>
            <p className="recommendation"><b>Suggested action</b> · {finding.recommendation}</p>
            <details><summary>View evidence</summary><pre>{JSON.stringify(finding.evidence, null, 2)}</pre></details>
          </div>
          {finding.source_url && <a className="arrow" href={finding.source_url} target="_blank" rel="noreferrer" aria-label="Open source on GitHub">↗</a>}
        </article>
      ))}
    </>
  );
}

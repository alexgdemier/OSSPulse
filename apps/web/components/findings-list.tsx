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
  const groups = useMemo(() => {
    const grouped = new Map<string, Insight[]>();
    for (const item of visible) {
      const isRepeatableBacklogFinding = ["IS001", "IS002", "PR001", "PR002"].includes(item.code);
      const key = isRepeatableBacklogFinding
        ? [item.code, item.category, item.severity, item.recommendation].join(":")
        : `${item.code}:${item.source_url ?? item.title}`;
      const items = grouped.get(key);
      if (items) items.push(item);
      else grouped.set(key, [item]);
    }
    return [...grouped.entries()].map(([key, items]) => ({ key, items }));
  }, [visible]);

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
        <span className="filter-count">Showing {visible.length} of {insights.length} findings in {groups.length} groups</span>
        {(severity !== "all" || category !== "all") && <button className="clear-filters" onClick={() => { setSeverity("all"); setCategory("all"); }}>Clear filters</button>}
      </div>
      {groups.length === 0 ? <p className="empty-state">No findings match these filters.</p> : groups.map(({ key, items }) => {
        const finding = items[0];
        const isGrouped = items.length > 1;
        const affectedItemName = finding.code.startsWith("IS") ? "issues" : "pull requests";
        return <article className="report-finding" key={key}>
          <span className={`finding-dot ${finding.severity === "critical" || finding.severity === "high" ? "high" : "medium"}`} />
          <div className="finding-content">
            <div className="finding-title">
              <span className="finding-code">{finding.code}</span>
              <h3>{finding.title}</h3>
              {isGrouped && <span className="finding-group-count">{items.length} items</span>}
              <span className={`severity severity-${finding.severity}`}>{finding.severity}</span>
              <span className="priority-score">Priority {finding.priority_score}</span>
            </div>
            <p>{isGrouped ? `${items.length} ${affectedItemName} meet this signal. Expand the evidence to review each one.` : finding.description}</p>
            <p className="recommendation"><b>Suggested action</b> · {finding.recommendation}</p>
            {isGrouped ? (
              <details className="finding-group-evidence">
                <summary>View all {items.length} affected {affectedItemName}</summary>
                <ul>
                  {items.map((item) => (
                    <li key={`${item.code}-${item.source_url ?? JSON.stringify(item.evidence)}`}>
                      <span>{item.description}</span>
                      {item.source_url && <a href={item.source_url} target="_blank" rel="noreferrer">Open on GitHub ↗</a>}
                    </li>
                  ))}
                </ul>
              </details>
            ) : (
              <details><summary>View evidence</summary><pre>{JSON.stringify(finding.evidence, null, 2)}</pre></details>
            )}
          </div>
          {!isGrouped && finding.source_url && <a className="arrow" href={finding.source_url} target="_blank" rel="noreferrer" aria-label="Open source on GitHub">↗</a>}
        </article>;
      })}
    </>
  );
}

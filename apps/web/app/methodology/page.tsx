import Link from "next/link";

const dimensions = [
  { name: "Maintenance", weight: "30%", indicators: [["PR response time", "30%"], ["Age of open PRs", "25%"], ["Issue response time", "25%"], ["Maintenance activity", "20%"]] },
  { name: "Community", weight: "25%", indicators: [["Active external contributors", "30%"], ["Contribution diversity", "25%"], ["New participants", "25%"], ["Maintainer interaction", "20%"]] },
  { name: "Development", weight: "20%", indicators: [["CI configuration", "25%"], ["Detectable tests", "30%"], ["Development setup", "20%"], ["Workflow quality", "25%"]] },
  { name: "Documentation", weight: "15%", indicators: [["README", "30%"], ["License", "25%"], ["CONTRIBUTING guide", "25%"], ["Additional documentation", "20%"]] },
  { name: "Sustainability", weight: "10%", indicators: [["Contribution concentration", "40%"], ["Activity trend", "35%"], ["Release continuity", "25%"]] },
];

const bands = [["85–100", "Excellent"], ["70–84", "Healthy"], ["50–69", "Needs Attention"], ["30–49", "At Risk"], ["0–29", "Critical"]];

export default function MethodologyPage() {
  return (
    <main className="shell report-shell methodology-shell">
      <nav className="nav">
        <Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link>
        <div className="nav-links"><Link href="/reports">Reports</Link><Link className="back-link" href="/">Analyze a repository →</Link></div>
      </nav>
      <header className="report-heading">
        <div className="eyebrow"><span className="live-dot" /> TRANSPARENT BY DESIGN</div>
        <h1>How OSS Pulse scores a repository</h1>
        <p className="lead">Every score is built from observable signals. We show what data was available, what could not be evaluated, and where the current methodology is still limited.</p>
      </header>

      <section className="method-callout">
        <span className="section-label">THE CORE RULE</span>
        <h2>Unknown is not zero.</h2>
        <p>When GitHub data is incomplete, OSS Pulse excludes affected dimensions from the weighted score and reduces coverage. Scores below 50% coverage are labeled <b>Insufficient Data</b>, and the web app withholds the total score. The API retains the weighted value for diagnostic use.</p>
      </section>

      <section className="method-section">
        <div className="method-section-heading"><span className="section-label">01 · OVERALL SCORE</span><h2>Weighted dimensions</h2></div>
        <div className="formula-card"><code>Health Score = Σ (dimension score × dimension weight) ÷ evaluable weight</code><p>Coverage is the sum of the original weights for evaluable dimensions. The remaining weights are renormalized only for calculating the displayed score.</p></div>
        <div className="dimension-cards">{dimensions.map((dimension) => <article className="method-dimension" key={dimension.name}><div className="method-dimension-heading"><h3>{dimension.name}</h3><strong>{dimension.weight}</strong></div><ul>{dimension.indicators.map(([name, weight]) => <li key={name}><span>{name}</span><b>{weight}</b></li>)}</ul></article>)}</div>
      </section>

      <section className="method-section">
        <div className="method-section-heading"><span className="section-label">02 · CLASSIFICATION</span><h2>Score bands</h2></div>
        <div className="score-bands">{bands.map(([score, label]) => <div key={label}><span>{score}</span><b>{label}</b></div>)}</div>
        <p className="method-note">These bands are provisional and should be interpreted alongside coverage, evidence, and project context. They are not a quality certification or an abandonment verdict.</p>
      </section>

      <section className="method-section">
        <div className="method-section-heading"><span className="section-label">03 · ENGINE v0.2.3-ALPHA</span><h2>Current signals and limits</h2></div>
        <div className="method-limits">
          <article><h3>Maintenance</h3><p>Uses the median age of eligible open pull requests, open issues with no comments, and time since the latest push. A separate sample checks up to five open issues for their first comment by a GitHub OWNER, MEMBER, or COLLABORATOR. This association is only a proxy for project involvement, not proof of maintainer status; the response sample is descriptive and is excluded from scoring. Draft pull requests and pull requests explicitly labeled as blocked or awaiting the author are excluded from stale pull request findings. No comments do not prove that a maintainer has not seen an issue.</p></article>
          <article><h3>Community</h3><p>Not currently scored. Public API data cannot reliably identify every maintainer or distinguish maintainers from external contributors. Reports show attributed active commit authors as a descriptive count instead.</p></article>
          <article><h3>Development and documentation</h3><p>Checks for recognizable files in the default branch tree. Root README, license, contributor guide, and setup signals must be at the repository root; test and documentation directories can be nested in monorepos. Finding a test file does not mean tests pass or that coverage is high. File presence does not measure documentation quality.</p></article>
          <article><h3>Sustainability</h3><p>Compares commits in two complete 90-day windows and uses complete published-release history. If both activity windows contain zero commits, or complete release history contains no published releases, the corresponding signal scores zero. Incomplete history is left unevaluated. A decline finding needs at least four commits in the previous window and a drop of 50% or more. Activity counts, trends, and attributed GitHub author counts are descriptive and are shown only when the relevant data is complete. Release cadence varies by project; no single quiet period proves abandonment.</p></article>
        </div>
        <p className="method-note">GitHub pagination and tree-size limits may reduce data completeness. Each report records completeness by source. Reports also retain the engine version so a future methodology change does not silently rewrite past results.</p>
      </section>

      <footer><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><span>Methodology version 0.2.3-alpha</span><span>Evidence over assumptions</span></footer>
    </main>
  );
}

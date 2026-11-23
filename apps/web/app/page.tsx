export default async function Home({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  return (
    <main className="shell">
      <nav className="nav" aria-label="Main navigation">
        <a className="brand" href="#top"><span className="brand-mark">◉</span> OSS PULSE</a>
        <div className="nav-links"><a href="/reports">Reports</a><a href="/methodology">Methodology</a><a href="https://github.com/alexgdemier/OSSPulse" target="_blank" rel="noreferrer">GitHub ↗</a></div>
      </nav>
      <section className="hero" id="top">
        {error && <p className="error-banner" role="alert">{error}</p>}
        <div className="eyebrow"><span className="live-dot" /> OPEN SOURCE MAINTENANCE INTELLIGENCE</div>
        <h1>Keep your project<br /><span>healthy and thriving.</span></h1>
        <p className="lead">Understand the health of your open source project. Discover what needs attention. Keep your community thriving.</p>
        <form className="search" action="/analyze" method="post">
          <span className="github-mark" aria-hidden="true">⌘</span>
          <input name="repository" type="url" placeholder="https://github.com/owner/repository" aria-label="GitHub repository URL" pattern="https://github\.com/[^/]+/[^/]+/?" maxLength={500} required />
          <button type="submit">Analyze repository <span aria-hidden="true">→</span></button>
        </form>
        <p className="privacy">No account required <span>·</span> Public repositories only</p>
      </section>
      <section className="preview" aria-label="Example repository health report">
        <div className="preview-top"><div><span className="repo-icon">⌘</span><span className="repo-name">acme / open-source-kit</span><span className="pill">PUBLIC</span></div><span className="updated">SAMPLE REPORT · NOT LIVE DATA</span></div>
        <div className="preview-body">
          <div className="score-card"><div className="section-label">HEALTH SCORE <span className="info">ⓘ</span></div><div className="score"><strong>74</strong><span>/ 100</span></div><div className="health"><span className="health-dot" /> Healthy <span className="coverage">· 75% coverage</span></div><div className="score-track"><i style={{ width: "74%" }} /></div><p>Transparent signals. Actionable context.</p></div>
          <div className="dimensions"><div className="section-label">HEALTH DIMENSIONS</div>{[["Maintenance", "78", "78%", "green"], ["Community", "Not evaluated", "0%", "amber"], ["Development", "67", "67%", "amber"], ["Documentation", "80", "80%", "green"], ["Sustainability", "Not evaluated", "0%", "amber"]].map(([name, score, width, tone]) => <div className="dimension" key={name}><div><span>{name}</span><b>{score}</b></div><div className="bar"><i className={tone} style={{ width }} /></div></div>)}</div>
          <div className="attention"><div className="attention-heading"><span className="section-label">NEEDS ATTENTION</span><span className="count">2</span></div><article className="finding"><span className="finding-dot high" /><div><b>Pull request needs a review</b><p>#142 · No activity for 38 days</p></div><span className="arrow">↗</span></article><article className="finding"><span className="finding-dot medium" /><div><b>Contributor guide missing</b><p>New contributors may need a clearer path</p></div><span className="arrow">↗</span></article></div>
        </div>
        <div className="preview-foot"><span>ⓘ Scores reflect observable signals, not popularity.</span><span>Methodology v0.2.2-alpha <span className="sep">·</span> All times UTC</span></div>
      </section>
      <section className="value" id="method"><div><span className="section-label">BUILT FOR MAINTAINERS</span><h2>Clarity for the work<br />behind the code.</h2></div><div className="value-items"><article><span>01</span><div><h3>See the full picture</h3><p>Maintenance, development, documentation, and sustainability signals in one place. Community remains unscored until it can be measured reliably.</p></div></article><article><span>02</span><div><h3>Understand every score</h3><p>Transparent methodology, visible evidence, and data coverage. Unknown signals stay unknown.</p></div></article><article><span>03</span><div><h3>Know what to do next</h3><p>Specific findings paired with practical recommendations you can act on.</p></div></article></div></section>
      <footer><a className="brand" href="#top"><span className="brand-mark">◉</span> OSS PULSE</a><span>Open source maintenance intelligence.</span><span>Independent project · Not affiliated with GitHub</span></footer>
    </main>
  );
}

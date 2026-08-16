export function ArtifactCards() {
  const cards = [
    "Question Answer Card",
    "Textbook Pain Point Card",
    "Research Source Card",
    "RL and KPI Scorecard"
  ];

  return (
    <section className="artifact-grid">
      {cards.map((title) => (
        <article className="artifact-card" key={title}>
          <h3>{title}</h3>
          <p>Evidence, confidence, and feedback are visible by design.</p>
        </article>
      ))}
    </section>
  );
}

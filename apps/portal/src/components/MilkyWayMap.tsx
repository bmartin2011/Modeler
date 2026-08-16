type Projection = {
  lens: string;
  sectors: { id: string; name: string; rings: string[] }[];
  overlays: { type: string; label: string; confidence: number }[];
  collapsible_branches: { entity_id: string; state: string; summary: string }[];
};

export function MilkyWayMap({ projection }: { projection: Projection }) {
  return (
    <section className="milky-way" aria-label={`${projection.lens} Milky Way map`}>
      <header>
        <h2>{projection.lens === "value_stream" ? "Value Stream Lens" : "Organization Lens"}</h2>
      </header>
      <div className="sector-grid">
        {projection.sectors.map((sector) => (
          <article className="sector" key={sector.id}>
            <h3>{sector.name}</h3>
            <p>{sector.rings.join(" / ")}</p>
          </article>
        ))}
      </div>
      {projection.overlays.map((overlay) => (
        <aside className="overlay" key={overlay.label}>
          <strong>{overlay.label}</strong>
          <span>{Math.round(overlay.confidence * 100)}% confidence</span>
        </aside>
      ))}
    </section>
  );
}

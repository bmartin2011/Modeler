import { useMemo, useState } from "react";

type ContextOption = { selected: string; available: string[] };
type ModelContext = { industry?: ContextOption; journey?: ContextOption };
type GraphEntity = { id: string; name: string; archimate_type: string };
type ProcessNode = GraphEntity & { type: string; verification_state: string; review_state: string; evidence_ids: string[]; confidence: number };
type ProcessContext = {
  performed_by: GraphEntity[];
  applications: GraphEntity[];
  data: { reads: GraphEntity[]; creates: GraphEntity[]; updates: GraphEntity[]; deletes: GraphEntity[] };
  capabilities: GraphEntity[];
  value_streams: GraphEntity[];
  gates: GraphEntity[];
  pain_points: GraphEntity[];
  evidence_ids: string[];
  confidence: { score: number; rationale: string };
};
type Projection = {
  lens: string;
  context?: ModelContext;
  archimate_legend?: { type: string; description: string }[];
  lanes?: { id: string; name: string; archimate_type: string; node_ids: string[] }[];
  nodes?: ProcessNode[];
  edges?: { id: string; type: string; source_id: string; target_id: string }[];
  process_contexts?: Record<string, ProcessContext>;
  overlays?: { type: string; label: string; confidence: number }[];
  unresolved?: { entity_id: string; question: string }[];
  collapsible_branches?: { entity_id: string; state: string; summary: string }[];
  sectors?: { id: string; name: string; rings: string[] }[];
};

function EntityList({ entities, emptyLabel = "Not modeled" }: { entities: GraphEntity[]; emptyLabel?: string }) {
  return entities.length ? <ul className="relationship-list">{entities.map((entity) => <li key={entity.id}><span>{entity.name}</span><small>{entity.archimate_type}</small></li>)}</ul> : <p className="empty-relationship">{emptyLabel}</p>;
}

export function MilkyWayMap({ projection, showContext = true }: { projection: Projection; showContext?: boolean }) {
  const nodes = projection.nodes ?? [];
  const lanes = projection.lanes ?? [];
  const processContexts = projection.process_contexts ?? {};
  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const processNodes = nodes.filter((node) => node.type === "process" && processContexts[node.id]);
  const [selectedProcessId, setSelectedProcessId] = useState<string>();
  const selectedProcess = processNodes.find((node) => node.id === selectedProcessId) ?? processNodes[0];
  const selectedContext = selectedProcess ? processContexts[selectedProcess.id] : undefined;
  const dataEntities = selectedContext ? [...selectedContext.data.reads, ...selectedContext.data.creates, ...selectedContext.data.updates, ...selectedContext.data.deletes] : [];
  const supportEntities = selectedContext ? [...selectedContext.capabilities, ...selectedContext.value_streams] : [];

  return <section className="milky-way" aria-label={`${projection.lens} Milky Way map`}>
    <header className="galaxy-header">
      <div>
        <h2>{projection.lens === "value_stream" ? "Value Stream Lens" : "Organization Lens"}</h2>
        {showContext && projection.context?.industry && projection.context?.journey ? <div className="context-pills"><p className="context-pill">{projection.context.industry.selected}</p><p className="context-pill">{projection.context.journey.selected}</p></div> : null}
      </div>
      <div className="archimate-legend" aria-label="ArchiMate type legend">
        {(projection.archimate_legend ?? []).map((item) => <span className="archimate-badge" key={item.type} title={item.description}>{item.type}</span>)}
      </div>
    </header>

    <div className="galaxy-layout">
      <div className="galaxy-lanes">
        {lanes.map((lane) => <section className="galaxy-lane" key={lane.id}>
          <header><h3>{lane.name}</h3><span className="archimate-badge">{lane.archimate_type}</span></header>
          {lane.node_ids.map((nodeId) => {
            const node = nodeById.get(nodeId);
            return node ? <button className="process-node" type="button" key={node.id} aria-pressed={selectedProcess?.id === node.id} onClick={() => setSelectedProcessId(node.id)}><strong>{node.name}</strong><span>{node.archimate_type}</span><small>{node.review_state} / {node.verification_state} / {Math.round(node.confidence * 100)}%</small></button> : null;
          })}
        </section>)}
        {!lanes.length && (projection.sectors ?? []).map((sector) => <section className="galaxy-lane" key={sector.id}><h3>{sector.name}</h3><p>{sector.rings.join(" / ")}</p></section>)}
      </div>

      {selectedProcess && selectedContext ? <aside className="relationship-inspector" aria-label={`${selectedProcess.name} relationships`}>
        <header><h3>{selectedProcess.name}</h3></header>
        <section><h4>Who does this process?</h4><EntityList entities={selectedContext.performed_by} /></section>
        <section><h4>What application supports it?</h4><EntityList entities={selectedContext.applications} /></section>
        <section><h4>What data is used, created, or modified?</h4><EntityList entities={dataEntities} /></section>
        <section><h4>What capability or value stream does it support?</h4><EntityList entities={supportEntities} /></section>
        {selectedContext.gates.length || selectedContext.pain_points.length ? <section><h4>Gates and pain points</h4><EntityList entities={[...selectedContext.gates, ...selectedContext.pain_points]} /></section> : null}
        <section><h4>Evidence and confidence</h4><p>{Math.round(selectedContext.confidence.score * 100)}% confidence</p><p>{selectedContext.confidence.rationale}</p><p className="evidence-list">Evidence: {selectedContext.evidence_ids.join(", ") || "Not modeled"}</p></section>
      </aside> : null}
    </div>

    {(projection.unresolved ?? []).length ? <section className="unresolved-list" aria-label="Unresolved model items"><h3>Unresolved model items</h3><ul>{projection.unresolved?.map((item) => <li key={`${item.entity_id}-${item.question}`}>{item.question}</li>)}</ul></section> : null}
    {(projection.overlays ?? []).map((overlay) => <aside className="overlay" key={overlay.label}><strong>{overlay.label}</strong><span>{Math.round(overlay.confidence * 100)}% confidence</span></aside>)}
  </section>;
}

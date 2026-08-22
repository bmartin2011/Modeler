import { useMemo, useState } from "react";

type ContextOption = { selected: string; available: string[] };
type ModelContext = { industry?: ContextOption; journey?: ContextOption };
type GraphEntity = { id: string; name: string; archimate_type: string };
type GraphNode = GraphEntity & { type: string; verification_state: string; review_state: string; evidence_ids: string[]; confidence?: number | null };
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
  unresolved?: { entity_id: string; relationship_id: string; relationship: string; question: string }[];
};
type Projection = {
  lens: string;
  context?: ModelContext;
  archimate_legend?: { type: string; description: string }[];
  lanes?: { id: string; name: string; archimate_type: string; node_ids: string[] }[];
  nodes?: GraphNode[];
  edges?: { id: string; relationship: string; source_id: string; target_id: string }[];
  process_contexts?: Record<string, ProcessContext>;
  overlays?: { type: string; label: string; confidence: number }[];
  unresolved?: { entity_id: string; question: string }[];
  collapsible_branches?: { entity_id: string; state: string; summary: string }[];
  sectors?: { id: string; name: string; rings: string[] }[];
};

function EntityList({ entities, emptyLabel = "Not modeled" }: { entities: GraphEntity[]; emptyLabel?: string }) {
  return entities.length ? <ul className="relationship-list">{entities.map((entity) => <li key={entity.id}><span>{entity.name}</span><small>{entity.archimate_type}</small></li>)}</ul> : <p className="empty-relationship">{emptyLabel}</p>;
}

function DataOperation({ label, entities }: { label: string; entities: GraphEntity[] }) {
  return <div className="data-operation"><h5>{label}</h5><EntityList entities={entities} emptyLabel="None" /></div>;
}

function confidenceLabel(confidence?: number | null) {
  return confidence == null ? "Confidence unavailable" : `${Math.round(confidence * 100)}%`;
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
  const supportEntities = selectedContext ? [...selectedContext.capabilities, ...selectedContext.value_streams] : [];
  const graphNodes = !lanes.length && nodes.length ? nodes : [];

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
            return node ? <button className="process-node" type="button" key={node.id} aria-pressed={selectedProcess?.id === node.id} onClick={() => setSelectedProcessId(node.id)}><strong>{node.name}</strong><span>{node.archimate_type}</span><small>{node.review_state} / {node.verification_state} / {confidenceLabel(node.confidence)}</small></button> : null;
          })}
        </section>)}
        {graphNodes.length ? <section className="organization-graph" aria-label="Organization graph">
          <div className="organization-nodes">{graphNodes.map((node) => <article className="organization-node" key={node.id}><strong>{node.name}</strong><span>{node.archimate_type}</span><small>{node.review_state} / {node.verification_state} / {confidenceLabel(node.confidence)}</small></article>)}</div>
          <ul className="organization-edges">{(projection.edges ?? []).map((edge) => {
            const source = nodeById.get(edge.source_id);
            const target = nodeById.get(edge.target_id);
            return source && target ? <li key={edge.id}>{source.name} {edge.relationship.replace(/_/g, " ")} {target.name}</li> : null;
          })}</ul>
          {(projection.collapsible_branches ?? []).length ? <ul className="collapsible-branches">{projection.collapsible_branches?.map((branch) => <li key={branch.entity_id}>{branch.summary}</li>)}</ul> : null}
        </section> : null}
        {!lanes.length && (projection.sectors ?? []).map((sector) => <section className="galaxy-lane" key={sector.id}><h3>{sector.name}</h3><p>{sector.rings.join(" / ")}</p></section>)}
      </div>

      {selectedProcess && selectedContext ? <aside className="relationship-inspector" aria-label={`${selectedProcess.name} relationships`}>
        <header><h3>{selectedProcess.name}</h3></header>
        <section><h4>Who does this process?</h4><EntityList entities={selectedContext.performed_by} /></section>
        <section><h4>What application supports it?</h4><EntityList entities={selectedContext.applications} /></section>
        <section><h4>What data is used, created, or modified?</h4><div className="data-operations"><DataOperation label="Reads" entities={selectedContext.data.reads} /><DataOperation label="Creates" entities={selectedContext.data.creates} /><DataOperation label="Updates" entities={selectedContext.data.updates} /><DataOperation label="Deletes" entities={selectedContext.data.deletes} /></div></section>
        <section><h4>What capability or value stream does it support?</h4><EntityList entities={supportEntities} /></section>
        {selectedContext.gates.length || selectedContext.pain_points.length ? <section><h4>Gates and pain points</h4><EntityList entities={[...selectedContext.gates, ...selectedContext.pain_points]} /></section> : null}
        {selectedContext.unresolved?.length ? <section><h4>What remains unresolved for this process?</h4><ul className="relationship-list">{selectedContext.unresolved.map((item) => <li key={item.relationship_id}>{item.question}</li>)}</ul></section> : null}
        <section><h4>Evidence and confidence</h4><p>{Math.round(selectedContext.confidence.score * 100)}% confidence</p><p>{selectedContext.confidence.rationale}</p><p className="evidence-list">Evidence: {selectedContext.evidence_ids.join(", ") || "Not modeled"}</p></section>
      </aside> : null}
    </div>

    {(projection.unresolved ?? []).length ? <section className="unresolved-list" aria-label="Unresolved model items"><h3>Unresolved model items</h3><ul>{projection.unresolved?.map((item) => <li key={`${item.entity_id}-${item.question}`}>{item.question}</li>)}</ul></section> : null}
    {(projection.overlays ?? []).map((overlay) => <aside className="overlay" key={overlay.label}><strong>{overlay.label}</strong><span>{Math.round(overlay.confidence * 100)}% confidence</span></aside>)}
  </section>;
}

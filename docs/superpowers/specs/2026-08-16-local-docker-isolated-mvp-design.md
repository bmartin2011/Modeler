# Local Docker Isolated MVP Design

Date: 2026-08-16
Status: Draft for review

## Purpose

Define how Modeler runs as a completely local, Docker-hosted MVP without colliding with other projects on the same machine. This spec refreshes the implementation direction after the first MVP slice exposed an important product constraint: Modeler must be a self-contained local application stack, not a set of loose services that assume common host ports or shared Docker resources.

This spec inherits the product vision from the repository README and the earlier ArchiMate visual portal design:

- Modeler is a visual documentation portal for business architecture.
- It should feel like an architecture intern with a good notebook: standards-aware, organization-learning, evidence-recording, and feedback-driven.
- It turns conversations, documents, research, and feedback into ArchiMate-aligned knowledge.
- The flagship visual artifact is a dual-lens Milky Way map for value streams and organization structure.
- Answers should include evidence, confidence, standards alignment, open questions, and learning hooks.
- Reinforcement learning starts conservatively as a measured feedback loop over mappings, viewpoints, corrections, branch collapse decisions, and documentation quality.
- Internal documentation is learning material; external documents are quality-controlled inputs or outputs unless a human approves promotion.
- MCP should become a first-class local agent interface over the same knowledge, views, documentation, and feedback loop.

## Problem Statement

The MVP must be easy to start, inspect, and trust locally. The first Compose attempt revealed a real local operating condition: another Docker project already owns host port `8000`. Modeler should expect this. Developers and users may have other local stacks running for smart home systems, databases, search, vector stores, or unrelated experiments.

The product must therefore isolate:

- Docker networks.
- Container names.
- Volumes.
- Host ports.
- Service discovery.
- Local model configuration.
- Future agent/MCP access.

Isolation is not only convenience. It protects the trust model. Modeler will eventually process sensitive people, process, policy, architecture, and value-stream data. Its local runtime should make resource ownership obvious and prevent accidental coupling to unrelated local systems.

## Design Principles

- Docker is the default host for the MVP. Opening `apps/portal/index.html` directly is not a supported product path.
- Internal traffic stays internal. Services communicate over a dedicated Docker network by service name.
- Host exposure is explicit and minimal. Only human-facing or agent-facing endpoints are published to the host.
- Host ports are namespaced away from common defaults to reduce collisions with other Docker projects.
- Local model use is explicit. LLM-backed interpretation should use Docker Desktop-provided local models or another local OpenAI-compatible endpoint by default.
- Cloud use remains opt-in. Any cloud model, hosted search, managed vector store, or external database must disclose cost, data boundary, retention policy, and reason before use.
- MCP is a product interface, not an afterthought. The MVP API should keep boundaries compatible with a future local MCP server.
- Evidence before claims applies to runtime too. The README should tell users how to verify that Docker is hosting the portal, API, and supporting services.

## Runtime Topology

The local MVP should run as one Compose application with a dedicated project identity.

Recommended Compose identity:

```text
Compose project: modeler-mvp
Network:         modeler_internal
Volumes:         modeler_postgres_data, modeler_chroma_data, modeler_fuseki_data
```

Services:

```text
portal          Browser UI for Milky Way views, Q&A, artifacts, and feedback
api             FastAPI orchestration boundary for graph questions and projections
mcp             Future local agent tool server over selected API/knowledge capabilities
fuseki          RDF/OWL/SHACL store for standards, organization facts, and provenance
chroma          Vector memory for conversations, research, docs, examples, and snippets
postgres        Durable app state, review queues, jobs, KPI snapshots, and audit records
redis           Cache, queue, scheduling, and short-lived coordination
searxng         Local metasearch facade for open research and standards discovery
worker          Future ingestion, extraction, evaluation, and documentation jobs
local-model     Optional adapter target for Docker Desktop local models or equivalent
```

For the MVP, `mcp`, `worker`, and `local-model` may be represented as documented interfaces or disabled Compose profiles until their first concrete implementation. The important design choice is that API boundaries and environment variables anticipate them.

## Network Model

All Modeler services should join a private Docker network:

```yaml
networks:
  modeler_internal:
    name: modeler_internal
```

Service-to-service traffic should use Docker DNS names:

```text
portal -> api:8000
api -> fuseki:3030
api -> chroma:8000
api -> postgres:5432
api -> redis:6379
api -> searxng:8080
api -> local model endpoint, when configured
mcp -> api:8000 or shared application modules, depending on implementation
worker -> api/database/graph/vector/search services as needed
```

The API should not call `localhost` for internal dependencies when running inside Docker. `localhost` inside a container means that container, not the host or another service.

## Host Port Policy

Modeler should avoid common host ports used by other local projects. Publish a predictable namespaced range:

```text
Portal UI   18173 -> portal:5173
API         18100 -> api:8000
MCP future  18190 -> mcp:<chosen-port>
Chroma      18101 -> chroma:8000, only if host inspection is useful
SearXNG     18180 -> searxng:8080, only if humans inspect search directly
Fuseki      18130 -> fuseki:3030, only if humans inspect RDF directly
Postgres    18432 -> postgres:5432, only if host DB tools need access
Redis       18379 -> redis:6379, only if host inspection is useful
```

Default MVP exposure should be:

- Publish `portal` for humans.
- Publish `api` for curl, browser debugging, and future local agent access.
- Keep stores internal unless active development requires host inspection.

Optional debug exposure can be controlled by Compose profiles or an override file. The base stack should be conservative.

## Configuration Model

The runtime should use environment variables for all cross-service endpoints:

```text
PORTAL_API_BASE_URL=/api or http://api:8000 inside Docker
API_PUBLIC_BASE_URL=http://localhost:18100
MODEL_BASE_URL=<Docker Desktop local model endpoint or other local OpenAI-compatible endpoint>
MODEL_NAME=<local model name>
CHROMA_URL=http://chroma:8000
FUSEKI_URL=http://fuseki:3030
SEARXNG_URL=http://searxng:8080
POSTGRES_URL=postgresql://modeler:modeler@postgres:5432/modeler
REDIS_URL=redis://redis:6379/0
CLOUD_ADAPTERS_ENABLED=false
```

Cloud adapters should remain disabled by default. Enabling them should require explicit configuration and visible documentation of what data may leave the local environment.

## Portal Hosting Rule

The product path is:

```bash
docker compose up --build
```

The user should open:

```text
http://localhost:18173
```

The file path below is a source artifact, not the product:

```text
apps/portal/index.html
```

If opened directly through `file://`, it may appear blank because the React/Vite module graph expects to be served by Vite or a built static server. The README should make the Docker URL obvious to avoid that trap.

## MCP Direction

The future MCP server should expose local tools for agents without bypassing the same evidence and trust rules used by the portal.

Initial tool candidates:

- `ask_modeler_question`: answer organization-grounded questions with evidence and confidence.
- `get_archimate_entities`: retrieve typed entities and relationships from the graph.
- `get_milky_way_view`: retrieve a value-stream or organization projection.
- `propose_archimate_mapping`: turn conversational text into candidate ArchiMate entities, relationships, and viewpoints.
- `critique_documentation`: grade documentation claims for coverage, freshness, ambiguity, traceability, and usefulness.
- `record_feedback`: capture thumbs-up, thumbs-down, correction, deviation, or approval events.

MCP outputs must include:

- Evidence.
- Confidence.
- Trust boundary.
- Learning eligibility.
- Missing information.
- Suggested next question when uncertainty remains.

The MCP server should run locally by default and communicate over `modeler_internal`. If exposed to the host, it should use the namespaced host port policy.

## Documentation And Learning Implications

Documentation of the codebase should be part of the learning pipeline. The Docker topology itself should become mined knowledge:

```text
Component: Portal
Predicate: is hosted by
Object: Docker Compose service portal
Evidence: docker-compose.yml and README verification section
Confidence: high after docker compose verification
Learning eligibility: internal, learn by default
```

The critique layer should reject or flag documentation that implies unsupported startup paths. For example, if a README suggests opening `apps/portal/index.html` directly, the documentation quality loop should mark that as misleading for a Vite-based app unless a static build path is also documented.

## MVP Acceptance Criteria

The refreshed MVP is acceptable when:

- `docker compose up --build` starts the Modeler stack without colliding with unrelated Docker projects.
- `docker compose ps` shows the portal and API running in the Modeler project.
- The portal is reachable at the documented Modeler host port.
- The portal renders meaningful app content, not a blank file view.
- The portal can request a Milky Way projection from the API through the Docker-hosted route.
- The API is reachable at the documented namespaced host port.
- The API answers "Who reports to John?" using seeded evidence.
- Store services are attached to the Modeler private network and do not rely on other projects' containers.
- The README identifies Docker as the default product host.
- Local model configuration is documented as local-first and cloud-disabled by default.
- The future MCP surface is documented enough that implementation can wrap the API without redefining trust rules.

## Risks And Open Questions

- Docker Desktop local model endpoints may vary by installation. The MVP should make the endpoint configurable instead of hardcoding a single provider shape.
- Publishing every store to the host is convenient during development but increases collision risk. The default should be minimal exposure with optional debug profiles.
- Some Docker images are large. The first `docker compose up --build` may require time and network access to pull images.
- The MVP currently has a deterministic/rules-based interpreter. That is acceptable while local LLM integration is shaped, but docs should not imply true conversational ArchiMate extraction is complete.
- MCP should not duplicate business logic. The first implementation should either wrap API endpoints or share application services.

## Recommended Next Step

Write an implementation plan focused on the runtime packaging slice:

1. Introduce an isolated Compose project/network/volume model.
2. Move host ports to the Modeler namespaced range.
3. Configure portal-to-API routing for Docker-hosted use.
4. Add local model environment settings with cloud adapters disabled.
5. Update README startup and verification instructions.
6. Verify Docker-hosted portal/API behavior in the browser.
7. Preserve the existing ArchiMate/Milky Way/learning-loop vision from the README as the product baseline.

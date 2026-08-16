# ArchiMate Visual Documentation Portal Design

Date: 2026-08-16
Status: Draft approved for planning

## Purpose

Build a browser-based visual documentation portal for business architecture and process knowledge. The system should help users navigate organization structure, value streams, processes, systems, gates, and pain points through ArchiMate-aligned views and viewpoints. It should behave like an architecture intern: standards-aware from day one, but continuously learning the organization through conversations, documents, feedback, and observed navigation outcomes.

The MVP should prove the core idea with fake, modeled organization data before connecting to real organizational documents or conversations.

## Design Principles

- Standards-driven, organization-influenced. ArchiMate, BPMN, UML, SysML, TOGAF-style repositories, and industry standards define the formal backbone. Organization-specific people, process, systems, policy, and pain points influence local interpretation.
- Evidence over assertion. Every insight, model mapping, recommendation, and playbook entry should track evidence, confidence, source, and review history.
- Human agency remains central. The playbook recommends actions and modeling decisions, but humans can override or deviate at any time. Deviations are learning events, not errors.
- Knowledge capture at every opportunity. Questions, answers, corrections, rejected mappings, accepted views, and navigation paths become evaluation and improvement signals.
- Generic MVP, industry extensible. The first pass should be small and flat, with industry selected as a future configuration overlay rather than hardcoded into the product.
- Modular by default. The portal, API, research discovery, semantic graph, vector memory, workers, and documentation renderer should be separately replaceable services.

## MVP Scope

The MVP uses a fake generic organization, such as Acme Services, to demonstrate end-to-end behavior.

The modeled data should include:

- A small, flat organization structure: one executive, three to five functional leads, and eight to twelve roles.
- Two to three value streams.
- Eight to fifteen business capabilities.
- Five to ten processes.
- A handful of systems, gates, handoffs, documents, and known or suspected pain points.
- Deliberate uncertainty, such as unknown reporting lines, unclear process ownership, duplicated handoffs, missing approval rules, and partially known systems.

The MVP should answer questions such as:

- Who reports to John?
- Which processes depend on this system?
- Where are approval gates concentrated?
- Which value stream stage has the most unresolved ownership?
- What textbook pain points are likely here?
- What evidence supports this recommendation?

When answers resolve uncertainty, the affected branches in the visual navigation should become verified and collapsible.

## Core Architecture

The system has eight first-class layers.

### 1. Standards Knowledge Base

The standards knowledge base stores canonical concepts, relationships, viewpoint rules, validation constraints, and modeling guidance.

Initial standards and reference families:

- ArchiMate for enterprise architecture concepts, relationships, layers, aspects, views, and viewpoints.
- BPMN for process flow, events, activities, gateways, lanes, and procedural alignment.
- UML and SysML for software, system, and engineering-aligned details.
- TOGAF-style architecture repository patterns for organizing reusable standards, viewpoints, templates, and reference models.
- NIST CSF Profiles, BIAN, and similar future overlays for industry-specific structures.

The standards layer should remain separate from organization-specific knowledge so the system can explain the difference between formal modeling rules and local organizational reality.

### 2. Organization Learning Model

The organization learning model stores people, roles, departments, value streams, capabilities, processes, systems, policies, gates, documents, risks, pain points, ownership, and evidence.

It should support partial knowledge. Unknown facts are allowed and visible. The system should ask targeted questions when a missing fact blocks a useful view, diagnosis, or recommendation.

Example:

The system may know that John owns a process gate but not whether Sarah reports to John. When the user answers, the graph records the reporting relationship, the evidence source, confidence, timestamp, and whether a human verified it.

### 3. Interpretation Layer

The interpretation layer maps conversational text and future documents into candidate architecture structures.

It should extract:

- Candidate ArchiMate elements and relationships.
- Candidate BPMN process structures.
- People, roles, teams, ownership, and decision rights.
- Goals, outcomes, value streams, capabilities, policies, gates, systems, and handoffs.
- Likely pain points and missing facts.
- Candidate viewpoints that fit the user's question or intent.

Early behavior should prefer selection and composition from known model elements over unconstrained generation. Generated suggestions must identify assumptions and uncertainty.

### 4. Evaluation, Reinforcement Learning, and KPI Layer

Reinforcement learning is a first-class design element, but early learning should be evidence-driven and conservative. The system should first collect high-quality supervised and interaction feedback before attempting heavier optimization.

For each design area, define:

- What to measure.
- Why the measurement matters.
- How the measurement is collected.
- How results will improve future behavior.

Initial KPIs:

- Mapping accuracy: percentage of accepted conversational-to-architecture mappings.
- Relationship validity: percentage of extracted relationships that pass standards and organization rules.
- Viewpoint fit: user acceptance rate for selected or generated views.
- Correction rate: how often users edit or reject extracted facts.
- Time to answer: time and interaction count needed to answer architecture questions.
- Confidence calibration: whether high-confidence answers are more likely to be accepted.
- Branch resolution rate: rate at which unknown graph branches become verified and collapsible.
- Source usefulness: which research, standards, or internal evidence sources lead to accepted decisions.
- Recommendation usefulness: whether playbook recommendations are accepted, modified, rejected, or later judged effective.

Learning signals:

- Explicit thumbs up/down or accept/reject feedback.
- Human corrections to mappings and relationships.
- Follow-up questions caused by ambiguity.
- View traversal paths and abandoned paths.
- Accepted collapses of graph branches.
- Reopened or challenged collapsed branches.
- Deviations from playbook recommendations.
- Outcome reviews against expected KPIs.

### 5. Research Intelligence Layer

The research layer keeps the knowledge base connected to open research and standards sources.

SearXNG should be included from day one as the preferred search service. It should support scheduled and manual searches for topics such as:

- ArchiMate ontology and enterprise architecture modeling.
- Natural language to BPMN or process models.
- Knowledge graph question answering.
- Reinforcement learning from feedback.
- Ontology validation with SHACL or related rule systems.
- Process mining and process improvement.
- Industry reference models and regulatory frameworks.

Search results should not automatically become trusted rules. They enter a reviewable source library with:

- Source URL.
- Title and authors, where available.
- Source type, such as standard, research paper, blog, ontology asset, or internal document.
- Topic tags.
- Summary.
- Freshness date.
- Applicability notes.
- Review status.
- Linked playbook decisions or architecture rules.

Trusted sources can inform ontology rules, playbook recommendations, examples, benchmarks, and future industry packs.

### 6. Playbook and Decision Ledger

The playbook recommends modeling, research, interpretation, navigation, and improvement strategies. It should be measured and revised like any other system component.

Each playbook entry should record:

- Decision or recommendation.
- Context where it applies.
- Rationale.
- Evidence and sources.
- Expected outcome.
- KPIs.
- Review cadence.
- Outcome evidence.
- Current status: proposed, active, revised, retired, or promoted.

Humans may deviate from the playbook. Deviations should be captured with rationale and later reviewed to improve future recommendations.

### 7. Visual Portal and Documentation Layer

The visual portal is the primary consumption experience. Sphinx-style documentation provides structured, navigable reference pages, while browser-native graph views provide exploration and sensemaking.

The flagship MVP view is a dual-lens Milky Way map inspired by Eero Hosiaisluoma's Milky Way Map and enterprise design examples.

The same underlying graph should render through two lenses:

- Value Stream Lens: sectors are stages such as Discover, Sell, Onboard, Deliver, Support, and Improve.
- Organization Lens: sectors are functions such as Strategy, Operations, Sales, Delivery, Finance, and IT.

The other lens appears as an overlay:

- In Value Stream Lens, departments and role ownership appear as colored overlays.
- In Organization Lens, value streams appear as flow lines crossing departments.

Milky Way rings should represent progressively detailed architecture concerns:

- Purpose and outcomes.
- Value streams.
- Capabilities.
- Processes.
- People and roles.
- Systems and data.
- Gates, controls, evidence, risks, and pain points.

Visual behavior:

- Expand uncertain branches.
- Collapse verified branches.
- Show confidence, evidence, and source provenance.
- Highlight load-bearing processes and systems.
- Show likely textbook pain points.
- Drill from high-level ArchiMate viewpoints into BPMN, UML, or SysML detail where appropriate.
- Let users ask questions directly from the view.

### 8. Documentation Intelligence and Quality Layer

Documentation quality is part of the learning system. The product should document its codebase and architecture artifacts, verify and critique those documents, grade their quality, and present evidence before asking users to trust the result.

This layer should mine knowledge from:

- Source code, tests, configuration, and service definitions.
- Product documentation and design specs.
- Conversations, decisions, corrections, and playbook entries.
- Research sources and standards references.
- Generated Sphinx pages and visual viewpoint definitions.

Extracted knowledge should be represented as auditable entity facts and triples.

Example triples:

- Visual Portal -> renders -> Milky Way Viewpoint.
- API -> projects -> RDF graph data.
- Playbook Decision -> measured by -> KPI.
- Documentation Claim -> supported by -> source evidence.
- Component -> documented in -> Sphinx page.

Each documentation claim should carry:

- Entity or artifact.
- Predicate or relationship.
- Evidence source.
- Confidence score.
- Validation status.
- Freshness timestamp.
- Review history.
- User feedback state.

Documentation critique should grade:

- Coverage: whether important components, services, decisions, and viewpoints are documented.
- Traceability: whether claims link to code, specs, conversations, standards, or research.
- Freshness: whether docs match the current implementation and current decisions.
- Ambiguity: whether vague or overloaded terms are flagged.
- Standards alignment: whether architecture language matches ArchiMate, BPMN, UML/SysML, and local modeling rules.
- Evidence strength: whether generated claims expose confidence, provenance, and validation status.
- Usefulness: whether users judge the documentation helpful for the conversation or task.

Human thumbs up/down, corrections, and requests for better evidence should become learning signals. Automated documentation updates should be blocked or flagged when they reduce clarity, coverage, traceability, evidence quality, or usefulness relative to the existing documentation baseline.

## Technical Stack

The primary delivery unit is a local Docker Compose prototype.

Services:

- Portal UI: browser-based visual navigation and documentation experience.
- API: application orchestration, graph queries, search facade, and AI interaction boundary.
- RDF store: Apache Jena Fuseki or Eclipse RDF4J for standards semantics, organization facts, provenance, and validation rules.
- ChromaDB: vector memory over conversations, documents, research snippets, decisions, and examples.
- Postgres: optional durable application store for users, projects, source metadata, review queues, job history, KPI snapshots, and other relational state that does not belong in the semantic graph.
- Redis: optional cache and lightweight coordination layer for queues, scheduled work, rate limits, temporary sessions, and expensive graph/query result caching.
- SearXNG: metasearch for research and standards discovery.
- Worker: ingestion, scheduled searches, extraction, evaluation, playbook updates, and graph projections.
- Sphinx/docs renderer: static or semi-static documentation generation from modeled knowledge.

Recommended data responsibilities:

- RDF/OWL/SHACL stores formal semantics, valid relationships, constraints, provenance, and explainable facts.
- Chroma stores fuzzy semantic retrieval and memory over unstructured or semi-structured text.
- Postgres stores conventional application records and audit-friendly workflow state when relational modeling is clearer than graph modeling.
- Redis speeds up repeated reads and coordinates background work when the MVP needs it; it should not be the source of truth.
- The API projects graph data into frontend-ready JSON for visual traversal.
- Sphinx renders curated documentation pages and indexed references.
- SearXNG discovers external sources but does not grant trust by itself.

Neo4j or another property graph can be added later if traversal analytics or UI performance require it. It is not required for the MVP. Postgres and Redis are lower-risk additions because they support normal application operations without competing with RDF as the standards and reasoning backbone.

## Data Flow

1. User asks a question, opens a view, or provides text.
2. API sends the request to the interpretation layer.
3. Interpretation layer retrieves relevant semantic facts from RDF and similar examples from Chroma.
4. Candidate mappings, answers, or views are validated against standards and organization rules.
5. The portal displays the answer, view, confidence, evidence, and unresolved questions.
6. User accepts, rejects, corrects, or asks follow-up questions.
7. Feedback is recorded in the decision ledger and evaluation layer.
8. Verified facts update the organization graph.
9. Graph projections and Sphinx documentation refresh as needed.

## Error Handling and Trust

The system should avoid false certainty.

Required answer states:

- Known and verified.
- Known but inferred.
- Ambiguous.
- Unknown.
- Conflicting evidence.
- Unsupported by current model.

When the system recommends a fix or identifies a pain point, it should include:

- Claim.
- Evidence.
- Confidence.
- Relevant standard, pattern, or playbook entry.
- Missing information.
- Suggested next question or next data source.

## Future Industry Packs

Industry packs should be optional overlays. They may add reference models, regulatory standards, recommended structures, validation rules, examples, and benchmarks.

Potential future packs:

- Banking and financial services, using BIAN and relevant regulatory/control frameworks.
- Manufacturing, using NIST manufacturing cybersecurity profiles and process/reference architecture patterns.
- Healthcare, using healthcare-specific regulatory, privacy, and process standards.
- Government operations, using public-sector architecture and compliance patterns.
- SaaS or digital services, using service management, security, and product operating-model references.

Industry packs should never override verified organization knowledge automatically. They should suggest likely structures, gaps, controls, and questions.

## MVP Success Criteria

The MVP is successful when it can:

- Start locally with Docker Compose.
- Load fake generic organization data.
- Render a dual-lens Milky Way map.
- Switch between Value Stream Lens and Organization Lens.
- Answer basic graph questions such as "who reports to John?"
- Collapse branches after facts are verified.
- Show confidence and evidence for answers.
- Identify simple textbook pain points from modeled patterns.
- Store playbook recommendations and deviations.
- Run SearXNG-backed research searches and save source candidates.
- Store semantic snippets in Chroma and standards/org facts in RDF.
- Generate or refresh Sphinx-style documentation from the modeled graph.

## Open Questions for Planning

- Choose Apache Jena Fuseki or Eclipse RDF4J as the first RDF store.
- Choose the frontend graph rendering library.
- Decide whether the first AI interpreter is mocked, rules-based, LLM-backed, or hybrid.
- Define the smallest fake organization dataset that demonstrates the intended behavior.
- Decide how Sphinx pages are generated from graph data.
- Decide the first playbook categories.

## Initial Recommendation

Build the knowledge core first, with a thin but real visual portal. The first implementation should prove that the system can store standards-aligned facts, model a small organization, render the same graph through value-stream and organization lenses, answer simple questions, record feedback, and prepare for data-driven improvement.

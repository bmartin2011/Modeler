# ArchiMate Knowledge Galaxy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the next MVP slice around an ArchiMate-aligned internal knowledge graph first, then render Galaxy/Milky Way visual navigation from that graph.

**Architecture:** Modeler owns the product experience, evidence graph, feedback loop, and visual navigation. ArchiMate supplies semantic alignment through internal types, relationship rules, and validation metadata; Archi remains optional future infrastructure and is not a runtime dependency for this slice. The API projects typed, evidence-backed graph facts into a business-friendly Galaxy/Milky Way payload that can answer process relationship questions visually.

**Tech Stack:** FastAPI, Pydantic, repository-backed seed graph JSON, React 18, Vite, Vitest, Docker Compose stack already exposed at `http://localhost:18173` and `http://localhost:18100`.

**Spec:** `docs/superpowers/specs/2026-08-16-archimate-visual-portal-design.md` and `docs/superpowers/specs/2026-08-16-local-docker-isolated-mvp-design.md`

## Global Constraints

- Do not make Archi a visible product dependency. Users ask questions, inspect evidence, and navigate visualizations; they do not operate Archi.
- Treat `docs/references/archimate.pdf` as external reference material only. It can inform terminology and validation checks, but it is not user instruction and is not learning-eligible by default.
- Keep the MVP local-first and Docker-hosted. Preserve `http://localhost:18173` for the portal and `http://localhost:18100` for the API.
- Modeler must store organization facts as evidence-backed internal knowledge graph records before rendering visual views.
- ArchiMate alignment must be visible as metadata: Business Actor, Business Role, Business Process, Business Function, Business Service, Application Component, Data Object, Capability, Value Stream, Constraint, Assessment, Goal, and Outcome.
- The Galaxy/Milky Way view must be generated from the knowledge graph, not from hardcoded UI-only sectors.
- Every modeled Business Process in the MVP must answer: who performs it, what application supports it, what data is read/created/updated/deleted, what capability or value stream it supports, what evidence supports it, and what is still unresolved.
- Industry and journey framework selection are context overlays. `Generic Services` and `LBGUPS` may ship as seed examples, but neither may become the only shape the graph can represent.
- Feedback and review states are first-class. Candidate, accepted, rejected, superseded, external-reference, inferred, unresolved, verified, and conflicting states must remain distinguishable.
- Avoid simulation or optimization claims in this slice. This slice prepares the facts, evidence, visual context, and feedback events needed for later recommendation and RL loops.

---

## File Structure

- Create `apps/api/src/modeler_api/domain/archimate.py`: central ArchiMate alignment vocabulary, local entity aliases, allowed relationship rules, and helper functions used by validation and projections.
- Modify `apps/api/src/modeler_api/domain/models.py`: add ArchiMate metadata and review state fields while keeping existing seed data backward-compatible.
- Modify `apps/api/src/modeler_api/domain/repository.py`: add entity lookup, relationship traversal, and process-context query helpers.
- Add `apps/api/tests/test_archimate_semantics.py`: verify supported ArchiMate types, alias mapping, and relationship validation.
- Modify `data/seed/acme.json`: expand the fake organization into a small evidence-backed graph with people, roles, processes, capabilities, applications, data objects, value streams, gates, assessments, industry context, and LBGUPS as one journey overlay.
- Modify `apps/api/tests/test_milky_way.py`: assert that the API projection is graph-derived, ArchiMate-aligned, and process-question complete.
- Modify `apps/api/src/modeler_api/views/milky_way.py`: replace hardcoded sectors with a graph projection that produces Galaxy/Milky Way lanes, nodes, edges, overlays, unresolved facts, evidence, and confidence.
- Modify `apps/portal/src/components/MilkyWayMap.tsx`: render graph-derived lanes, nodes, edges, ArchiMate type badges, evidence/confidence, and a selected process inspector.
- Modify `apps/portal/src/App.tsx`: add industry and journey context controls while preserving lens switching.
- Modify `apps/portal/src/styles.css`: provide a dense, legible business architecture layout.
- Modify `apps/portal/tests/app.test.tsx` and `apps/portal/tests/milky-way.test.tsx`: verify visible ArchiMate concepts, graph-derived process answers, context controls, and unresolved/evidence states.
- Modify `README.md`: document the corrected foundation and the role of ArchiMate alignment versus optional Archi integration.

---

### Task 1: Add ArchiMate Semantic Vocabulary

**Files:**
- Create: `apps/api/src/modeler_api/domain/archimate.py`
- Modify: `apps/api/src/modeler_api/domain/models.py`
- Test: `apps/api/tests/test_archimate_semantics.py`

**Interfaces:**
- Produces: `normalize_archimate_type(entity_type: str, explicit_type: str | None = None) -> str`
- Produces: `is_supported_archimate_type(archimate_type: str) -> bool`
- Produces: `relationship_rule_for(source_type: str, relationship_type: str, target_type: str) -> RelationshipRule | None`
- Produces: `Entity.archimate_type: str | None`
- Produces: `Entity.review_state: ReviewState`
- Produces: `Relationship.archimate_relationship: str | None`
- Produces: `Relationship.review_state: ReviewState`

- [ ] **Step 1: Write failing semantic vocabulary tests**

Create `apps/api/tests/test_archimate_semantics.py`:

```python
from modeler_api.domain.archimate import (
    SUPPORTED_ARCHIMATE_TYPES,
    is_supported_archimate_type,
    normalize_archimate_type,
    relationship_rule_for,
)
from modeler_api.domain.models import Confidence, Entity, Relationship


def test_supported_archimate_types_include_mvp_language():
    assert {
        "Business Actor",
        "Business Role",
        "Business Process",
        "Business Function",
        "Business Service",
        "Application Component",
        "Data Object",
        "Capability",
        "Value Stream",
        "Constraint",
        "Assessment",
        "Goal",
        "Outcome",
    }.issubset(SUPPORTED_ARCHIMATE_TYPES)


def test_local_entity_types_normalize_to_archimate_types():
    assert normalize_archimate_type("person") == "Business Actor"
    assert normalize_archimate_type("role") == "Business Role"
    assert normalize_archimate_type("process") == "Business Process"
    assert normalize_archimate_type("system") == "Application Component"
    assert normalize_archimate_type("data_object") == "Data Object"
    assert normalize_archimate_type("pain_point") == "Assessment"
    assert normalize_archimate_type("gate") == "Constraint"


def test_explicit_archimate_type_must_be_supported():
    assert normalize_archimate_type("custom", "Value Stream") == "Value Stream"
    assert not is_supported_archimate_type("Spreadsheet Tab")


def test_process_relationship_rules_cover_core_questions():
    assert relationship_rule_for("Business Role", "performs", "Business Process") is not None
    assert relationship_rule_for("Business Actor", "performs", "Business Process") is not None
    assert relationship_rule_for("Business Process", "uses", "Application Component") is not None
    assert relationship_rule_for("Business Process", "reads", "Data Object") is not None
    assert relationship_rule_for("Business Process", "creates", "Data Object") is not None
    assert relationship_rule_for("Business Process", "updates", "Data Object") is not None
    assert relationship_rule_for("Business Process", "deletes", "Data Object") is not None
    assert relationship_rule_for("Business Process", "realizes", "Capability") is not None


def test_models_accept_archimate_and_review_metadata():
    entity = Entity(
        id="process.qualify_opportunity",
        type="process",
        archimate_type="Business Process",
        name="Qualify Opportunity",
        verification_state="inferred",
        review_state="candidate",
        evidence_ids=["evidence.seed_org"],
    )
    relationship = Relationship(
        id="rel.sales_performs_qualify",
        type="performs",
        archimate_relationship="assignment",
        source_id="role.sales_lead",
        target_id="process.qualify_opportunity",
        verification_state="inferred",
        review_state="candidate",
        confidence=Confidence(score=0.71, rationale="Seed model states sales owns qualification."),
        evidence_ids=["evidence.seed_org"],
    )

    assert entity.archimate_type == "Business Process"
    assert entity.review_state == "candidate"
    assert relationship.archimate_relationship == "assignment"
    assert relationship.review_state == "candidate"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd apps/api
$env:PATH='C:\Users\bmart\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
python -m pytest tests/test_archimate_semantics.py -q
```

Expected: fails because `archimate.py`, `archimate_type`, `archimate_relationship`, and `review_state` do not exist.

- [ ] **Step 3: Create ArchiMate vocabulary module**

Create `apps/api/src/modeler_api/domain/archimate.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


SUPPORTED_ARCHIMATE_TYPES = {
    "Business Actor",
    "Business Role",
    "Business Process",
    "Business Function",
    "Business Service",
    "Application Component",
    "Data Object",
    "Capability",
    "Value Stream",
    "Constraint",
    "Assessment",
    "Goal",
    "Outcome",
}


LOCAL_TYPE_ALIASES = {
    "organization": "Business Actor",
    "person": "Business Actor",
    "role": "Business Role",
    "process": "Business Process",
    "business_function": "Business Function",
    "business_service": "Business Service",
    "system": "Application Component",
    "application": "Application Component",
    "data_object": "Data Object",
    "capability": "Capability",
    "value_stream": "Value Stream",
    "journey": "Value Stream",
    "journey_stage": "Value Stream",
    "gate": "Constraint",
    "constraint": "Constraint",
    "pain_point": "Assessment",
    "assessment": "Assessment",
    "goal": "Goal",
    "outcome": "Outcome",
    "industry": "Outcome",
}


@dataclass(frozen=True)
class RelationshipRule:
    source_type: str
    relationship_type: str
    target_type: str
    archimate_relationship: str
    rationale: str


RELATIONSHIP_RULES = (
    RelationshipRule("Business Actor", "reports_to", "Business Actor", "association", "Organization reporting is a local organization relationship."),
    RelationshipRule("Business Actor", "assigned_to", "Business Role", "assignment", "Actors can be assigned to roles."),
    RelationshipRule("Business Role", "performs", "Business Process", "assignment", "Roles perform business behavior."),
    RelationshipRule("Business Actor", "performs", "Business Process", "assignment", "Actors may directly perform business behavior in a small organization model."),
    RelationshipRule("Business Process", "uses", "Application Component", "serving", "Applications serve or support business behavior."),
    RelationshipRule("Business Process", "reads", "Data Object", "access", "Processes access data objects."),
    RelationshipRule("Business Process", "creates", "Data Object", "access", "Processes create data objects."),
    RelationshipRule("Business Process", "updates", "Data Object", "access", "Processes update data objects."),
    RelationshipRule("Business Process", "deletes", "Data Object", "access", "Processes delete data objects."),
    RelationshipRule("Business Process", "realizes", "Capability", "realization", "Processes can realize business capabilities for the MVP view."),
    RelationshipRule("Business Process", "supports", "Value Stream", "realization", "Processes support value stream or journey stages."),
    RelationshipRule("Capability", "enables", "Value Stream", "realization", "Capabilities enable value stream outcomes."),
    RelationshipRule("Business Process", "requires_gate", "Constraint", "association", "Gates constrain process progression."),
    RelationshipRule("Constraint", "indicates", "Assessment", "association", "Constraints can indicate a pain point assessment."),
    RelationshipRule("Assessment", "affects", "Business Process", "association", "Pain points affect process behavior."),
    RelationshipRule("Assessment", "affects", "Capability", "association", "Pain points affect capability health."),
)


def is_supported_archimate_type(archimate_type: str) -> bool:
    return archimate_type in SUPPORTED_ARCHIMATE_TYPES


def normalize_archimate_type(entity_type: str, explicit_type: str | None = None) -> str:
    if explicit_type is not None:
        if not is_supported_archimate_type(explicit_type):
            raise ValueError(f"unsupported ArchiMate type: {explicit_type}")
        return explicit_type

    try:
        return LOCAL_TYPE_ALIASES[entity_type]
    except KeyError as exc:
        raise ValueError(f"cannot normalize entity type to ArchiMate: {entity_type}") from exc


def relationship_rule_for(source_type: str, relationship_type: str, target_type: str) -> RelationshipRule | None:
    for rule in RELATIONSHIP_RULES:
        if (
            rule.source_type == source_type
            and rule.relationship_type == relationship_type
            and rule.target_type == target_type
        ):
            return rule
    return None
```

- [ ] **Step 4: Add model metadata fields**

In `apps/api/src/modeler_api/domain/models.py`, add:

```python
ReviewState = Literal["candidate", "accepted", "rejected", "superseded", "external_reference"]
```

Update `Entity`:

```python
class Entity(BaseModel):
    id: str
    type: str
    archimate_type: str | None = None
    name: str
    verification_state: VerificationState
    review_state: ReviewState = "accepted"
    evidence_ids: list[str] = Field(default_factory=list)
```

Update `Relationship`:

```python
class Relationship(BaseModel):
    id: str
    type: str
    archimate_relationship: str | None = None
    source_id: str
    target_id: str
    verification_state: VerificationState
    review_state: ReviewState = "accepted"
    confidence: Confidence
    evidence_ids: list[str] = Field(min_length=1)
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
python -m pytest tests/test_archimate_semantics.py -q
```

Expected: all tests in `test_archimate_semantics.py` pass.

- [ ] **Step 6: Run API regression tests**

Run:

```powershell
python -m pytest -q
```

Expected: all existing API tests still pass because new model fields have defaults.

- [ ] **Step 7: Commit**

```powershell
git add apps/api/src/modeler_api/domain/archimate.py apps/api/src/modeler_api/domain/models.py apps/api/tests/test_archimate_semantics.py
git commit -m "feat: add archimate semantic vocabulary"
```

---

### Task 2: Add Graph Traversal And Process Context Queries

**Files:**
- Modify: `apps/api/src/modeler_api/domain/repository.py`
- Test: `apps/api/tests/test_archimate_semantics.py`

**Interfaces:**
- Consumes: `KnowledgeRepository.graph`
- Produces: `KnowledgeRepository.get_entity(entity_id: str) -> Entity`
- Produces: `KnowledgeRepository.related_from(source_id: str, relationship_type: str | None = None) -> list[tuple[Relationship, Entity]]`
- Produces: `KnowledgeRepository.related_to(target_id: str, relationship_type: str | None = None) -> list[tuple[Relationship, Entity]]`
- Produces: `KnowledgeRepository.process_context(process_id: str) -> dict[str, list[tuple[Relationship, Entity]]]`

- [ ] **Step 1: Add failing traversal tests**

Append to `apps/api/tests/test_archimate_semantics.py`:

```python
from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph


def _repo() -> KnowledgeRepository:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return KnowledgeRepository(graph)


def test_repository_traverses_outgoing_relationships():
    repo = _repo()

    outgoing = repo.related_from("gate.ops_review", "indicates")

    assert [(rel.type, entity.id) for rel, entity in outgoing] == [
        ("indicates", "pain.approval_concentration")
    ]


def test_repository_traverses_incoming_relationships():
    repo = _repo()

    incoming = repo.related_to("person.john", "reports_to")

    assert {entity.id for _rel, entity in incoming} == {"person.maya", "person.luis"}
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
cd apps/api
$env:PATH='C:\Users\bmart\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
python -m pytest tests/test_archimate_semantics.py -q
```

Expected: fails because traversal methods do not exist.

- [ ] **Step 3: Implement traversal methods**

Update `apps/api/src/modeler_api/domain/repository.py`:

```python
from modeler_api.domain.models import Entity, KnowledgeGraph, Relationship


class KnowledgeRepository:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    def get_entity(self, entity_id: str) -> Entity:
        return self.graph.get_entity(entity_id)

    def find_entities_by_type(self, entity_type: str) -> list[Entity]:
        return [entity for entity in self.graph.entities if entity.type == entity_type]

    def find_relationships(
        self,
        type: str | None = None,
        target_id: str | None = None,
        source_id: str | None = None,
    ) -> list[Relationship]:
        relationships = self.graph.relationships
        if type is not None:
            relationships = [rel for rel in relationships if rel.type == type]
        if target_id is not None:
            relationships = [rel for rel in relationships if rel.target_id == target_id]
        if source_id is not None:
            relationships = [rel for rel in relationships if rel.source_id == source_id]
        return relationships

    def related_from(
        self, source_id: str, relationship_type: str | None = None
    ) -> list[tuple[Relationship, Entity]]:
        return [
            (relationship, self.get_entity(relationship.target_id))
            for relationship in self.find_relationships(type=relationship_type, source_id=source_id)
        ]

    def related_to(
        self, target_id: str, relationship_type: str | None = None
    ) -> list[tuple[Relationship, Entity]]:
        return [
            (relationship, self.get_entity(relationship.source_id))
            for relationship in self.find_relationships(type=relationship_type, target_id=target_id)
        ]

    def process_context(self, process_id: str) -> dict[str, list[tuple[Relationship, Entity]]]:
        return {
            "performers": self.related_to(process_id, "performs"),
            "applications": self.related_from(process_id, "uses"),
            "reads": self.related_from(process_id, "reads"),
            "creates": self.related_from(process_id, "creates"),
            "updates": self.related_from(process_id, "updates"),
            "deletes": self.related_from(process_id, "deletes"),
            "capabilities": self.related_from(process_id, "realizes"),
            "value_streams": self.related_from(process_id, "supports"),
            "gates": self.related_from(process_id, "requires_gate"),
            "pain_points": self.related_to(process_id, "affects"),
        }
```

- [ ] **Step 4: Run focused tests**

Run:

```powershell
python -m pytest tests/test_archimate_semantics.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add apps/api/src/modeler_api/domain/repository.py apps/api/tests/test_archimate_semantics.py
git commit -m "feat: add graph traversal helpers"
```

---

### Task 3: Expand Seed Into An Evidence-Backed ArchiMate-Aligned Graph

**Files:**
- Modify: `data/seed/acme.json`
- Test: `apps/api/tests/test_milky_way.py`
- Test: `apps/api/tests/test_archimate_semantics.py`

**Interfaces:**
- Consumes: model metadata from Task 1.
- Produces seeded graph facts for industry context, LBGUPS journey overlay, people, roles, processes, capabilities, applications, data objects, gates, assessments, value streams, and process relationships.
- Required process IDs: `process.attract_prospect`, `process.qualify_opportunity`, `process.onboard_customer`, `process.deliver_service`, `process.invoice_customer`, `process.resolve_customer_issue`.

- [ ] **Step 1: Add failing seed completeness tests**

Append to `apps/api/tests/test_archimate_semantics.py`:

```python
def test_seed_contains_archimate_metadata_for_core_entities():
    repo = _repo()

    required = {
        "person.john": "Business Actor",
        "role.sales_lead": "Business Role",
        "process.qualify_opportunity": "Business Process",
        "app.crm": "Application Component",
        "data.qualified_opportunity": "Data Object",
        "cap.opportunity_management": "Capability",
        "vs.customer_lifecycle": "Value Stream",
        "gate.ops_review": "Constraint",
        "pain.manual_handoff": "Assessment",
    }

    for entity_id, archimate_type in required.items():
        assert repo.get_entity(entity_id).archimate_type == archimate_type


def test_each_seed_process_has_core_relationship_context():
    repo = _repo()
    process_ids = [
        "process.attract_prospect",
        "process.qualify_opportunity",
        "process.onboard_customer",
        "process.deliver_service",
        "process.invoice_customer",
        "process.resolve_customer_issue",
    ]

    for process_id in process_ids:
        context = repo.process_context(process_id)
        assert context["performers"], process_id
        assert context["applications"], process_id
        assert (
            context["reads"]
            or context["creates"]
            or context["updates"]
            or context["deletes"]
        ), process_id
        assert context["capabilities"], process_id
        assert context["value_streams"], process_id
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
cd apps/api
$env:PATH='C:\Users\bmart\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
python -m pytest tests/test_archimate_semantics.py -q
```

Expected: fails because the seed graph is still too thin.

- [ ] **Step 3: Expand seed evidence**

In `data/seed/acme.json`, keep existing evidence and add:

```json
{
  "id": "evidence.seed_process_web",
  "label": "Seed process relationship web",
  "source_type": "seed",
  "source_ref": "data/seed/acme.json",
  "learning_eligibility": "learn_by_default"
}
```

Add external reference evidence for the local PDF without making it learning-eligible:

```json
{
  "id": "evidence.archimate_reference_pdf",
  "label": "ArchiMate reference PDF",
  "source_type": "external",
  "source_ref": "docs/references/archimate.pdf",
  "learning_eligibility": "do_not_learn"
}
```

- [ ] **Step 4: Expand seed entities**

Add or rename entities so the graph includes:

```json
{"id": "industry.generic_services", "type": "industry", "archimate_type": "Outcome", "name": "Generic Services", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "journey.lbgups", "type": "journey", "archimate_type": "Value Stream", "name": "LBGUPS Customer Lifecycle", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "stage.learn", "type": "journey_stage", "archimate_type": "Value Stream", "name": "Learn", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "stage.buy", "type": "journey_stage", "archimate_type": "Value Stream", "name": "Buy", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "stage.get", "type": "journey_stage", "archimate_type": "Value Stream", "name": "Get", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "stage.use", "type": "journey_stage", "archimate_type": "Value Stream", "name": "Use", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "stage.pay", "type": "journey_stage", "archimate_type": "Value Stream", "name": "Pay", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "stage.support", "type": "journey_stage", "archimate_type": "Value Stream", "name": "Support", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "role.sales_lead", "type": "role", "archimate_type": "Business Role", "name": "Sales Lead", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "role.operations_lead", "type": "role", "archimate_type": "Business Role", "name": "Operations Lead", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "role.delivery_lead", "type": "role", "archimate_type": "Business Role", "name": "Delivery Lead", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "role.finance_lead", "type": "role", "archimate_type": "Business Role", "name": "Finance Lead", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "role.support_lead", "type": "role", "archimate_type": "Business Role", "name": "Support Lead", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "process.attract_prospect", "type": "process", "archimate_type": "Business Process", "name": "Attract Prospect", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "process.qualify_opportunity", "type": "process", "archimate_type": "Business Process", "name": "Qualify Opportunity", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "process.onboard_customer", "type": "process", "archimate_type": "Business Process", "name": "Onboard Customer", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_org", "evidence.seed_process_web"]},
{"id": "process.deliver_service", "type": "process", "archimate_type": "Business Process", "name": "Deliver Service", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_org", "evidence.seed_process_web"]},
{"id": "process.invoice_customer", "type": "process", "archimate_type": "Business Process", "name": "Invoice Customer", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "process.resolve_customer_issue", "type": "process", "archimate_type": "Business Process", "name": "Resolve Customer Issue", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "app.crm", "type": "application", "archimate_type": "Application Component", "name": "CRM", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_org"]},
{"id": "app.customer_portal", "type": "application", "archimate_type": "Application Component", "name": "Customer Portal", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_org"]},
{"id": "app.delivery_workspace", "type": "application", "archimate_type": "Application Component", "name": "Delivery Workspace", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "app.billing", "type": "application", "archimate_type": "Application Component", "name": "Billing System", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "app.support_desk", "type": "application", "archimate_type": "Application Component", "name": "Support Desk", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "data.lead_profile", "type": "data_object", "archimate_type": "Data Object", "name": "Lead Profile", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "data.qualified_opportunity", "type": "data_object", "archimate_type": "Data Object", "name": "Qualified Opportunity", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "data.customer_account", "type": "data_object", "archimate_type": "Data Object", "name": "Customer Account", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "data.service_request", "type": "data_object", "archimate_type": "Data Object", "name": "Service Request", "verification_state": "verified", "review_state": "accepted", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "data.invoice", "type": "data_object", "archimate_type": "Data Object", "name": "Invoice", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "data.support_ticket", "type": "data_object", "archimate_type": "Data Object", "name": "Support Ticket", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "cap.opportunity_management", "type": "capability", "archimate_type": "Capability", "name": "Opportunity Management", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "cap.billing_management", "type": "capability", "archimate_type": "Capability", "name": "Billing Management", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "cap.customer_support", "type": "capability", "archimate_type": "Capability", "name": "Customer Support", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]},
{"id": "pain.manual_handoff", "type": "pain_point", "archimate_type": "Assessment", "name": "Manual Sales-to-Delivery Handoff", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"]}
```

Keep existing `person.*`, `cap.customer_intake`, `cap.service_delivery`, `gate.ops_review`, and `pain.approval_concentration`; add `archimate_type` and `review_state` to them.

- [ ] **Step 5: Expand seed relationships**

Add relationship records that cover:

```text
person -> assigned_to -> role
role/person -> performs -> process
process -> uses -> application
process -> reads/creates/updates/deletes -> data_object
process -> realizes -> capability
process -> supports -> journey_stage
journey_stage -> supports -> journey
process -> requires_gate -> gate
gate -> indicates -> pain_point
pain_point -> affects -> process
capability -> enables -> journey_stage
```

For each new relationship, include:

```json
"archimate_relationship": "assignment",
"verification_state": "inferred",
"review_state": "candidate",
"confidence": {"score": 0.72, "rationale": "Seed process web provides the modeled relationship."},
"evidence_ids": ["evidence.seed_process_web"]
```

Use the matching `archimate_relationship` from `relationship_rule_for` when a rule exists.

- [ ] **Step 6: Run seed tests**

Run:

```powershell
python -m pytest tests/test_archimate_semantics.py -q
```

Expected: seed completeness tests pass.

- [ ] **Step 7: Run API regression tests**

Run:

```powershell
python -m pytest -q
```

Expected: all API tests pass.

- [ ] **Step 8: Commit**

```powershell
git add data/seed/acme.json apps/api/tests/test_archimate_semantics.py
git commit -m "feat: seed archimate knowledge graph"
```

---

### Task 4: Project The Graph Into Galaxy/Milky Way Views

**Files:**
- Modify: `apps/api/src/modeler_api/views/milky_way.py`
- Modify: `apps/api/tests/test_milky_way.py`

**Interfaces:**
- Consumes: `KnowledgeRepository.process_context(process_id)`
- Produces API payload:

```python
{
    "lens": "value_stream",
    "context": {
        "industry": {"selected": "Generic Services", "available": ["Generic Services"]},
        "journey": {"selected": "LBGUPS Customer Lifecycle", "available": ["LBGUPS Customer Lifecycle"]},
    },
    "archimate_legend": [{"type": "Business Process", "description": "A behavior element that groups business behavior."}],
    "lanes": [{"id": "stage.learn", "name": "Learn", "archimate_type": "Value Stream", "node_ids": ["process.attract_prospect"]}],
    "nodes": [{"id": "process.attract_prospect", "name": "Attract Prospect", "archimate_type": "Business Process", "verification_state": "inferred", "review_state": "candidate", "evidence_ids": ["evidence.seed_process_web"], "confidence": 0.72}],
    "edges": [{"source_id": "role.sales_lead", "target_id": "process.attract_prospect", "relationship": "performs", "archimate_relationship": "assignment", "confidence": 0.72}],
    "process_contexts": {"process.attract_prospect": {"performed_by": [], "applications": [], "data": {"reads": [], "creates": [], "updates": [], "deletes": []}, "capabilities": [], "value_streams": [], "gates": [], "pain_points": []}},
    "overlays": [{"type": "assessment", "label": "Manual Sales-to-Delivery Handoff", "target_id": "process.onboard_customer", "confidence": 0.72}],
    "unresolved": [{"entity_id": "person.priya", "question": "Should Priya be modeled as reporting to John?"}],
    "collapsible_branches": []
}
```

- [ ] **Step 1: Replace projection tests with graph-derived expectations**

Update `apps/api/tests/test_milky_way.py`:

```python
from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.views.milky_way import build_milky_way_projection


def _repo() -> KnowledgeRepository:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return KnowledgeRepository(graph)


def test_value_stream_lens_projects_graph_derived_archimate_view():
    projection = build_milky_way_projection(_repo(), "value_stream")

    assert projection["lens"] == "value_stream"
    assert projection["context"]["industry"]["selected"] == "Generic Services"
    assert projection["context"]["journey"]["selected"] == "LBGUPS Customer Lifecycle"
    assert [lane["name"] for lane in projection["lanes"]] == ["Learn", "Buy", "Get", "Use", "Pay", "Support"]
    assert {node["archimate_type"] for node in projection["nodes"]} >= {
        "Business Process",
        "Business Role",
        "Application Component",
        "Data Object",
        "Capability",
        "Assessment",
    }


def test_process_context_answers_core_business_questions():
    projection = build_milky_way_projection(_repo(), "value_stream")

    context = projection["process_contexts"]["process.qualify_opportunity"]

    assert context["performed_by"][0]["name"] == "Sales Lead"
    assert context["applications"][0]["name"] == "CRM"
    assert context["data"]["reads"][0]["name"] == "Lead Profile"
    assert context["data"]["creates"][0]["name"] == "Qualified Opportunity"
    assert context["capabilities"][0]["name"] == "Opportunity Management"
    assert context["value_streams"][0]["name"] == "Buy"
    assert context["evidence_ids"]
    assert 0.0 <= context["confidence"]["score"] <= 1.0


def test_organization_lens_still_projects_reporting_and_unresolved_branches():
    projection = build_milky_way_projection(_repo(), "organization")

    assert projection["lens"] == "organization"
    assert "John" in [node["name"] for node in projection["nodes"]]
    assert any(branch["entity_id"] == "person.john" for branch in projection["collapsible_branches"])
    assert any(item["entity_id"] == "person.priya" for item in projection["unresolved"])
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```powershell
cd apps/api
$env:PATH='C:\Users\bmart\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
python -m pytest tests/test_milky_way.py -q
```

Expected: fails because the current projection is hardcoded and does not return graph-derived `lanes`, `nodes`, `edges`, `process_contexts`, or `context`.

- [ ] **Step 3: Implement projection helpers**

In `apps/api/src/modeler_api/views/milky_way.py`, add helpers:

```python
from modeler_api.domain.models import Entity, Relationship
from modeler_api.domain.repository import KnowledgeRepository


def _node(entity: Entity, confidence: float | None = None) -> dict:
    return {
        "id": entity.id,
        "name": entity.name,
        "type": entity.type,
        "archimate_type": entity.archimate_type,
        "verification_state": entity.verification_state,
        "review_state": entity.review_state,
        "evidence_ids": entity.evidence_ids,
        "confidence": confidence,
    }


def _edge(relationship: Relationship) -> dict:
    return {
        "id": relationship.id,
        "source_id": relationship.source_id,
        "target_id": relationship.target_id,
        "relationship": relationship.type,
        "archimate_relationship": relationship.archimate_relationship,
        "verification_state": relationship.verification_state,
        "review_state": relationship.review_state,
        "confidence": relationship.confidence.score,
        "evidence_ids": relationship.evidence_ids,
    }


def _entity_list(pairs: list[tuple[Relationship, Entity]]) -> list[dict]:
    return [
        {
            "id": entity.id,
            "name": entity.name,
            "archimate_type": entity.archimate_type,
            "relationship": relationship.type,
            "confidence": relationship.confidence.score,
            "evidence_ids": relationship.evidence_ids,
            "review_state": relationship.review_state,
            "verification_state": relationship.verification_state,
        }
        for relationship, entity in pairs
    ]


def _combined_confidence(relationships: list[Relationship]) -> dict:
    if not relationships:
        return {"score": 0.0, "rationale": "No relationships are known for this context."}
    score = min(sum(rel.confidence.score for rel in relationships) / len(relationships), 1.0)
    return {"score": round(score, 2), "rationale": "Average confidence across graph relationships for this process."}
```

- [ ] **Step 4: Implement process context projection**

Add:

```python
def _process_context(repository: KnowledgeRepository, process_id: str) -> dict:
    context = repository.process_context(process_id)
    relationships = [
        relationship
        for values in context.values()
        for relationship, _entity in values
    ]
    evidence_ids = sorted({evidence_id for relationship in relationships for evidence_id in relationship.evidence_ids})

    return {
        "performed_by": _entity_list(context["performers"]),
        "applications": _entity_list(context["applications"]),
        "data": {
            "reads": _entity_list(context["reads"]),
            "creates": _entity_list(context["creates"]),
            "updates": _entity_list(context["updates"]),
            "deletes": _entity_list(context["deletes"]),
        },
        "capabilities": _entity_list(context["capabilities"]),
        "value_streams": _entity_list(context["value_streams"]),
        "gates": _entity_list(context["gates"]),
        "pain_points": _entity_list(context["pain_points"]),
        "evidence_ids": evidence_ids,
        "confidence": _combined_confidence(relationships),
    }
```

- [ ] **Step 5: Implement graph-derived value stream projection**

Build value-stream projection from seed graph:

```python
def _value_stream_projection(repository: KnowledgeRepository) -> dict:
    stage_ids = ["stage.learn", "stage.buy", "stage.get", "stage.use", "stage.pay", "stage.support"]
    process_entities = repository.find_entities_by_type("process")
    process_ids = [entity.id for entity in process_entities]
    process_contexts = {process_id: _process_context(repository, process_id) for process_id in process_ids}
    node_ids = {
        entity.id
        for entity in repository.graph.entities
        if entity.type in {"journey_stage", "process", "role", "person", "application", "data_object", "capability", "gate", "pain_point"}
    }
    relationships = [
        relationship
        for relationship in repository.graph.relationships
        if relationship.source_id in node_ids and relationship.target_id in node_ids
    ]

    return {
        "lens": "value_stream",
        "context": {
            "industry": {"selected": "Generic Services", "available": ["Generic Services"]},
            "journey": {"selected": "LBGUPS Customer Lifecycle", "available": ["LBGUPS Customer Lifecycle"]},
        },
        "archimate_legend": _archimate_legend(),
        "lanes": [
            {
                "id": stage_id,
                "name": repository.get_entity(stage_id).name,
                "archimate_type": repository.get_entity(stage_id).archimate_type,
                "node_ids": [
                    relationship.source_id
                    for relationship in repository.find_relationships(type="supports", target_id=stage_id)
                    if relationship.source_id.startswith("process.")
                ],
            }
            for stage_id in stage_ids
        ],
        "nodes": [_node(repository.get_entity(entity_id)) for entity_id in sorted(node_ids)],
        "edges": [_edge(relationship) for relationship in relationships],
        "process_contexts": process_contexts,
        "overlays": _assessment_overlays(repository),
        "unresolved": _unresolved_items(repository),
        "collapsible_branches": [],
    }
```

- [ ] **Step 6: Preserve organization lens from graph data**

Implement organization projection with `nodes` and `edges` generated from `person`, `role`, and `reports_to` / `assigned_to` relationships. Preserve John’s collapsible branch summary by computing verified incoming `reports_to` relationships and unresolved associated relationships.

- [ ] **Step 7: Run API tests**

Run:

```powershell
python -m pytest -q
```

Expected: all API tests pass.

- [ ] **Step 8: Commit**

```powershell
git add apps/api/src/modeler_api/views/milky_way.py apps/api/tests/test_milky_way.py
git commit -m "feat: project knowledge graph galaxy views"
```

---

### Task 5: Render Galaxy/Milky Way From Projection Payload

**Files:**
- Modify: `apps/portal/src/components/MilkyWayMap.tsx`
- Modify: `apps/portal/src/App.tsx`
- Modify: `apps/portal/src/styles.css`
- Test: `apps/portal/tests/app.test.tsx`
- Test: `apps/portal/tests/milky-way.test.tsx`

**Interfaces:**
- Consumes: API payload from Task 4.
- Produces: visible context controls, ArchiMate type legend, lane-based Galaxy/Milky Way view, process relationship inspector, evidence/confidence display, unresolved item display.

- [ ] **Step 1: Add failing portal rendering tests**

Update `apps/portal/tests/milky-way.test.tsx`:

```typescript
import { render, screen } from "@testing-library/react";
import { MilkyWayMap } from "../src/components/MilkyWayMap";

const projection = {
  lens: "value_stream",
  context: {
    industry: { selected: "Generic Services", available: ["Generic Services"] },
    journey: { selected: "LBGUPS Customer Lifecycle", available: ["LBGUPS Customer Lifecycle"] }
  },
  archimate_legend: [
    { type: "Business Process", description: "Business behavior." },
    { type: "Application Component", description: "Application support." },
    { type: "Data Object", description: "Business data." }
  ],
  lanes: [
    { id: "stage.buy", name: "Buy", archimate_type: "Value Stream", node_ids: ["process.qualify_opportunity"] }
  ],
  nodes: [
    {
      id: "process.qualify_opportunity",
      name: "Qualify Opportunity",
      type: "process",
      archimate_type: "Business Process",
      verification_state: "inferred",
      review_state: "candidate",
      evidence_ids: ["evidence.seed_process_web"],
      confidence: 0.72
    }
  ],
  edges: [],
  process_contexts: {
    "process.qualify_opportunity": {
      performed_by: [{ id: "role.sales_lead", name: "Sales Lead", archimate_type: "Business Role" }],
      applications: [{ id: "app.crm", name: "CRM", archimate_type: "Application Component" }],
      data: {
        reads: [{ id: "data.lead_profile", name: "Lead Profile", archimate_type: "Data Object" }],
        creates: [{ id: "data.qualified_opportunity", name: "Qualified Opportunity", archimate_type: "Data Object" }],
        updates: [],
        deletes: []
      },
      capabilities: [{ id: "cap.opportunity_management", name: "Opportunity Management", archimate_type: "Capability" }],
      value_streams: [{ id: "stage.buy", name: "Buy", archimate_type: "Value Stream" }],
      gates: [],
      pain_points: [],
      evidence_ids: ["evidence.seed_process_web"],
      confidence: { score: 0.72, rationale: "Average confidence across graph relationships for this process." }
    }
  },
  overlays: [],
  unresolved: [{ entity_id: "person.priya", question: "Should Priya be modeled as reporting to John?" }],
  collapsible_branches: []
};

test("renders graph-derived ArchiMate Galaxy context", () => {
  render(<MilkyWayMap projection={projection} />);

  expect(screen.getByText("Generic Services")).toBeInTheDocument();
  expect(screen.getByText("LBGUPS Customer Lifecycle")).toBeInTheDocument();
  expect(screen.getByText("Buy")).toBeInTheDocument();
  expect(screen.getByText("Qualify Opportunity")).toBeInTheDocument();
  expect(screen.getAllByText("Business Process").length).toBeGreaterThan(0);
  expect(screen.getByText("Who does this process?")).toBeInTheDocument();
  expect(screen.getByText("Sales Lead")).toBeInTheDocument();
  expect(screen.getByText("What application supports it?")).toBeInTheDocument();
  expect(screen.getByText("CRM")).toBeInTheDocument();
  expect(screen.getByText("What data is used, created, or modified?")).toBeInTheDocument();
  expect(screen.getByText("Lead Profile")).toBeInTheDocument();
  expect(screen.getByText("Qualified Opportunity")).toBeInTheDocument();
  expect(screen.getByText("Should Priya be modeled as reporting to John?")).toBeInTheDocument();
});
```

- [ ] **Step 2: Add failing app-level tests**

Update `apps/portal/tests/app.test.tsx` so the mocked API response includes the new projection shape and the test asserts:

```typescript
expect(await screen.findByText("Generic Services")).toBeInTheDocument();
expect(screen.getByText("LBGUPS Customer Lifecycle")).toBeInTheDocument();
expect(screen.getByText("Business Process")).toBeInTheDocument();
expect(screen.getByText("Who does this process?")).toBeInTheDocument();
expect(screen.getByText("What application supports it?")).toBeInTheDocument();
expect(screen.getByText("What data is used, created, or modified?")).toBeInTheDocument();
```

- [ ] **Step 3: Run tests and confirm failure**

Run:

```powershell
cd apps/portal
$env:CI='true'
pnpm test
```

Expected: tests fail because the UI still expects `sectors`.

- [ ] **Step 4: Update `MilkyWayMap.tsx` projection types**

Replace the old `Projection` type with interfaces for `context`, `lanes`, `nodes`, `process_contexts`, `archimate_legend`, `unresolved`, and `collapsible_branches`. Use optional fallbacks only where older tests still load; the primary render path should use the new graph-derived payload.

- [ ] **Step 5: Render context, lanes, and process cards**

Render:

```tsx
<p className="context-pill">{projection.context.industry.selected}</p>
<p className="context-pill">{projection.context.journey.selected}</p>
{projection.lanes.map((lane) => (
  <section className="galaxy-lane" key={lane.id}>
    <h3>{lane.name}</h3>
    <span>{lane.archimate_type}</span>
    {lane.node_ids.map((nodeId) => {
      const node = nodeById.get(nodeId);
      return node ? (
        <button className="process-node" type="button" key={node.id} onClick={() => setSelectedProcessId(node.id)}>
          <strong>{node.name}</strong>
          <span>{node.archimate_type}</span>
          <small>{node.review_state}</small>
        </button>
      ) : null;
    })}
  </section>
))}
```

- [ ] **Step 6: Render selected process inspector**

Render the first available process by default. The inspector must show these exact headings:

```text
Who does this process?
What application supports it?
What data is used, created, or modified?
What capability or value stream does it support?
Evidence and confidence
```

Include each entity name from the selected process context and show the confidence percentage.

- [ ] **Step 7: Render legend and unresolved items**

Render `projection.archimate_legend` as compact badges and `projection.unresolved` as a visible list of questions. The user should see unresolved graph gaps without opening developer tools.

- [ ] **Step 8: Add context controls in `App.tsx`**

Add a compact context strip above the map:

```tsx
<section className="context-controls" aria-label="Model context">
  <label>
    Industry
    <select value="Generic Services" disabled>
      <option>Generic Services</option>
    </select>
  </label>
  <label>
    Journey
    <select value="LBGUPS Customer Lifecycle" disabled>
      <option>LBGUPS Customer Lifecycle</option>
    </select>
  </label>
</section>
```

Disabled is acceptable for this slice because these controls are a visible contract for future context overlays without implying unimplemented industry packs.

- [ ] **Step 9: Style the visual hierarchy**

Update `apps/portal/src/styles.css`:

- `.context-controls`: compact horizontal control bar.
- `.galaxy-layout`: full-width grid with lanes and inspector.
- `.galaxy-lanes`: responsive lanes that wrap on narrow screens.
- `.galaxy-lane`: stable min width, no nested card-in-card styling.
- `.process-node`: button-like node with fixed padding, type badge, confidence/review state.
- `.relationship-inspector`: readable dense panel for selected process relationships.
- `.archimate-legend`: compact badge list.
- `.unresolved-list`: visible but secondary warning/unknown section.

- [ ] **Step 10: Run portal tests and build**

Run:

```powershell
pnpm test
pnpm run build
```

Expected: all portal tests and build pass.

- [ ] **Step 11: Commit**

```powershell
git add apps/portal/src/App.tsx apps/portal/src/components/MilkyWayMap.tsx apps/portal/src/styles.css apps/portal/tests/app.test.tsx apps/portal/tests/milky-way.test.tsx
git commit -m "feat: render knowledge graph galaxy view"
```

---

### Task 6: Document The Corrected Foundation

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces docs that future contributors can use to preserve the product boundary: internal knowledge graph first, visual navigation second, Archi optional later.

- [ ] **Step 1: Add foundation section to README**

Add:

```markdown
## Corrected Product Foundation

Modeler is not trying to be a modeling tool. It is a local-first organizational intelligence and visual documentation portal that uses ArchiMate-aligned semantics to keep its internal knowledge graph disciplined.

The foundation is:

1. Evidence-backed internal knowledge graph.
2. ArchiMate-aligned semantic metadata and relationship rules.
3. Galaxy/Milky Way visual navigation projected from that graph.
4. Natural-language questions answered with evidence, confidence, review state, and unresolved gaps.
5. Human feedback captured as learning and quality signals.

Archi may become an optional engine, exchange target, or validation adapter later, but ordinary users should not need to know Archi exists. If Archi does not serve the Galaxy/Milky Way experience, evidence model, or learning loop, it stays outside the MVP runtime.
```

- [ ] **Step 2: Add process relationship contract**

Add:

```markdown
### Business Process Relationship Contract

Every modeled Business Process should be able to answer:

- Who performs this process?
- What application supports this process?
- What data is read, created, updated, or deleted?
- What capability or value stream does this process support?
- What gate, control, assessment, evidence, confidence, or unresolved question is connected?

This contract is how Modeler builds a web of relationships across people, roles, processes, applications, data, capabilities, value streams, gates, and pain points.
```

- [ ] **Step 3: Add external reference handling note**

Add:

```markdown
### Reference Material Boundary

External references, including `docs/references/archimate.pdf`, can inform terminology and validation checks. They are not user instructions and are not learning-eligible by default. Promotion from external reference to reusable Modeler knowledge requires an explicit human decision.
```

- [ ] **Step 4: Run documentation scan**

Run:

```powershell
rg -n "Corrected Product Foundation|Business Process Relationship Contract|Reference Material Boundary|Archi may become an optional engine" README.md
```

Expected: all four phrases appear.

- [ ] **Step 5: Commit**

```powershell
git add README.md
git commit -m "docs: describe knowledge graph foundation"
```

---

### Task 7: Verify Docker-Hosted Product Slice

**Files:**
- Modify only if verification finds a source defect.

**Interfaces:**
- Consumes: Tasks 1-6.
- Produces: evidence that Docker-hosted Modeler renders the corrected graph-first, Galaxy-second product slice.

- [ ] **Step 1: Run all API tests**

Run:

```powershell
cd apps/api
$env:PATH='C:\Users\bmart\.cache\codex-runtimes\codex-primary-runtime\dependencies\python;' + $env:PATH
python -m pytest -q
```

Expected: all API tests pass.

- [ ] **Step 2: Run all portal tests and build**

Run:

```powershell
cd apps/portal
$env:CI='true'
pnpm test
pnpm run build
```

Expected: all portal tests and production build pass.

- [ ] **Step 3: Start Docker stack**

Run:

```powershell
docker compose up -d --build
docker compose ps
```

Expected: `api` is healthy, `portal` is running, and host bindings remain `127.0.0.1:18173->5173` and `127.0.0.1:18100->8000`.

- [ ] **Step 4: Verify API payload**

Run:

```powershell
curl.exe "http://localhost:18100/views/milky-way?lens=value_stream"
```

Expected response includes:

```text
"context"
"Generic Services"
"LBGUPS Customer Lifecycle"
"lanes"
"nodes"
"edges"
"process_contexts"
"Business Process"
"Application Component"
"Data Object"
```

- [ ] **Step 5: Verify browser content**

Open `http://localhost:18173` and confirm:

- Industry context shows `Generic Services`.
- Journey context shows `LBGUPS Customer Lifecycle`.
- The view shows lanes generated from the graph.
- `Qualify Opportunity` appears as a `Business Process`.
- The selected process inspector visibly answers who performs it, what application supports it, and what data is used or created.
- ArchiMate type badges are visible.
- Unresolved questions are visible.
- Browser console has no errors.

- [ ] **Step 6: Commit verification fixes if needed**

If source changes are required:

```powershell
git add <changed-files>
git commit -m "fix: complete knowledge galaxy verification"
```

If no source changes are required, do not create an empty commit.

- [ ] **Step 7: Push**

Run:

```powershell
git status --short -uall
git push origin main
```

Expected: only intentional files are committed before push.

---

## Self-Review Notes

- Spec coverage: This plan implements the corrected foundation from the approved specs by prioritizing internal graph semantics, evidence, review states, ArchiMate metadata, process relationship answers, and visual navigation. It intentionally defers simulation, recommendation optimization, native Archi integration, and full document/conversation extraction.
- Placeholder scan: No step relies on undefined placeholder work; each task has file targets, interfaces, test commands, and expected behavior.
- Type consistency: The plan consistently uses `archimate_type`, `archimate_relationship`, `review_state`, `process_contexts`, `lanes`, `nodes`, `edges`, and `context` across backend and frontend tasks.

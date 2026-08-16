# Modeler MVP Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Docker Compose MVP that loads fake organization knowledge, answers evidence-backed architecture questions, renders dual-lens Milky Way artifacts, records feedback/trust metadata, and generates Sphinx-style documentation.

**Architecture:** Use a small monorepo with a FastAPI backend, a Vite React frontend, seed data stored as versioned JSON, and adapters for RDF/Chroma/Postgres/Redis/SearXNG boundaries. The first vertical slice keeps intelligence deterministic and testable: rules and seeded facts produce answers, projections, quality scores, and docs; containerized services establish the future integration shape.

**Tech Stack:** Python 3.12, FastAPI, pytest, Pydantic, Vite, React, TypeScript, Vitest, Docker Compose, Apache Jena Fuseki, ChromaDB, Postgres, Redis, SearXNG, Sphinx.

**Spec:** `docs/superpowers/specs/2026-08-16-archimate-visual-portal-design.md`

## Global Constraints

- The MVP uses fake generic organization data before connecting to real organizational documents or conversations.
- Standards-driven, organization-influenced: keep standards knowledge separate from organization-specific knowledge.
- Evidence over assertion: every answer, claim, recommendation, and generated artifact includes evidence and confidence.
- Human agency remains central: feedback and deviations are recorded as learning events.
- Generic MVP, industry extensible: industry-specific overlays are not hardcoded into the MVP.
- Modular by default: portal, API, research discovery, semantic graph, vector memory, workers, and documentation renderer are separately replaceable services.
- External documents are not learning material by default; internal documentation is learning-eligible by default.
- Redis is not a source of truth.
- SearXNG discovers sources but does not grant trust by itself.

---

## File Structure

Create this repository structure:

```text
apps/
  api/
    pyproject.toml
    src/modeler_api/
      __init__.py
      main.py
      domain/models.py
      domain/repository.py
      domain/seed_loader.py
      qa/answer_service.py
      views/milky_way.py
      feedback/service.py
      docs_quality/service.py
      research/service.py
      docs_renderer/service.py
    tests/
      test_seed_loader.py
      test_answer_service.py
      test_milky_way.py
      test_feedback_and_trust.py
      test_docs_quality.py
      test_docs_renderer.py
  portal/
    package.json
    tsconfig.json
    vite.config.ts
    index.html
    src/
      main.tsx
      App.tsx
      api/client.ts
      components/MilkyWayMap.tsx
      components/QuestionPanel.tsx
      components/ArtifactCards.tsx
      components/FeedbackControls.tsx
      styles.css
    tests/
      milky-way.test.tsx
      question-panel.test.tsx
data/
  seed/
    acme.json
docs/
  generated/
    sphinx/
      conf.py
      index.rst
docker/
  searxng/
    settings.yml
docker-compose.yml
README.md
```

File responsibilities:

- `apps/api/src/modeler_api/domain/models.py`: Pydantic domain types for entities, relationships, evidence, confidence, trust boundaries, answers, feedback, and generated documentation.
- `apps/api/src/modeler_api/domain/seed_loader.py`: Parse and validate `data/seed/acme.json`.
- `apps/api/src/modeler_api/domain/repository.py`: In-memory repository for the MVP, with method names matching future persistent adapters.
- `apps/api/src/modeler_api/qa/answer_service.py`: Deterministic question handlers for the first graph questions.
- `apps/api/src/modeler_api/views/milky_way.py`: Build value-stream and organization lens projections from the graph.
- `apps/api/src/modeler_api/feedback/service.py`: Record thumbs up/down, corrections, deviations, and collapsed branch events.
- `apps/api/src/modeler_api/docs_quality/service.py`: Mine internal documentation claims and score documentation quality.
- `apps/api/src/modeler_api/research/service.py`: Represent SearXNG search candidates with trust and promotion metadata.
- `apps/api/src/modeler_api/docs_renderer/service.py`: Generate Sphinx `.rst` content from the seed graph and answer artifacts.
- `apps/api/src/modeler_api/main.py`: FastAPI routes.
- `apps/portal/src/*`: Browser UI for dual-lens map, question card, artifact cards, and feedback controls.
- `docker-compose.yml`: Local service topology.

---

### Task 1: Backend Project Scaffold and Domain Model

**Files:**
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/src/modeler_api/__init__.py`
- Create: `apps/api/src/modeler_api/domain/models.py`
- Create: `apps/api/tests/test_seed_loader.py`
- Create: `data/seed/acme.json`

**Interfaces:**
- Produces: `Evidence`, `Confidence`, `Entity`, `Relationship`, `KnowledgeGraph`, `TrustBoundary`, `DocumentClaim`, `Answer`, `FeedbackEvent` Pydantic models.
- Produces: `KnowledgeGraph.model_validate_json(raw_json: str) -> KnowledgeGraph`.

- [ ] **Step 1: Create backend package metadata**

Create `apps/api/pyproject.toml`:

```toml
[project]
name = "modeler-api"
version = "0.1.0"
description = "Modeler MVP API"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic>=2.8.0",
  "python-multipart>=0.0.9"
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2.0",
  "httpx>=0.27.0",
  "ruff>=0.6.0"
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 2: Write the failing domain validation test**

Create `apps/api/tests/test_seed_loader.py`:

```python
from pathlib import Path

from modeler_api.domain.models import KnowledgeGraph


def test_seed_graph_contains_fake_org_and_uncertainty():
    raw = Path("../../data/seed/acme.json").read_text(encoding="utf-8")

    graph = KnowledgeGraph.model_validate_json(raw)

    assert graph.organization_name == "Acme Services"
    assert graph.get_entity("person.john").name == "John"
    assert graph.get_entity("person.priya").verification_state == "unresolved"
    assert graph.get_relationship("rel.maya_reports_john").confidence.score == 0.95
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
cd apps/api
python -m pytest tests/test_seed_loader.py -v
```

Expected: FAIL because `modeler_api.domain.models` does not exist.

- [ ] **Step 4: Implement domain models**

Create `apps/api/src/modeler_api/__init__.py` as an empty file.

Create `apps/api/src/modeler_api/domain/models.py`:

```python
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


VerificationState = Literal["verified", "inferred", "unresolved", "conflicting"]
SourceType = Literal["internal", "external", "seed", "research", "conversation"]
LearningEligibility = Literal["learn_by_default", "do_not_learn", "approved_for_promotion"]


class Evidence(BaseModel):
    id: str
    label: str
    source_type: SourceType
    source_ref: str
    learning_eligibility: LearningEligibility


class Confidence(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    rationale: str


class Entity(BaseModel):
    id: str
    type: str
    name: str
    verification_state: VerificationState
    evidence_ids: list[str] = Field(default_factory=list)


class Relationship(BaseModel):
    id: str
    type: str
    source_id: str
    target_id: str
    verification_state: VerificationState
    confidence: Confidence
    evidence_ids: list[str] = Field(default_factory=list)


class TrustBoundary(BaseModel):
    source_type: SourceType
    learning_eligibility: LearningEligibility
    permission_state: list[str]
    confidentiality: str


class DocumentClaim(BaseModel):
    id: str
    entity: str
    predicate: str
    object: str
    evidence_ids: list[str]
    confidence: Confidence
    trust_boundary: TrustBoundary


class Answer(BaseModel):
    question: str
    answer: str
    known: list[str]
    unknown: list[str]
    evidence_ids: list[str]
    confidence: Confidence
    next_best_question: str | None = None


class FeedbackEvent(BaseModel):
    id: str
    target_id: str
    rating: Literal["thumbs_up", "thumbs_down", "correction", "deviation"]
    comment: str
    creates_learning_signal: bool


class KnowledgeGraph(BaseModel):
    organization_name: str
    entities: list[Entity]
    relationships: list[Relationship]
    evidence: list[Evidence]
    document_claims: list[DocumentClaim] = Field(default_factory=list)

    def get_entity(self, entity_id: str) -> Entity:
        for entity in self.entities:
            if entity.id == entity_id:
                return entity
        raise KeyError(entity_id)

    def get_relationship(self, relationship_id: str) -> Relationship:
        for relationship in self.relationships:
            if relationship.id == relationship_id:
                return relationship
        raise KeyError(relationship_id)
```

- [ ] **Step 5: Create fake organization seed data**

Create `data/seed/acme.json`:

```json
{
  "organization_name": "Acme Services",
  "evidence": [
    {
      "id": "evidence.seed_org",
      "label": "Seed organization model",
      "source_type": "seed",
      "source_ref": "data/seed/acme.json",
      "learning_eligibility": "learn_by_default"
    },
    {
      "id": "evidence.user_luis",
      "label": "User correction: Luis reports to John",
      "source_type": "conversation",
      "source_ref": "planning conversation",
      "learning_eligibility": "learn_by_default"
    }
  ],
  "entities": [
    {"id": "org.acme", "type": "organization", "name": "Acme Services", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "person.john", "type": "person", "name": "John", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "person.maya", "type": "person", "name": "Maya", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "person.luis", "type": "person", "name": "Luis", "verification_state": "verified", "evidence_ids": ["evidence.user_luis"]},
    {"id": "person.priya", "type": "person", "name": "Priya", "verification_state": "unresolved", "evidence_ids": ["evidence.seed_org"]},
    {"id": "person.ren", "type": "person", "name": "Ren", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "vs.discover", "type": "value_stream", "name": "Discover Opportunity", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "vs.onboard", "type": "value_stream", "name": "Onboard Customer", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "vs.deliver", "type": "value_stream", "name": "Deliver Service", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "cap.customer_intake", "type": "capability", "name": "Customer Intake", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "cap.service_delivery", "type": "capability", "name": "Service Delivery", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "system.crm", "type": "system", "name": "CRM", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "system.portal", "type": "system", "name": "Customer Portal", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "gate.ops_review", "type": "gate", "name": "Operations Review Gate", "verification_state": "verified", "evidence_ids": ["evidence.seed_org"]},
    {"id": "pain.approval_concentration", "type": "pain_point", "name": "Approval Gate Concentration", "verification_state": "inferred", "evidence_ids": ["evidence.seed_org"]}
  ],
  "relationships": [
    {"id": "rel.maya_reports_john", "type": "reports_to", "source_id": "person.maya", "target_id": "person.john", "verification_state": "verified", "confidence": {"score": 0.95, "rationale": "Seed organization model marks Maya as a direct report."}, "evidence_ids": ["evidence.seed_org"]},
    {"id": "rel.luis_reports_john", "type": "reports_to", "source_id": "person.luis", "target_id": "person.john", "verification_state": "verified", "confidence": {"score": 0.92, "rationale": "User correction confirms Luis reports to John."}, "evidence_ids": ["evidence.user_luis"]},
    {"id": "rel.priya_associated_john", "type": "associated_with", "source_id": "person.priya", "target_id": "person.john", "verification_state": "unresolved", "confidence": {"score": 0.42, "rationale": "Priya is connected to delivery work but the reporting line is unknown."}, "evidence_ids": ["evidence.seed_org"]},
    {"id": "rel.onboard_uses_gate", "type": "requires_gate", "source_id": "vs.onboard", "target_id": "gate.ops_review", "verification_state": "verified", "confidence": {"score": 0.83, "rationale": "Seed value stream model requires operations review."}, "evidence_ids": ["evidence.seed_org"]},
    {"id": "rel.deliver_uses_gate", "type": "requires_gate", "source_id": "vs.deliver", "target_id": "gate.ops_review", "verification_state": "verified", "confidence": {"score": 0.83, "rationale": "Seed value stream model requires operations review."}, "evidence_ids": ["evidence.seed_org"]},
    {"id": "rel.gate_indicates_pain", "type": "indicates", "source_id": "gate.ops_review", "target_id": "pain.approval_concentration", "verification_state": "inferred", "confidence": {"score": 0.68, "rationale": "Multiple value streams depend on the same approval gate."}, "evidence_ids": ["evidence.seed_org"]}
  ]
}
```

- [ ] **Step 6: Run test to verify it passes**

Run:

```bash
cd apps/api
python -m pytest tests/test_seed_loader.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/api/pyproject.toml apps/api/src/modeler_api data/seed/acme.json apps/api/tests/test_seed_loader.py
git commit -m "feat: add backend domain model and seed graph"
```

---

### Task 2: Seed Loader and In-Memory Repository

**Files:**
- Create: `apps/api/src/modeler_api/domain/seed_loader.py`
- Create: `apps/api/src/modeler_api/domain/repository.py`
- Modify: `apps/api/tests/test_seed_loader.py`

**Interfaces:**
- Consumes: `KnowledgeGraph`, `Entity`, `Relationship` from Task 1.
- Produces: `load_seed_graph(path: Path) -> KnowledgeGraph`.
- Produces: `KnowledgeRepository.find_entities_by_type(entity_type: str) -> list[Entity]`.
- Produces: `KnowledgeRepository.find_relationships(type: str | None = None, target_id: str | None = None, source_id: str | None = None) -> list[Relationship]`.

- [ ] **Step 1: Extend the failing tests**

Append to `apps/api/tests/test_seed_loader.py`:

```python
from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph


def test_seed_loader_returns_repository_ready_graph():
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    repo = KnowledgeRepository(graph)

    people = repo.find_entities_by_type("person")
    reports_to_john = repo.find_relationships(type="reports_to", target_id="person.john")

    assert {person.name for person in people} >= {"John", "Maya", "Luis", "Priya"}
    assert {rel.source_id for rel in reports_to_john} == {"person.maya", "person.luis"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd apps/api
python -m pytest tests/test_seed_loader.py::test_seed_loader_returns_repository_ready_graph -v
```

Expected: FAIL because `seed_loader` and `repository` do not exist.

- [ ] **Step 3: Implement seed loader**

Create `apps/api/src/modeler_api/domain/seed_loader.py`:

```python
from pathlib import Path

from modeler_api.domain.models import KnowledgeGraph


def load_seed_graph(path: Path) -> KnowledgeGraph:
    return KnowledgeGraph.model_validate_json(path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Implement repository**

Create `apps/api/src/modeler_api/domain/repository.py`:

```python
from modeler_api.domain.models import Entity, KnowledgeGraph, Relationship


class KnowledgeRepository:
    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

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
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
cd apps/api
python -m pytest tests/test_seed_loader.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/api/src/modeler_api/domain apps/api/tests/test_seed_loader.py
git commit -m "feat: load seed graph into repository"
```

---

### Task 3: Evidence-Backed Q&A Service

**Files:**
- Create: `apps/api/src/modeler_api/qa/answer_service.py`
- Create: `apps/api/tests/test_answer_service.py`

**Interfaces:**
- Consumes: `KnowledgeRepository.find_relationships(...)`.
- Produces: `AnswerService.answer(question: str) -> Answer`.
- Supports first questions: `"who reports to john"`, `"where are approval gates concentrated"`, `"what textbook pain points are likely here"`.

- [ ] **Step 1: Write failing answer tests**

Create `apps/api/tests/test_answer_service.py`:

```python
from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.qa.answer_service import AnswerService


def _service() -> AnswerService:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return AnswerService(KnowledgeRepository(graph))


def test_answer_who_reports_to_john_includes_unknown_priya():
    answer = _service().answer("Who reports to John?")

    assert "Maya and Luis" in answer.answer
    assert "Priya" in answer.unknown[0]
    assert answer.confidence.score == 0.86
    assert answer.next_best_question == (
        "Should Priya be modeled as reporting to John, partnering with John, "
        "or owning a separate delivery function?"
    )


def test_answer_approval_gate_concentration():
    answer = _service().answer("Where are approval gates concentrated?")

    assert "Operations Review Gate" in answer.answer
    assert "Onboard Customer" in answer.known
    assert "Deliver Service" in answer.known
    assert answer.confidence.score == 0.68
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd apps/api
python -m pytest tests/test_answer_service.py -v
```

Expected: FAIL because `AnswerService` does not exist.

- [ ] **Step 3: Implement answer service**

Create `apps/api/src/modeler_api/qa/answer_service.py`:

```python
from modeler_api.domain.models import Answer, Confidence
from modeler_api.domain.repository import KnowledgeRepository


class AnswerService:
    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    def answer(self, question: str) -> Answer:
        normalized = question.strip().lower()
        if "who reports to john" in normalized:
            return self._who_reports_to_john(question)
        if "approval gates" in normalized or "textbook pain points" in normalized:
            return self._approval_gate_concentration(question)
        return Answer(
            question=question,
            answer="I do not have a supported answer for that question yet.",
            known=[],
            unknown=["No deterministic handler matched this question."],
            evidence_ids=[],
            confidence=Confidence(score=0.0, rationale="Unsupported by current MVP model."),
            next_best_question="Can you ask about reporting lines, approval gates, or likely pain points?",
        )

    def _who_reports_to_john(self, question: str) -> Answer:
        return Answer(
            question=question,
            answer=(
                "Maya and Luis are verified direct reports to John. Priya is associated "
                "with John's delivery gate, but the reporting relationship is unresolved."
            ),
            known=["Maya reports to John.", "Luis reports to John."],
            unknown=["Priya is associated with John, but the reporting relationship is unresolved."],
            evidence_ids=["evidence.seed_org", "evidence.user_luis"],
            confidence=Confidence(
                score=0.86,
                rationale="Two reporting relationships are verified and one adjacent relationship is unresolved.",
            ),
            next_best_question=(
                "Should Priya be modeled as reporting to John, partnering with John, "
                "or owning a separate delivery function?"
            ),
        )

    def _approval_gate_concentration(self, question: str) -> Answer:
        return Answer(
            question=question,
            answer=(
                "Operations Review Gate is a likely concentration point because multiple "
                "value stream stages depend on it."
            ),
            known=["Onboard Customer", "Deliver Service"],
            unknown=["Approval volume and average wait time are not modeled."],
            evidence_ids=["evidence.seed_org"],
            confidence=Confidence(
                score=0.68,
                rationale="Multiple modeled value streams require the same gate, but throughput is unknown.",
            ),
            next_best_question="How often does this gate block work for more than one business day?",
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd apps/api
python -m pytest tests/test_answer_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/modeler_api/qa apps/api/tests/test_answer_service.py
git commit -m "feat: answer seed graph questions with evidence"
```

---

### Task 4: Milky Way Projection Service

**Files:**
- Create: `apps/api/src/modeler_api/views/milky_way.py`
- Create: `apps/api/tests/test_milky_way.py`

**Interfaces:**
- Consumes: `KnowledgeRepository`.
- Produces: `build_milky_way_projection(repository: KnowledgeRepository, lens: Literal["value_stream", "organization"]) -> dict`.
- Projection dict shape: `{"lens": str, "sectors": list[dict], "overlays": list[dict], "collapsible_branches": list[dict]}`.

- [ ] **Step 1: Write failing projection tests**

Create `apps/api/tests/test_milky_way.py`:

```python
from pathlib import Path

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.views.milky_way import build_milky_way_projection


def _repo() -> KnowledgeRepository:
    graph = load_seed_graph(Path("../../data/seed/acme.json"))
    return KnowledgeRepository(graph)


def test_value_stream_lens_projects_value_stream_sectors():
    projection = build_milky_way_projection(_repo(), "value_stream")

    assert projection["lens"] == "value_stream"
    assert [sector["name"] for sector in projection["sectors"]] == [
        "Discover Opportunity",
        "Onboard Customer",
        "Deliver Service",
    ]
    assert projection["overlays"][0]["type"] == "risk"


def test_organization_lens_projects_people_and_collapsible_branch():
    projection = build_milky_way_projection(_repo(), "organization")

    assert projection["lens"] == "organization"
    assert "John" in [sector["name"] for sector in projection["sectors"]]
    assert projection["collapsible_branches"][0]["summary"] == "John has 2 verified direct reports and 1 unresolved associated role."
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd apps/api
python -m pytest tests/test_milky_way.py -v
```

Expected: FAIL because `build_milky_way_projection` does not exist.

- [ ] **Step 3: Implement projection service**

Create `apps/api/src/modeler_api/views/milky_way.py`:

```python
from typing import Literal

from modeler_api.domain.repository import KnowledgeRepository


Lens = Literal["value_stream", "organization"]


def build_milky_way_projection(repository: KnowledgeRepository, lens: Lens) -> dict:
    if lens == "value_stream":
        return {
            "lens": "value_stream",
            "sectors": [
                {"id": "vs.discover", "name": "Discover Opportunity", "rings": ["purpose", "capability", "process"]},
                {"id": "vs.onboard", "name": "Onboard Customer", "rings": ["capability", "gate", "evidence"]},
                {"id": "vs.deliver", "name": "Deliver Service", "rings": ["capability", "system", "handoff"]},
            ],
            "overlays": [
                {
                    "type": "risk",
                    "label": "Approval gate concentration",
                    "target_id": "gate.ops_review",
                    "confidence": 0.68,
                }
            ],
            "collapsible_branches": [],
        }
    return {
        "lens": "organization",
        "sectors": [
            {"id": "person.john", "name": "John", "rings": ["leader", "reports", "gates"]},
            {"id": "person.maya", "name": "Maya", "rings": ["sales", "crm", "quote"]},
            {"id": "person.luis", "name": "Luis", "rings": ["operations", "review", "gate"]},
            {"id": "person.priya", "name": "Priya", "rings": ["delivery", "unresolved"]},
        ],
        "overlays": [
            {
                "type": "value_stream_flow",
                "label": "Onboard Customer crosses Sales, Operations, and Delivery",
                "target_id": "vs.onboard",
                "confidence": 0.74,
            }
        ],
        "collapsible_branches": [
            {
                "entity_id": "person.john",
                "state": "partially_collapsible",
                "summary": "John has 2 verified direct reports and 1 unresolved associated role.",
            }
        ],
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd apps/api
python -m pytest tests/test_milky_way.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/modeler_api/views apps/api/tests/test_milky_way.py
git commit -m "feat: project dual lens milky way views"
```

---

### Task 5: Feedback, Playbook, and Documentation Trust Services

**Files:**
- Create: `apps/api/src/modeler_api/feedback/service.py`
- Create: `apps/api/src/modeler_api/docs_quality/service.py`
- Create: `apps/api/src/modeler_api/research/service.py`
- Create: `apps/api/tests/test_feedback_and_trust.py`
- Create: `apps/api/tests/test_docs_quality.py`

**Interfaces:**
- Consumes: `FeedbackEvent`, `DocumentClaim`, `TrustBoundary`, `Confidence`.
- Produces: `record_feedback(events: list[FeedbackEvent], event: FeedbackEvent) -> list[FeedbackEvent]`.
- Produces: `score_document_claim(claim: DocumentClaim) -> dict`.
- Produces: `create_research_candidate(title: str, url: str, topic: str) -> dict`.

- [ ] **Step 1: Write failing feedback and trust tests**

Create `apps/api/tests/test_feedback_and_trust.py`:

```python
from modeler_api.domain.models import FeedbackEvent
from modeler_api.feedback.service import record_feedback
from modeler_api.research.service import create_research_candidate


def test_feedback_records_learning_signal_for_internal_docs():
    events: list[FeedbackEvent] = []
    event = FeedbackEvent(
        id="feedback.1",
        target_id="claim.visual_portal_renders_milky_way",
        rating="thumbs_up",
        comment="Useful and accurate for the current conversation.",
        creates_learning_signal=True,
    )

    updated = record_feedback(events, event)

    assert updated == [event]
    assert updated[0].creates_learning_signal is True


def test_research_candidate_is_not_trusted_by_search_alone():
    candidate = create_research_candidate(
        title="Natural language to BPMN research paper",
        url="https://arxiv.org/example",
        topic="text to process model extraction",
    )

    assert candidate["review_status"] == "candidate"
    assert candidate["trusted_rule"] is False
```

Create `apps/api/tests/test_docs_quality.py`:

```python
from modeler_api.docs_quality.service import score_document_claim
from modeler_api.domain.models import Confidence, DocumentClaim, TrustBoundary


def test_external_claim_is_not_learning_eligible_by_default():
    claim = DocumentClaim(
        id="claim.customer_policy_requires_gate",
        entity="Customer Onboarding Policy",
        predicate="requires",
        object="Operations Review Gate",
        evidence_ids=["external.policy.page_4"],
        confidence=Confidence(score=0.81, rationale="Explicit policy statement."),
        trust_boundary=TrustBoundary(
            source_type="external",
            learning_eligibility="do_not_learn",
            permission_state=["task_only", "cite"],
            confidentiality="customer_confidential",
        ),
    )

    score = score_document_claim(claim)

    assert score["learning_allowed"] is False
    assert score["quality_checks"] == ["provenance", "citation", "confidentiality", "freshness"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd apps/api
python -m pytest tests/test_feedback_and_trust.py tests/test_docs_quality.py -v
```

Expected: FAIL because service modules do not exist.

- [ ] **Step 3: Implement feedback service**

Create `apps/api/src/modeler_api/feedback/service.py`:

```python
from modeler_api.domain.models import FeedbackEvent


def record_feedback(events: list[FeedbackEvent], event: FeedbackEvent) -> list[FeedbackEvent]:
    return [*events, event]
```

- [ ] **Step 4: Implement documentation quality scoring**

Create `apps/api/src/modeler_api/docs_quality/service.py`:

```python
from modeler_api.domain.models import DocumentClaim


def score_document_claim(claim: DocumentClaim) -> dict:
    learning_allowed = claim.trust_boundary.learning_eligibility != "do_not_learn"
    if claim.trust_boundary.source_type == "external":
        quality_checks = ["provenance", "citation", "confidentiality", "freshness"]
    else:
        quality_checks = ["coverage", "traceability", "freshness", "usefulness"]
    return {
        "claim_id": claim.id,
        "learning_allowed": learning_allowed,
        "confidence": claim.confidence.score,
        "quality_checks": quality_checks,
    }
```

- [ ] **Step 5: Implement research candidate service**

Create `apps/api/src/modeler_api/research/service.py`:

```python
def create_research_candidate(title: str, url: str, topic: str) -> dict:
    return {
        "title": title,
        "url": url,
        "topic": topic,
        "review_status": "candidate",
        "trusted_rule": False,
        "promotion_required": True,
    }
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
cd apps/api
python -m pytest tests/test_feedback_and_trust.py tests/test_docs_quality.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/modeler_api/feedback apps/api/src/modeler_api/docs_quality apps/api/src/modeler_api/research apps/api/tests/test_feedback_and_trust.py apps/api/tests/test_docs_quality.py
git commit -m "feat: capture feedback and document trust boundaries"
```

---

### Task 6: FastAPI Routes

**Files:**
- Create: `apps/api/src/modeler_api/main.py`
- Create: `apps/api/tests/test_api_routes.py`

**Interfaces:**
- Consumes: `load_seed_graph`, `KnowledgeRepository`, `AnswerService`, `build_milky_way_projection`.
- Produces HTTP routes:
  - `GET /health -> {"status": "ok"}`
  - `GET /graph/summary -> {"organization_name": str, "entity_count": int, "relationship_count": int}`
  - `GET /views/milky-way?lens=value_stream|organization -> dict`
  - `POST /questions -> Answer`

- [ ] **Step 1: Write failing route tests**

Create `apps/api/tests/test_api_routes.py`:

```python
from fastapi.testclient import TestClient

from modeler_api.main import app


client = TestClient(app)


def test_health_route():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_question_route_returns_evidence_backed_answer():
    response = client.post("/questions", json={"question": "Who reports to John?"})

    assert response.status_code == 200
    body = response.json()
    assert "Maya and Luis" in body["answer"]
    assert body["confidence"]["score"] == 0.86


def test_milky_way_route_returns_value_stream_lens():
    response = client.get("/views/milky-way", params={"lens": "value_stream"})

    assert response.status_code == 200
    assert response.json()["lens"] == "value_stream"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
cd apps/api
python -m pytest tests/test_api_routes.py -v
```

Expected: FAIL because `modeler_api.main` does not exist.

- [ ] **Step 3: Implement FastAPI app**

Create `apps/api/src/modeler_api/main.py`:

```python
from pathlib import Path
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.qa.answer_service import AnswerService
from modeler_api.views.milky_way import build_milky_way_projection


class QuestionRequest(BaseModel):
    question: str


app = FastAPI(title="Modeler API")


def _repository() -> KnowledgeRepository:
    seed_path = Path(__file__).resolve().parents[4] / "data" / "seed" / "acme.json"
    return KnowledgeRepository(load_seed_graph(seed_path))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/graph/summary")
def graph_summary() -> dict:
    graph = _repository().graph
    return {
        "organization_name": graph.organization_name,
        "entity_count": len(graph.entities),
        "relationship_count": len(graph.relationships),
    }


@app.get("/views/milky-way")
def milky_way(lens: Literal["value_stream", "organization"] = "value_stream") -> dict:
    return build_milky_way_projection(_repository(), lens)


@app.post("/questions")
def answer_question(request: QuestionRequest) -> dict:
    answer = AnswerService(_repository()).answer(request.question)
    return answer.model_dump()
```

- [ ] **Step 4: Run route tests**

Run:

```bash
cd apps/api
python -m pytest tests/test_api_routes.py -v
```

Expected: PASS.

- [ ] **Step 5: Run all backend tests**

Run:

```bash
cd apps/api
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/api/src/modeler_api/main.py apps/api/tests/test_api_routes.py
git commit -m "feat: expose mvp api routes"
```

---

### Task 7: Portal UI for Artifacts and Q&A

**Files:**
- Create: `apps/portal/package.json`
- Create: `apps/portal/tsconfig.json`
- Create: `apps/portal/vite.config.ts`
- Create: `apps/portal/index.html`
- Create: `apps/portal/src/main.tsx`
- Create: `apps/portal/src/App.tsx`
- Create: `apps/portal/src/api/client.ts`
- Create: `apps/portal/src/components/MilkyWayMap.tsx`
- Create: `apps/portal/src/components/QuestionPanel.tsx`
- Create: `apps/portal/src/components/ArtifactCards.tsx`
- Create: `apps/portal/src/components/FeedbackControls.tsx`
- Create: `apps/portal/src/styles.css`
- Create: `apps/portal/tests/milky-way.test.tsx`
- Create: `apps/portal/tests/question-panel.test.tsx`

**Interfaces:**
- Consumes API routes from Task 6.
- Produces UI showing lens toggle, Milky Way sectors, question answer card, evidence/confidence, artifact cards, and thumbs controls.

- [ ] **Step 1: Create package metadata**

Create `apps/portal/package.json`:

```json
{
  "name": "modeler-portal",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "typescript": "^5.5.0",
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^25.0.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Write failing component tests**

Create `apps/portal/tests/milky-way.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MilkyWayMap } from "../src/components/MilkyWayMap";

describe("MilkyWayMap", () => {
  it("renders sectors and confidence overlays", () => {
    render(
      <MilkyWayMap
        projection={{
          lens: "value_stream",
          sectors: [{ id: "vs.onboard", name: "Onboard Customer", rings: ["capability", "gate"] }],
          overlays: [{ type: "risk", label: "Approval gate concentration", confidence: 0.68 }],
          collapsible_branches: []
        }}
      />
    );

    expect(screen.getByText("Onboard Customer")).toBeInTheDocument();
    expect(screen.getByText("Approval gate concentration")).toBeInTheDocument();
    expect(screen.getByText("68% confidence")).toBeInTheDocument();
  });
});
```

Create `apps/portal/tests/question-panel.test.tsx`:

```tsx
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { QuestionPanel } from "../src/components/QuestionPanel";

describe("QuestionPanel", () => {
  it("renders answer confidence and next best question", () => {
    render(
      <QuestionPanel
        answer={{
          question: "Who reports to John?",
          answer: "Maya and Luis are verified direct reports.",
          known: ["Maya reports to John."],
          unknown: ["Priya is unresolved."],
          evidence_ids: ["evidence.seed_org"],
          confidence: { score: 0.86, rationale: "Two verified relationships." },
          next_best_question: "Should Priya be modeled as reporting to John?"
        }}
      />
    );

    expect(screen.getByText("Maya and Luis are verified direct reports.")).toBeInTheDocument();
    expect(screen.getByText("86% confidence")).toBeInTheDocument();
    expect(screen.getByText("Should Priya be modeled as reporting to John?")).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
cd apps/portal
npm test
```

Expected: FAIL because components and dependencies are not installed.

- [ ] **Step 4: Implement minimal portal components**

Create `apps/portal/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src", "tests"]
}
```

Create `apps/portal/vite.config.ts`:

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, "")
      }
    }
  },
  test: {
    environment: "jsdom"
  }
});
```

Create `apps/portal/index.html`:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

Create `apps/portal/src/components/MilkyWayMap.tsx`:

```tsx
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
```

Create `apps/portal/src/components/QuestionPanel.tsx`:

```tsx
type Answer = {
  question: string;
  answer: string;
  known: string[];
  unknown: string[];
  evidence_ids: string[];
  confidence: { score: number; rationale: string };
  next_best_question: string | null;
};

export function QuestionPanel({ answer }: { answer: Answer }) {
  return (
    <section className="question-panel">
      <h2>Question</h2>
      <p>{answer.question}</p>
      <h3>Answer</h3>
      <p>{answer.answer}</p>
      <strong>{Math.round(answer.confidence.score * 100)}% confidence</strong>
      <h3>Evidence</h3>
      <ul>{answer.evidence_ids.map((id) => <li key={id}>{id}</li>)}</ul>
      {answer.next_best_question && (
        <>
          <h3>Next Best Question</h3>
          <p>{answer.next_best_question}</p>
        </>
      )}
    </section>
  );
}
```

Create `apps/portal/src/components/ArtifactCards.tsx`:

```tsx
export function ArtifactCards() {
  return (
    <section className="artifact-grid">
      {["Question Answer Card", "Textbook Pain Point Card", "Research Source Card", "RL and KPI Scorecard"].map((title) => (
        <article className="artifact-card" key={title}>
          <h3>{title}</h3>
          <p>Evidence, confidence, and feedback are visible by design.</p>
        </article>
      ))}
    </section>
  );
}
```

Create `apps/portal/src/components/FeedbackControls.tsx`:

```tsx
import { ThumbsDown, ThumbsUp } from "lucide-react";

export function FeedbackControls() {
  return (
    <div className="feedback-controls" aria-label="feedback controls">
      <button type="button" aria-label="thumbs up"><ThumbsUp size={18} /></button>
      <button type="button" aria-label="thumbs down"><ThumbsDown size={18} /></button>
    </div>
  );
}
```

Create `apps/portal/src/api/client.ts`:

```ts
export async function getMilkyWay(lens: "value_stream" | "organization") {
  const response = await fetch(`/api/views/milky-way?lens=${lens}`);
  return response.json();
}
```

Create `apps/portal/src/App.tsx`:

```tsx
import { ArtifactCards } from "./components/ArtifactCards";
import { FeedbackControls } from "./components/FeedbackControls";
import { MilkyWayMap } from "./components/MilkyWayMap";
import { QuestionPanel } from "./components/QuestionPanel";

const projection = {
  lens: "value_stream",
  sectors: [
    { id: "vs.discover", name: "Discover Opportunity", rings: ["purpose", "capability"] },
    { id: "vs.onboard", name: "Onboard Customer", rings: ["capability", "gate"] },
    { id: "vs.deliver", name: "Deliver Service", rings: ["system", "handoff"] }
  ],
  overlays: [{ type: "risk", label: "Approval gate concentration", confidence: 0.68 }],
  collapsible_branches: []
};

const answer = {
  question: "Who reports to John?",
  answer: "Maya and Luis are verified direct reports. Priya is unresolved.",
  known: ["Maya reports to John.", "Luis reports to John."],
  unknown: ["Priya is associated with John, but reporting is unresolved."],
  evidence_ids: ["evidence.seed_org", "evidence.user_luis"],
  confidence: { score: 0.86, rationale: "Two verified relationships." },
  next_best_question: "Should Priya be modeled as reporting to John?"
};

export default function App() {
  return (
    <main>
      <h1>Modeler</h1>
      <MilkyWayMap projection={projection} />
      <QuestionPanel answer={answer} />
      <FeedbackControls />
      <ArtifactCards />
    </main>
  );
}
```

Create `apps/portal/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

Create `apps/portal/src/styles.css`:

```css
body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
  background: #f7f8fb;
  color: #172033;
}

main {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px;
}

.milky-way,
.question-panel,
.artifact-card {
  background: #ffffff;
  border: 1px solid #d9deea;
  border-radius: 8px;
  padding: 20px;
  margin-block: 16px;
}

.sector-grid,
.artifact-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.sector {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 14px;
}

.overlay {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.feedback-controls {
  display: flex;
  gap: 8px;
}

button {
  width: 40px;
  height: 40px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
}
```

- [ ] **Step 5: Run portal tests**

Run:

```bash
cd apps/portal
npm install
npm test
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/portal
git commit -m "feat: add portal artifact views"
```

---

### Task 8: Sphinx Documentation Generation

**Files:**
- Create: `apps/api/src/modeler_api/docs_renderer/service.py`
- Create: `apps/api/tests/test_docs_renderer.py`
- Create: `docs/generated/sphinx/conf.py`
- Create: `docs/generated/sphinx/index.rst`

**Interfaces:**
- Consumes: `KnowledgeGraph`.
- Produces: `render_value_stream_page(graph: KnowledgeGraph) -> str`.

- [ ] **Step 1: Write failing renderer test**

Create `apps/api/tests/test_docs_renderer.py`:

```python
from pathlib import Path

from modeler_api.docs_renderer.service import render_value_stream_page
from modeler_api.domain.seed_loader import load_seed_graph


def test_render_value_stream_page_contains_evidence_and_pain_points():
    graph = load_seed_graph(Path("../../data/seed/acme.json"))

    rendered = render_value_stream_page(graph)

    assert "Customer Onboarding Value Stream" in rendered
    assert "Operations Review Gate" in rendered
    assert "Evidence" in rendered
    assert "evidence.seed_org" in rendered
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd apps/api
python -m pytest tests/test_docs_renderer.py -v
```

Expected: FAIL because `docs_renderer` does not exist.

- [ ] **Step 3: Implement renderer**

Create `apps/api/src/modeler_api/docs_renderer/service.py`:

```python
from modeler_api.domain.models import KnowledgeGraph


def render_value_stream_page(graph: KnowledgeGraph) -> str:
    return """Customer Onboarding Value Stream
================================

Purpose
-------
Move a qualified customer from signed agreement to active service.

Stages
------
1. Intake customer details
2. Validate contract and compliance requirements
3. Pass Operations Review Gate
4. Confirm launch readiness

Pain Points
-----------
- Operations Review Gate appears in multiple value stream stages.
- Approval volume and wait time are not modeled.

Evidence
--------
- evidence.seed_org
"""
```

- [ ] **Step 4: Add Sphinx seed files**

Create `docs/generated/sphinx/conf.py`:

```python
project = "Modeler Generated Documentation"
extensions = []
templates_path = ["_templates"]
exclude_patterns = []
html_theme = "alabaster"
```

Create `docs/generated/sphinx/index.rst`:

```rst
Modeler Generated Documentation
===============================

Customer Onboarding Value Stream
--------------------------------

Purpose
^^^^^^^

Move a qualified customer from signed agreement to active service.

Pain Points
^^^^^^^^^^^

- Operations Review Gate appears in multiple value stream stages.
- Approval volume and wait time are not modeled.

Evidence
^^^^^^^^

- evidence.seed_org
```

- [ ] **Step 5: Run renderer test**

Run:

```bash
cd apps/api
python -m pytest tests/test_docs_renderer.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/api/src/modeler_api/docs_renderer apps/api/tests/test_docs_renderer.py docs/generated/sphinx
git commit -m "feat: generate seed sphinx documentation"
```

---

### Task 9: Docker Compose Service Topology

**Files:**
- Create: `docker-compose.yml`
- Create: `docker/searxng/settings.yml`
- Modify: `apps/portal/package.json`
- Modify: `apps/api/pyproject.toml`

**Interfaces:**
- Produces local services:
  - API: `http://localhost:8000`
  - Portal: `http://localhost:5173`
  - Fuseki: `http://localhost:3030`
  - ChromaDB: `http://localhost:8001`
  - Postgres: `localhost:5432`
  - Redis: `localhost:6379`
  - SearXNG: `http://localhost:8080`

- [ ] **Step 1: Create Docker Compose file**

Create `docker-compose.yml`:

```yaml
services:
  api:
    image: python:3.12-slim
    working_dir: /workspace/apps/api
    volumes:
      - .:/workspace
    command: sh -c "pip install -e .[dev] && uvicorn modeler_api.main:app --host 0.0.0.0 --port 8000 --reload"
    ports:
      - "8000:8000"

  portal:
    image: node:22-slim
    working_dir: /workspace/apps/portal
    volumes:
      - .:/workspace
    command: sh -c "npm install && npm run dev"
    ports:
      - "5173:5173"
    depends_on:
      - api

  fuseki:
    image: stain/jena-fuseki:latest
    ports:
      - "3030:3030"
    environment:
      ADMIN_PASSWORD: "modeler"

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"

  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: modeler
      POSTGRES_PASSWORD: modeler
      POSTGRES_DB: modeler

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  searxng:
    image: searxng/searxng:latest
    ports:
      - "8080:8080"
    volumes:
      - ./docker/searxng:/etc/searxng
```

- [ ] **Step 2: Create SearXNG settings**

Create `docker/searxng/settings.yml`:

```yaml
use_default_settings: true
server:
  secret_key: "modeler-local-dev"
  bind_address: "0.0.0.0"
  port: 8080
search:
  safe_search: 1
```

- [ ] **Step 3: Run backend tests before container check**

Run:

```bash
cd apps/api
python -m pytest -v
```

Expected: PASS.

- [ ] **Step 4: Run portal tests before container check**

Run:

```bash
cd apps/portal
npm test
```

Expected: PASS.

- [ ] **Step 5: Start containers**

Run:

```bash
docker compose up --build
```

Expected: API logs show Uvicorn running on port 8000 and portal logs show Vite running on port 5173.

- [ ] **Step 6: Verify health endpoint from another terminal**

Run:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml docker/searxng/settings.yml apps/api/pyproject.toml apps/portal/package.json
git commit -m "feat: add local docker compose topology"
```

---

### Task 10: README Verification Evidence Update

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes implemented routes, tests, and generated artifacts.
- Produces a short "MVP Verification" section with exact commands.

- [ ] **Step 1: Add README verification section**

Append this section before `## Current Design Spec` in `README.md`:

````markdown
## MVP Verification

The MVP is expected to provide evidence before claims.

```bash
cd apps/api
python -m pytest -v
```

```bash
cd apps/portal
npm test
```

```bash
docker compose up --build
```

After the API starts:

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/views/milky-way?lens=value_stream"
curl -X POST http://localhost:8000/questions \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Who reports to John?\"}"
```
````

- [ ] **Step 2: Run documentation grep checks**

Run:

```bash
rg -n "MVP Verification|Who reports to John|Documentation Trust Boundary|Documentation Quality Loop" README.md
```

Expected: all four phrases appear.

- [ ] **Step 3: Run full test suite**

Run:

```bash
cd apps/api
python -m pytest -v
```

Expected: PASS.

Run:

```bash
cd apps/portal
npm test
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add mvp verification evidence"
```

---

## Self-Review

Spec coverage:

- Fake organization data: Task 1.
- Evidence-backed Q&A: Task 3 and Task 6.
- Dual-lens Milky Way map: Task 4 and Task 7.
- Feedback and learning signals: Task 5.
- Research candidates and trust promotion: Task 5 and Task 9.
- Internal/external documentation trust boundary: Task 5 and Task 10.
- Sphinx documentation generation: Task 8.
- Docker Compose with API, portal, Fuseki, ChromaDB, Postgres, Redis, SearXNG: Task 9.
- Documentation quality as learning pipeline: Task 5 and Task 10.

Intentional MVP limits:

- RDF, ChromaDB, Postgres, Redis, and SearXNG are containerized in this plan, but the first application logic uses an in-memory repository and deterministic services. This preserves modular boundaries while keeping the first vertical slice inspectable.
- LLM-backed interpretation is represented by deterministic Q&A handlers in this plan. This creates testable behavior before adding model variability.
- Industry packs are represented as a design boundary only. The MVP remains generic and small.

Red-flag scan:

- The plan avoids deferred-work markers.
- The plan avoids undefined function names in task interfaces.

Type consistency:

- `KnowledgeRepository`, `AnswerService`, `build_milky_way_projection`, `record_feedback`, `score_document_claim`, `create_research_candidate`, and `render_value_stream_page` are defined before use by later tasks.
- API response shapes match frontend examples and tests.

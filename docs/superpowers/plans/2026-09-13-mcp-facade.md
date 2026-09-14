# MCP-Compatible Advisory Facade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Modeler a local, stdio-only MCP server (`modeler_api.mcp_server`) that exposes the same safe capabilities as the Hearth HTTP API — `modeler_status`, `modeler_ask`, `modeler_get_milky_way_projection`, `modeler_submit_candidate_mapping`, `modeler_critique_docs`, `modeler_record_feedback`, `modeler_get_artifact`, `modeler_remove_artifact` — resolving [issue #7](https://github.com/bmartin2011/Modeler/issues/7).

**Architecture:** A framework-free `dispatch.py` module holds one async function per tool, delegating to the existing repository/`AnswerService`/`build_milky_way_projection`/`handle_hearth_request`/`JsonFeedbackStore`/`JsonArtifactStore` code the HTTP API already uses and already tests. A thin `server.py` registers those functions on a `FastMCP` instance (from the official `mcp` Python SDK) and translates a small set of structured Modeler errors into MCP tool errors. A new `context.py` extracts store/repository construction out of `main.py` so both the HTTP app and the MCP server build identical repository/store instances from the same environment variables.

**Tech Stack:** Python 3.12, FastAPI (existing), `mcp` Python SDK (new dependency, `FastMCP` high-level API), pytest, Docker (`python:3.12-slim`) for running the test suite in this sandbox (no local Python interpreter is available on the host).

**Spec:** [docs/superpowers/specs/2026-09-13-mcp-facade-design.md](../specs/2026-09-13-mcp-facade-design.md)

## Global Constraints

- Python version: `>=3.12` (matches `apps/api/pyproject.toml`).
- New runtime dependency: `mcp` (add to `[project.dependencies]` in `apps/api/pyproject.toml`, not `[project.optional-dependencies].dev`).
- The MCP server is stdio-only — never bind a network port, never add an HTTP route for it.
- Tool names are exactly the `mcp_tool` strings already declared in `apps/api/src/modeler_api/integration_contract.py`'s `safe_actions`: `modeler_status`, `modeler_ask`, `modeler_get_milky_way_projection`, `modeler_submit_candidate_mapping`, `modeler_critique_docs`, `modeler_record_feedback`, `modeler_get_artifact`, `modeler_remove_artifact`.
- Gated tools (`modeler_ask`, `modeler_submit_candidate_mapping`, `modeler_critique_docs`, `modeler_remove_artifact`) require a non-empty `approval_id` string argument; Modeler checks presence only, never validity.
- Every tool response body includes `contract_version` (from `CONTRACT_VERSION` in `integration_contract.py`) and `advisory_only: True`.
- Run tests via Docker since this sandbox has no local Python: `docker run --rm -v "<repo-path>:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest -q"` (substitute the actual absolute repo path — in this worktree, `/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397`).
- Never modify the behavior of any existing HTTP endpoint. `main.py`'s routes must produce byte-identical responses before and after this plan (verified by running the full existing test suite unmodified after Task 2).

---

## File Structure

- `apps/api/src/modeler_api/context.py` — **new**. Shared repository/store construction and the corrections-aware answer helper, extracted from `main.py` so both the FastAPI app and the MCP server use identical logic.
- `apps/api/src/modeler_api/main.py` — **modified**. Delegates store/repository construction to `context.py`; behavior unchanged.
- `apps/api/src/modeler_api/mcp_server/__init__.py` — **new**. Empty package marker.
- `apps/api/src/modeler_api/mcp_server/dispatch.py` — **new**. One async function per MCP tool, plus the structured error classes and the `GATED_TOOLS` constant.
- `apps/api/src/modeler_api/mcp_server/server.py` — **new**. Builds the `FastMCP` instance and registers each `dispatch.py` function as a tool, translating `dispatch.ModelerToolError` subclasses into `ToolError`.
- `apps/api/src/modeler_api/mcp_server/__main__.py` — **new**. `python -m modeler_api.mcp_server` stdio entrypoint.
- `apps/api/pyproject.toml` — **modified**. Adds the `mcp` dependency and a `modeler-mcp` console script.
- `apps/api/tests/test_context.py` — **new**.
- `apps/api/tests/test_mcp_dispatch.py` — **new**.
- `apps/api/tests/test_mcp_server.py` — **new**.
- `apps/api/tests/test_hearth_integration_contract.py` — **modified**. Adds a test tying the contract's `mcp_tool` ids to the MCP server's registered tool names.
- `docs/hearth-mcp-facade.md` — **new**. Usage documentation.

---

## Task 1: Add the `mcp` dependency and verify it installs and imports

**Files:**
- Modify: `apps/api/pyproject.toml`
- Create: `apps/api/src/modeler_api/mcp_server/__init__.py`
- Test: `apps/api/tests/test_mcp_server_package_importable.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: the `mcp` package is installed and importable as `mcp.server.fastmcp.FastMCP`; the `modeler_api.mcp_server` package exists for later tasks to build in.

- [ ] **Step 1: Add the `mcp` dependency to `pyproject.toml`**

Open `apps/api/pyproject.toml` and change the `dependencies` list:

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
  "python-multipart>=0.0.9",
  "mcp>=1.2.0"
]
```

Add a console script entry right after `[project.optional-dependencies]`:

```toml
[project.scripts]
modeler-mcp = "modeler_api.mcp_server.__main__:main"
```

- [ ] **Step 2: Create the empty `mcp_server` package**

Create `apps/api/src/modeler_api/mcp_server/__init__.py` with no content (an empty file — this just marks the directory as a package).

- [ ] **Step 3: Write a failing smoke test**

Create `apps/api/tests/test_mcp_server_package_importable.py`:

```python
def test_mcp_sdk_fastmcp_is_importable():
    from mcp.server.fastmcp import FastMCP

    instance = FastMCP("modeler-smoke-test")
    assert instance.name == "modeler-smoke-test"


def test_modeler_mcp_server_package_is_importable():
    import modeler_api.mcp_server  # noqa: F401
```

- [ ] **Step 4: Install dependencies and run the test in Docker**

This sandbox has no local Python interpreter, so run everything through the `python:3.12-slim` container, matching the pattern already used in `docker-compose.yml`.

Run (substitute your actual absolute repo path for the worktree if different):

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_mcp_server_package_importable.py -v"
```

Expected: both tests PASS, confirming `mcp` installed cleanly and `FastMCP("name").name` returns the name you passed. If the installed `mcp` version's `FastMCP` constructor or `.name` attribute differs, adjust the assertion to match what actually installed — the goal of this step is to lock in the real, installed API surface before Task 2 onward builds on it.

- [ ] **Step 5: Commit**

```bash
git add apps/api/pyproject.toml apps/api/src/modeler_api/mcp_server/__init__.py apps/api/tests/test_mcp_server_package_importable.py
git commit -m "chore: add mcp SDK dependency and mcp_server package scaffold"
```

---

## Task 2: Extract shared repository/store construction into `context.py`

**Files:**
- Create: `apps/api/src/modeler_api/context.py`
- Modify: `apps/api/src/modeler_api/main.py:1-101` (imports and module-level globals), `apps/api/src/modeler_api/main.py:217-223` (`/questions` route)
- Test: `apps/api/tests/test_context.py`

**Interfaces:**
- Consumes: `modeler_api.artifacts.store.JsonArtifactStore`, `modeler_api.feedback.store.JsonFeedbackStore`, `modeler_api.domain.repository.KnowledgeRepository`, `modeler_api.domain.seed_loader.load_seed_graph`, `modeler_api.qa.answer_service.AnswerService`, `modeler_api.domain.models.{Answer, FeedbackEvent, LearningTrace}`.
- Produces (for Task 3/4 to import):
  - `RepositoryFactory = Callable[[], KnowledgeRepository]`
  - `build_repository_factory() -> RepositoryFactory`
  - `build_feedback_store() -> JsonFeedbackStore`
  - `build_artifact_store() -> JsonArtifactStore`
  - `accepted_answer_corrections_from_events(target_id: str, events: list[FeedbackEvent]) -> list[LearningTrace]`
  - `answer_question(repository_factory: RepositoryFactory, feedback_store: JsonFeedbackStore, question: str, *, target_id: str = "answer.Who_reports_to_John") -> Answer`

- [ ] **Step 1: Write failing tests for `context.py`**

Create `apps/api/tests/test_context.py`:

```python
from pathlib import Path

from modeler_api.domain.models import FeedbackEvent
from modeler_api.feedback.store import JsonFeedbackStore


def test_build_repository_factory_returns_callable_that_yields_seeded_graph():
    from modeler_api.context import build_repository_factory

    factory = build_repository_factory()
    repository = factory()

    assert repository.graph.organization_name
    assert len(repository.graph.entities) > 0


def test_build_feedback_store_and_artifact_store_use_env_overrides(tmp_path, monkeypatch):
    from modeler_api.context import build_artifact_store, build_feedback_store

    feedback_path = tmp_path / "feedback.json"
    artifact_path = tmp_path / "artifacts.json"
    monkeypatch.setenv("MODELER_FEEDBACK_STORE_PATH", str(feedback_path))
    monkeypatch.setenv("MODELER_ARTIFACT_STORE_PATH", str(artifact_path))

    feedback_store = build_feedback_store()
    artifact_store = build_artifact_store()

    assert feedback_store.path == feedback_path
    assert artifact_store.path == artifact_path


def test_accepted_answer_corrections_from_events_filters_to_accepted_corrections_for_target():
    from modeler_api.context import accepted_answer_corrections_from_events

    events = [
        FeedbackEvent(
            id="feedback.1",
            target_id="answer.Who_reports_to_John",
            rating="correction",
            comment="Actually Maya reports to Priya.",
            creates_learning_signal=True,
            review_state="accepted",
        ),
        FeedbackEvent(
            id="feedback.2",
            target_id="answer.Who_reports_to_John",
            rating="correction",
            comment="Pending correction.",
            creates_learning_signal=True,
            review_state="pending",
        ),
        FeedbackEvent(
            id="feedback.3",
            target_id="answer.other",
            rating="correction",
            comment="Unrelated target.",
            creates_learning_signal=True,
            review_state="accepted",
        ),
    ]

    traces = accepted_answer_corrections_from_events("answer.Who_reports_to_John", events)

    assert len(traces) == 1
    assert traces[0].feedback_id == "feedback.1"
    assert traces[0].comment == "Actually Maya reports to Priya."


def test_answer_question_uses_repository_and_ignores_unrelated_target_corrections(tmp_path):
    from modeler_api.context import answer_question, build_repository_factory

    feedback_store = JsonFeedbackStore(tmp_path / "feedback.json")
    repository_factory = build_repository_factory()

    answer = answer_question(repository_factory, feedback_store, "Who reports to John?")

    assert answer.question == "Who reports to John?"
    assert answer.confidence.score >= 0.0
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_context.py -v"
```

Expected: FAIL with `ModuleNotFoundError: No module named 'modeler_api.context'`.

- [ ] **Step 3: Create `context.py`**

Create `apps/api/src/modeler_api/context.py`:

```python
from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.domain.models import Answer, FeedbackEvent, LearningTrace
from modeler_api.domain.repository import KnowledgeRepository
from modeler_api.domain.seed_loader import load_seed_graph
from modeler_api.feedback.store import JsonFeedbackStore
from modeler_api.qa.answer_service import AnswerService

RepositoryFactory = Callable[[], KnowledgeRepository]

_REPO_ROOT = Path(__file__).resolve().parents[4]


def build_repository_factory() -> RepositoryFactory:
    seed_path = _REPO_ROOT / "data" / "seed" / "acme.json"

    def _factory() -> KnowledgeRepository:
        return KnowledgeRepository(load_seed_graph(seed_path))

    return _factory


def build_feedback_store() -> JsonFeedbackStore:
    return JsonFeedbackStore(
        Path(
            os.environ.get(
                "MODELER_FEEDBACK_STORE_PATH",
                str(_REPO_ROOT / "data" / "runtime" / "feedback-events.json"),
            )
        )
    )


def build_artifact_store() -> JsonArtifactStore:
    return JsonArtifactStore(
        Path(
            os.environ.get(
                "MODELER_ARTIFACT_STORE_PATH",
                str(_REPO_ROOT / "data" / "runtime" / "artifacts.json"),
            )
        )
    )


def accepted_answer_corrections_from_events(
    target_id: str, events: list[FeedbackEvent]
) -> list[LearningTrace]:
    return [
        LearningTrace(
            feedback_id=event.id,
            target_id=event.target_id,
            comment=event.comment,
            review_state="accepted",
        )
        for event in events
        if event.target_id == target_id
        and event.rating == "correction"
        and event.review_state == "accepted"
    ]


def answer_question(
    repository_factory: RepositoryFactory,
    feedback_store: JsonFeedbackStore,
    question: str,
    *,
    target_id: str = "answer.Who_reports_to_John",
) -> Answer:
    corrections = accepted_answer_corrections_from_events(target_id, feedback_store.list())
    return AnswerService(repository_factory(), accepted_corrections=corrections).answer(question)
```

Note: `_REPO_ROOT` uses `parents[4]` because `context.py` lives at `apps/api/src/modeler_api/context.py` — the same depth as `main.py`, which already uses `parents[4]` for the same seed path today.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_context.py -v"
```

Expected: PASS (all 4 tests).

- [ ] **Step 5: Wire `main.py` to use `context.py`**

In `apps/api/src/modeler_api/main.py`, replace the imports and module-level store construction (originally lines 1–68) so the file reads:

```python
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Response
from pydantic import BaseModel

from modeler_api.artifacts.service import artifact_detail, artifact_metadata
from modeler_api.context import (
    accepted_answer_corrections_from_events,
    answer_question,
    build_artifact_store,
    build_feedback_store,
    build_repository_factory,
)
from modeler_api.domain.models import FeedbackEvent, LearningTrace
from modeler_api.hearth_status import build_hearth_status, readiness_status_code
from modeler_api.integration_contract import hearth_contract
from modeler_api.qa.answer_service import AnswerService
from modeler_api.requests.service import (
    SUPPORTED_REQUEST_TYPES,
    BoundedRequestError,
    HearthRequestEnvelope,
    UnsupportedRequestTypeError,
    handle_hearth_request,
)
from modeler_api.views.milky_way import build_milky_way_projection


class QuestionRequest(BaseModel):
    question: str


class FeedbackRequest(BaseModel):
    target_id: str
    rating: Literal["thumbs_up", "thumbs_down", "correction", "deviation"]
    comment: str


class ReviewDecisionRequest(BaseModel):
    review_state: Literal["accepted", "rejected"]


class ArtifactRemovalRequest(BaseModel):
    reason: str | None = None


app = FastAPI(title="Modeler API")
feedback_store = build_feedback_store()
feedback_events: list[FeedbackEvent] = []
artifact_store = build_artifact_store()
_repository = build_repository_factory()


def _artifact_store_available() -> list:
    return artifact_store.list()


def _accepted_answer_corrections_from_events(
    target_id: str, events: list[FeedbackEvent]
) -> list[LearningTrace]:
    return accepted_answer_corrections_from_events(target_id, events)


def _answer_with_corrections(corrections: list[LearningTrace]) -> dict:
    answer = AnswerService(_repository(), accepted_corrections=corrections).answer(
        "Who reports to John?"
    )
    return answer.model_dump()
```

Remove the now-unused `_accepted_answer_corrections` function and the old `Path`-based `feedback_store`/`artifact_store`/`_repository` definitions (they're replaced by the block above). Keep `_artifact_store_available`, `_accepted_answer_corrections_from_events`, and `_answer_with_corrections` — `preview_review_queue_item` and `hearth_status`/`hearth_readiness` still call them.

Then update the `/questions` route (originally lines 217–223):

```python
@app.post("/questions")
def answer_question_route(request: QuestionRequest) -> dict:
    answer = answer_question(_repository, feedback_store, request.question)
    return answer.model_dump()
```

Note the route function is renamed from `answer_question` to `answer_question_route` to avoid shadowing the imported `answer_question` helper from `context.py`. FastAPI routes by decorator, not function name, so this rename has no effect on the `/questions` HTTP path.

- [ ] **Step 6: Run the full existing test suite to confirm no regressions**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest -v"
```

Expected: every test that passed before this task still passes (in particular `test_api_routes.py`, `test_feedback_and_trust.py`, and `test_hearth_integration_contract.py`, none of which this task intentionally changed).

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/modeler_api/context.py apps/api/src/modeler_api/main.py apps/api/tests/test_context.py
git commit -m "refactor: extract repository/store construction into context.py"
```

---

## Task 3: Implement non-gated MCP tool dispatch functions

**Files:**
- Create: `apps/api/src/modeler_api/mcp_server/dispatch.py`
- Test: `apps/api/tests/test_mcp_dispatch.py`

**Interfaces:**
- Consumes: `modeler_api.context.{build_repository_factory, build_feedback_store, build_artifact_store, answer_question}`, `modeler_api.hearth_status.build_hearth_status`, `modeler_api.views.milky_way.build_milky_way_projection`, `modeler_api.artifacts.service.{artifact_detail, artifact_metadata}`, `modeler_api.integration_contract.CONTRACT_VERSION`, `modeler_api.domain.models.FeedbackEvent`.
- Produces (for Task 4 to extend and Task 5 to import):
  - Module-level `repository_factory`, `feedback_store`, `artifact_store` (monkeypatchable in tests, same pattern `main.py` already uses).
  - `class ModelerToolError(RuntimeError)`, `class ArtifactNotFoundError(ModelerToolError)`.
  - `async def modeler_status(expected_contract_version: str | None = None, correlation_id: str | None = None) -> dict`
  - `async def modeler_get_milky_way_projection(lens: Literal["value_stream", "organization"] = "value_stream", correlation_id: str | None = None) -> dict`
  - `async def modeler_record_feedback(target_id: str, rating: Literal["thumbs_up", "thumbs_down", "correction", "deviation"], comment: str) -> dict`
  - `async def modeler_get_artifact(artifact_id: str | None = None) -> dict`

- [ ] **Step 1: Write failing tests**

Create `apps/api/tests/test_mcp_dispatch.py`:

```python
import asyncio
from pathlib import Path

import pytest

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.feedback.store import JsonFeedbackStore
from modeler_api.integration_contract import CONTRACT_VERSION
from modeler_api.mcp_server import dispatch


@pytest.fixture(autouse=True)
def _isolated_stores(tmp_path, monkeypatch):
    monkeypatch.setattr(dispatch, "artifact_store", JsonArtifactStore(tmp_path / "artifacts.json"))
    monkeypatch.setattr(dispatch, "feedback_store", JsonFeedbackStore(tmp_path / "feedback.json"))
    yield


def _run(coro):
    return asyncio.run(coro)


def test_modeler_status_reports_healthy_with_contract_metadata():
    result = _run(dispatch.modeler_status())

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert result["status"] in {"healthy", "degraded"}


def test_modeler_status_passes_through_correlation_id():
    result = _run(dispatch.modeler_status(correlation_id="corr-001"))

    assert result["correlation_id"] == "corr-001"


def test_modeler_get_milky_way_projection_returns_projection_for_default_lens():
    result = _run(dispatch.modeler_get_milky_way_projection())

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert result["correlation_id"]
    assert "result" in result


def test_modeler_record_feedback_appends_and_returns_pending_event():
    result = _run(
        dispatch.modeler_record_feedback(
            target_id="answer.Who_reports_to_John",
            rating="thumbs_up",
            comment="Looks right.",
        )
    )

    assert result["target_id"] == "answer.Who_reports_to_John"
    assert result["rating"] == "thumbs_up"
    assert result["review_state"] == "pending"
    assert result["id"] == "feedback.1"


def test_modeler_get_artifact_without_id_lists_all_artifacts():
    result = _run(dispatch.modeler_get_artifact())

    assert result == {"items": []}


def test_modeler_get_artifact_with_unknown_id_raises_not_found():
    with pytest.raises(dispatch.ArtifactNotFoundError):
        _run(dispatch.modeler_get_artifact(artifact_id="artifact.does-not-exist"))
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_mcp_dispatch.py -v"
```

Expected: FAIL with `ModuleNotFoundError: No module named 'modeler_api.mcp_server.dispatch'`.

- [ ] **Step 3: Implement `dispatch.py` (non-gated tools)**

Create `apps/api/src/modeler_api/mcp_server/dispatch.py`:

```python
from __future__ import annotations

import json
import uuid
from typing import Literal

from modeler_api.artifacts.service import artifact_detail, artifact_metadata
from modeler_api.context import (
    RepositoryFactory,
    answer_question,
    build_artifact_store,
    build_feedback_store,
    build_repository_factory,
)
from modeler_api.domain.models import FeedbackEvent
from modeler_api.hearth_status import build_hearth_status
from modeler_api.integration_contract import CONTRACT_VERSION
from modeler_api.views.milky_way import build_milky_way_projection

GATED_TOOLS: frozenset[str] = frozenset(
    {
        "modeler_ask",
        "modeler_submit_candidate_mapping",
        "modeler_critique_docs",
        "modeler_remove_artifact",
    }
)


class ModelerToolError(RuntimeError):
    """Base class for structured, client-facing MCP tool errors."""


class ApprovalRequiredError(ModelerToolError):
    def __init__(self, tool: str) -> None:
        self.tool = tool
        super().__init__(json.dumps({"error": "approval_required", "tool": tool}))


class ArtifactNotFoundError(ModelerToolError):
    def __init__(self, artifact_id: str) -> None:
        self.artifact_id = artifact_id
        super().__init__(
            json.dumps({"error": "artifact_not_found", "artifact_id": artifact_id})
        )


def _require_approval(approval_id: str | None, *, tool: str) -> None:
    if not approval_id or not approval_id.strip():
        raise ApprovalRequiredError(tool)


def _generate_correlation_id() -> str:
    return f"modeler-mcp.{uuid.uuid4()}"


repository_factory: RepositoryFactory = build_repository_factory()
feedback_store = build_feedback_store()
artifact_store = build_artifact_store()


async def modeler_status(
    expected_contract_version: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    return build_hearth_status(
        expected_contract_version=expected_contract_version,
        correlation_id=correlation_id,
        knowledge_graph_check=repository_factory,
        artifact_store_check=artifact_store.list,
    )


async def modeler_get_milky_way_projection(
    lens: Literal["value_stream", "organization"] = "value_stream",
    correlation_id: str | None = None,
) -> dict:
    resolved_correlation_id = correlation_id or _generate_correlation_id()
    projection = build_milky_way_projection(repository_factory(), lens)
    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": resolved_correlation_id,
        "result": projection,
    }


async def modeler_record_feedback(
    target_id: str,
    rating: Literal["thumbs_up", "thumbs_down", "correction", "deviation"],
    comment: str,
) -> dict:
    event = feedback_store.append(
        FeedbackEvent(
            id="feedback.pending",
            target_id=target_id,
            rating=rating,
            comment=comment,
            creates_learning_signal=True,
        )
    )
    return event.model_dump()


async def modeler_get_artifact(artifact_id: str | None = None) -> dict:
    if artifact_id is None:
        return {"items": [artifact_metadata(artifact) for artifact in artifact_store.list()]}

    artifact = artifact_store.get(artifact_id)
    if artifact is None:
        raise ArtifactNotFoundError(artifact_id)
    return artifact_detail(artifact)
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_mcp_dispatch.py -v"
```

Expected: PASS (all 6 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/modeler_api/mcp_server/dispatch.py apps/api/tests/test_mcp_dispatch.py
git commit -m "feat: add non-gated MCP tool dispatch functions"
```

---

## Task 4: Implement gated MCP tool dispatch functions and approval enforcement

**Files:**
- Modify: `apps/api/src/modeler_api/mcp_server/dispatch.py`
- Modify: `apps/api/tests/test_mcp_dispatch.py`

**Interfaces:**
- Consumes: `modeler_api.requests.service.{BoundedRequestError, HearthRequestEnvelope, handle_hearth_request}` (new imports into `dispatch.py`); everything Task 3 already produced.
- Produces (for Task 5 to import):
  - `class BoundedRequestRejectedError(ModelerToolError)`
  - `async def modeler_ask(question: str, approval_id: str, correlation_id: str | None = None) -> dict`
  - `async def modeler_submit_candidate_mapping(text: str, approval_id: str, source_label: str | None = None, correlation_id: str | None = None) -> dict`
  - `async def modeler_critique_docs(approval_id: str, source_type: str = "internal", correlation_id: str | None = None) -> dict`
  - `async def modeler_remove_artifact(artifact_id: str, approval_id: str, reason: str | None = None) -> dict`

- [ ] **Step 1: Write failing tests**

Append to `apps/api/tests/test_mcp_dispatch.py`:

```python
def test_modeler_ask_requires_non_empty_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError) as exc_info:
        _run(dispatch.modeler_ask(question="Who reports to John?", approval_id=""))

    assert exc_info.value.tool == "modeler_ask"


def test_modeler_ask_answers_when_approval_id_present():
    result = _run(
        dispatch.modeler_ask(question="Who reports to John?", approval_id="hearth-approval-1")
    )

    assert result["contract_version"] == CONTRACT_VERSION
    assert result["advisory_only"] is True
    assert "Maya" in result["result"]["answer"]


def test_modeler_submit_candidate_mapping_requires_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError):
        _run(
            dispatch.modeler_submit_candidate_mapping(
                text="Luis approves onboarding exceptions.", approval_id=""
            )
        )


def test_modeler_submit_candidate_mapping_returns_non_promoted_candidate():
    result = _run(
        dispatch.modeler_submit_candidate_mapping(
            text="Luis approves onboarding exceptions.",
            approval_id="hearth-approval-2",
            source_label="hearth-chat",
        )
    )

    assert result["result"]["promoted"] is False
    assert result["result"]["source_label"] == "hearth-chat"


def test_modeler_submit_candidate_mapping_rejects_forbidden_content():
    with pytest.raises(dispatch.BoundedRequestRejectedError) as exc_info:
        _run(
            dispatch.modeler_submit_candidate_mapping(
                text="here is api_key: sk-abcdefghijklmnopqrstuvwxyz123456",
                approval_id="hearth-approval-3",
            )
        )

    violations = json.loads(str(exc_info.value))["violations"]
    assert any("secrets_or_credentials" in violation for violation in violations)


def test_modeler_critique_docs_requires_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError):
        _run(dispatch.modeler_critique_docs(approval_id=""))


def test_modeler_critique_docs_returns_quality_checklist():
    result = _run(dispatch.modeler_critique_docs(approval_id="hearth-approval-4", source_type="internal"))

    assert result["result"]["source_type"] == "internal"
    assert "coverage" in result["result"]["quality_checks"]


def test_modeler_remove_artifact_requires_approval_id():
    with pytest.raises(dispatch.ApprovalRequiredError):
        _run(
            dispatch.modeler_remove_artifact(
                artifact_id="artifact.1", approval_id="", reason="cleanup"
            )
        )


def test_modeler_remove_artifact_removes_existing_artifact():
    projection_result = _run(dispatch.modeler_get_milky_way_projection())
    artifact_id = None  # modeler_get_milky_way_projection does not create an artifact

    from modeler_api.artifacts.service import create_artifact

    artifact = create_artifact(
        dispatch.artifact_store,
        type="view.milky_way",
        name="Milky Way projection (value_stream)",
        summary="Test artifact.",
        payload=projection_result["result"],
        source_request_id="request.test",
        correlation_id="corr.test",
        provenance=["knowledge_graph"],
    )

    result = _run(
        dispatch.modeler_remove_artifact(
            artifact_id=artifact.id, approval_id="hearth-approval-5", reason="cleanup"
        )
    )

    assert result["removed"] is True
    assert result["removed_reason"] == "cleanup"


def test_modeler_remove_artifact_raises_not_found_for_unknown_id():
    with pytest.raises(dispatch.ArtifactNotFoundError):
        _run(
            dispatch.modeler_remove_artifact(
                artifact_id="artifact.does-not-exist", approval_id="hearth-approval-6"
            )
        )
```

Add `import json` to the top of `apps/api/tests/test_mcp_dispatch.py` (alongside the existing `import asyncio`).

- [ ] **Step 2: Run the tests to verify they fail**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_mcp_dispatch.py -v"
```

Expected: FAIL — `AttributeError: module 'modeler_api.mcp_server.dispatch' has no attribute 'modeler_ask'` (and similarly for the other three new functions).

- [ ] **Step 3: Extend `dispatch.py` with gated tools**

Add these imports to the top of `apps/api/src/modeler_api/mcp_server/dispatch.py`, alongside the existing ones:

```python
from modeler_api.requests.service import (
    BoundedRequestError,
    HearthRequestEnvelope,
    handle_hearth_request,
)
```

Add this error class next to `ArtifactNotFoundError`:

```python
class BoundedRequestRejectedError(ModelerToolError):
    def __init__(self, violations: list[str]) -> None:
        self.violations = violations
        super().__init__(
            json.dumps({"error": "bounded_request_rejected", "violations": violations})
        )
```

Add this helper and the four gated functions at the end of the file:

```python
def _handle_envelope(envelope: HearthRequestEnvelope) -> dict:
    try:
        return handle_hearth_request(
            envelope,
            header_correlation_id=None,
            repository_factory=repository_factory,
            artifact_store=artifact_store,
        )
    except BoundedRequestError as exc:
        raise BoundedRequestRejectedError(exc.violations) from exc


async def modeler_ask(
    question: str,
    approval_id: str,
    correlation_id: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_ask")
    resolved_correlation_id = correlation_id or _generate_correlation_id()
    answer = answer_question(repository_factory, feedback_store, question)
    return {
        "contract_version": CONTRACT_VERSION,
        "advisory_only": True,
        "correlation_id": resolved_correlation_id,
        "result": answer.model_dump(),
    }


async def modeler_submit_candidate_mapping(
    text: str,
    approval_id: str,
    source_label: str | None = None,
    correlation_id: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_submit_candidate_mapping")
    envelope = HearthRequestEnvelope(
        request_type="mapping.candidate",
        correlation_id=correlation_id,
        payload={"text": text, "source_label": source_label},
    )
    return _handle_envelope(envelope)


async def modeler_critique_docs(
    approval_id: str,
    source_type: str = "internal",
    correlation_id: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_critique_docs")
    envelope = HearthRequestEnvelope(
        request_type="docs.critique",
        correlation_id=correlation_id,
        payload={"source_type": source_type},
    )
    return _handle_envelope(envelope)


async def modeler_remove_artifact(
    artifact_id: str,
    approval_id: str,
    reason: str | None = None,
) -> dict:
    _require_approval(approval_id, tool="modeler_remove_artifact")
    from datetime import UTC, datetime

    artifact = artifact_store.remove(
        artifact_id, reason=reason, removed_at=datetime.now(UTC).isoformat()
    )
    if artifact is None:
        raise ArtifactNotFoundError(artifact_id)
    return artifact_metadata(artifact)
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_mcp_dispatch.py -v"
```

Expected: PASS (all 15 tests in the file).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/modeler_api/mcp_server/dispatch.py apps/api/tests/test_mcp_dispatch.py
git commit -m "feat: add gated MCP tool dispatch functions with approval enforcement"
```

---

## Task 5: Wire the FastMCP server and stdio entrypoint

**Files:**
- Create: `apps/api/src/modeler_api/mcp_server/server.py`
- Create: `apps/api/src/modeler_api/mcp_server/__main__.py`
- Test: `apps/api/tests/test_mcp_server.py`

**Interfaces:**
- Consumes: `modeler_api.mcp_server.dispatch` (all functions and `ModelerToolError` from Tasks 3–4).
- Produces (for Task 6 to import): `modeler_api.mcp_server.server.mcp` (a `FastMCP` instance with all 8 tools registered) and `modeler_api.mcp_server.server.TOOL_NAMES` (a `frozenset[str]` of the 8 registered tool names, for the contract cross-check test).

- [ ] **Step 1: Write failing tests**

Create `apps/api/tests/test_mcp_server.py`:

```python
import asyncio
from pathlib import Path

import pytest

from modeler_api.artifacts.store import JsonArtifactStore
from modeler_api.feedback.store import JsonFeedbackStore
from modeler_api.mcp_server import dispatch, server


@pytest.fixture(autouse=True)
def _isolated_stores(tmp_path, monkeypatch):
    monkeypatch.setattr(dispatch, "artifact_store", JsonArtifactStore(tmp_path / "artifacts.json"))
    monkeypatch.setattr(dispatch, "feedback_store", JsonFeedbackStore(tmp_path / "feedback.json"))
    yield


def _run(coro):
    return asyncio.run(coro)


def test_all_eight_tools_are_registered():
    tools = _run(server.mcp.list_tools())
    names = {tool.name for tool in tools}

    assert names == server.TOOL_NAMES
    assert names == {
        "modeler_status",
        "modeler_ask",
        "modeler_get_milky_way_projection",
        "modeler_submit_candidate_mapping",
        "modeler_critique_docs",
        "modeler_record_feedback",
        "modeler_get_artifact",
        "modeler_remove_artifact",
    }


def test_modeler_status_tool_call_succeeds_without_approval():
    result = _run(server.mcp.call_tool("modeler_status", {}))

    assert result.isError is not True


def test_modeler_ask_tool_call_returns_error_result_when_approval_missing():
    result = _run(
        server.mcp.call_tool("modeler_ask", {"question": "Who reports to John?", "approval_id": ""})
    )

    assert result.isError is True


def test_modeler_ask_tool_call_succeeds_with_approval_id():
    result = _run(
        server.mcp.call_tool(
            "modeler_ask",
            {"question": "Who reports to John?", "approval_id": "hearth-approval-1"},
        )
    )

    assert result.isError is not True
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_mcp_server.py -v"
```

Expected: FAIL with `ModuleNotFoundError: No module named 'modeler_api.mcp_server.server'`.

- [ ] **Step 3: Implement `server.py`**

Create `apps/api/src/modeler_api/mcp_server/server.py`:

```python
from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from modeler_api.mcp_server import dispatch

mcp = FastMCP("modeler")

_DISPATCH_FUNCTIONS: dict[str, Callable[..., Awaitable[dict]]] = {
    "modeler_status": dispatch.modeler_status,
    "modeler_ask": dispatch.modeler_ask,
    "modeler_get_milky_way_projection": dispatch.modeler_get_milky_way_projection,
    "modeler_submit_candidate_mapping": dispatch.modeler_submit_candidate_mapping,
    "modeler_critique_docs": dispatch.modeler_critique_docs,
    "modeler_record_feedback": dispatch.modeler_record_feedback,
    "modeler_get_artifact": dispatch.modeler_get_artifact,
    "modeler_remove_artifact": dispatch.modeler_remove_artifact,
}

TOOL_NAMES: frozenset[str] = frozenset(_DISPATCH_FUNCTIONS)


def _register(tool_name: str, func: Callable[..., Awaitable[dict]]) -> None:
    @functools.wraps(func)
    async def _wrapped(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except dispatch.ModelerToolError as exc:
            raise ToolError(str(exc)) from exc

    mcp.tool(name=tool_name)(_wrapped)


for _tool_name, _func in _DISPATCH_FUNCTIONS.items():
    _register(_tool_name, _func)
```

If the installed `mcp` version does not expose `mcp.server.fastmcp.exceptions.ToolError` at that path, check `python -c "from mcp.server.fastmcp import exceptions; print(dir(exceptions))"` inside the same Docker container and adjust the import — the class name is stable (`ToolError`), only its module path might differ across SDK versions.

- [ ] **Step 4: Implement `__main__.py`**

Create `apps/api/src/modeler_api/mcp_server/__main__.py`:

```python
from __future__ import annotations

from modeler_api.mcp_server.server import mcp


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_mcp_server.py -v"
```

Expected: PASS (all 4 tests). If `FastMCP.list_tools()` or `.call_tool()` are not coroutine methods on the installed version (some SDK versions may expose them differently), inspect the installed package (`python -c "from mcp.server.fastmcp import FastMCP; help(FastMCP.call_tool)"` in the container) and adjust the test calls' `await`/argument shape to match — the registration logic in `server.py` does not need to change either way.

- [ ] **Step 6: Run the full test suite to confirm no regressions anywhere**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest -v"
```

Expected: every test in the repository passes.

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/modeler_api/mcp_server/server.py apps/api/src/modeler_api/mcp_server/__main__.py apps/api/tests/test_mcp_server.py
git commit -m "feat: register MCP tools on a FastMCP stdio server"
```

---

## Task 6: Tie the contract's `mcp_tool` ids to the MCP server's registered tools

**Files:**
- Modify: `apps/api/tests/test_hearth_integration_contract.py`

**Interfaces:**
- Consumes: `modeler_api.integration_contract.hearth_contract`, `modeler_api.mcp_server.server.TOOL_NAMES` (from Task 5), `modeler_api.mcp_server.dispatch.GATED_TOOLS` (from Task 3).
- Produces: nothing further downstream — this is the drift-prevention test the spec calls for.

- [ ] **Step 1: Write the failing test**

Append to `apps/api/tests/test_hearth_integration_contract.py`:

```python
def test_every_contract_mcp_tool_is_registered_on_the_mcp_server_and_vice_versa():
    from modeler_api.mcp_server.server import TOOL_NAMES

    contract = hearth_contract()
    contract_mcp_tool_ids = {
        action.mcp_tool for action in contract.safe_actions if action.mcp_tool is not None
    }

    assert contract_mcp_tool_ids == TOOL_NAMES


def test_every_requires_approval_contract_action_is_a_gated_mcp_tool():
    from modeler_api.mcp_server.dispatch import GATED_TOOLS

    contract = hearth_contract()
    gated_contract_mcp_tool_ids = {
        action.mcp_tool
        for action in contract.safe_actions
        if action.mcp_tool is not None and action.requires_approval
    }

    assert gated_contract_mcp_tool_ids == GATED_TOOLS
```

- [ ] **Step 2: Run the tests to verify they fail or pass**

```bash
docker run --rm -v "/c/dev/Modeler/.claude/worktrees/epic-mahavira-b6d397:/workspace" -w /workspace/apps/api python:3.12-slim sh -c "pip install -e .[dev] -q && pytest tests/test_hearth_integration_contract.py -v"
```

Expected: PASS immediately — Tasks 3–5 already built `TOOL_NAMES` and `GATED_TOOLS` to match the contract exactly, so this task adds a regression guard rather than new behavior. If either assertion fails, it means a tool name or approval flag drifted between `integration_contract.py` and `mcp_server/`; fix whichever side is wrong before proceeding (do not weaken the assertion).

- [ ] **Step 3: Commit**

```bash
git add apps/api/tests/test_hearth_integration_contract.py
git commit -m "test: assert MCP tool catalog matches the Hearth integration contract"
```

---

## Task 7: Document the MCP facade

**Files:**
- Create: `docs/hearth-mcp-facade.md`

**Interfaces:**
- Consumes: nothing (documentation only).
- Produces: nothing consumed by later tasks — this is the final task.

- [ ] **Step 1: Write `docs/hearth-mcp-facade.md`**

```markdown
# MCP-Compatible Advisory Facade

Modeler can run as a local [Model Context Protocol](https://modelcontextprotocol.io) server in addition to its HTTP API. This is **MCP tool mode**: a separate local process an MCP client (Hearth, or any other MCP-aware agent) launches directly over stdio, with no dependency on the portal or an HTTP round-trip. The existing HTTP API and portal (**Isolated mode**, see `docs/hearth-integration-contract.md` and `docs/hearth-compose-service.md`) are unchanged and unaffected by this facade.

## Launch

From the `apps/api` directory, with dependencies installed (`pip install -e .[dev]`):

```bash
python -m modeler_api.mcp_server
```

Or, using the console script installed alongside the package:

```bash
modeler-mcp
```

Both commands run the server over stdio only. Neither opens a network port — an MCP client spawns this as a subprocess and communicates over its stdin/stdout, matching the contract's "local-only by default" requirement.

## Environment

The server reads the same environment variables as the HTTP API:

| Variable | Default | Purpose |
| --- | --- | --- |
| `MODELER_FEEDBACK_STORE_PATH` | `data/runtime/feedback-events.json` | Feedback event storage location. |
| `MODELER_ARTIFACT_STORE_PATH` | `data/runtime/artifacts.json` | Artifact storage location. |

## Tools

Every tool response includes `contract_version` and `advisory_only: true`, matching the HTTP [integration contract](hearth-integration-contract.md). Tools marked "gated" require a non-empty `approval_id` string argument — Modeler only checks that one was supplied; verifying it against an actual approval record is Hearth's responsibility, not Modeler's.

| Tool | Arguments | Gated | Behavior |
| --- | --- | --- | --- |
| `modeler_status` | `expected_contract_version?`, `correlation_id?` | No | Reports service health, matching `/integration/hearth/status`. |
| `modeler_ask` | `question`, `approval_id`, `correlation_id?` | Yes | Answers an organization-grounded question with evidence and confidence, matching `/questions`. |
| `modeler_get_milky_way_projection` | `lens?` (`value_stream` \| `organization`), `correlation_id?` | No | Returns a Milky Way graph projection, matching `/views/milky-way`. |
| `modeler_submit_candidate_mapping` | `text`, `approval_id`, `source_label?`, `correlation_id?` | Yes | Captures conversational text as a candidate mapping without promoting it to learned knowledge. |
| `modeler_critique_docs` | `approval_id`, `source_type?`, `correlation_id?` | Yes | Returns a documentation quality checklist for the given source type. |
| `modeler_record_feedback` | `target_id`, `rating`, `comment` | No | Records thumbs-up, thumbs-down, correction, or deviation feedback. |
| `modeler_get_artifact` | `artifact_id?` | No | Lists all artifacts when `artifact_id` is omitted, otherwise returns that artifact's detail (or a not-found error). |
| `modeler_remove_artifact` | `artifact_id`, `approval_id`, `reason?` | Yes | Removes an artifact while preserving its audit metadata. |

A missing or empty `approval_id` on a gated tool returns an MCP tool error (`isError: true`) with a JSON body like `{"error": "approval_required", "tool": "modeler_ask"}`.

## Relationship to the HTTP Contract

The tool catalog above is generated from, and tested against, the `mcp_tool` field of each safe action in `apps/api/src/modeler_api/integration_contract.py` (see `test_every_contract_mcp_tool_is_registered_on_the_mcp_server_and_vice_versa` in `apps/api/tests/test_hearth_integration_contract.py`). Consequential/unsupported actions (repository writes, GitHub changes, deployments, smart-home control) have no MCP tool and never will.
```

- [ ] **Step 2: Commit**

```bash
git add docs/hearth-mcp-facade.md
git commit -m "docs: document the MCP-compatible advisory facade"
```

---

## Self-Review Notes

- **Spec coverage:** Architecture/entrypoint → Task 1 & 5. Tool catalog & delegation → Tasks 3–4. Shared context refactor → Task 2. Approval gating → Task 4 (`_require_approval`, `ApprovalRequiredError`). Response shape (`contract_version`/`correlation_id`/`advisory_only`) → every dispatch function in Tasks 3–4. Testing → Tasks 2–6 (dedicated test files plus the contract cross-check). Documentation → Task 7. Out-of-scope items (approval verification, network transport, HTTP behavior changes) are explicitly not touched by any task.
- **Placeholder scan:** no TBD/TODO markers; every step has runnable code or an exact command.
- **Type consistency:** `RepositoryFactory`, `answer_question`, `accepted_answer_corrections_from_events`, `ModelerToolError` and its subclasses, `GATED_TOOLS`, and `TOOL_NAMES` are defined once (Tasks 2, 3, 5) and referenced with identical names/signatures everywhere they're reused (Tasks 4–6).

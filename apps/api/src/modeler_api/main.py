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

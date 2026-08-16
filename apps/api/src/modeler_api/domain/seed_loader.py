from pathlib import Path

from modeler_api.domain.models import KnowledgeGraph


def load_seed_graph(path: Path) -> KnowledgeGraph:
    return KnowledgeGraph.model_validate_json(path.read_text(encoding="utf-8"))

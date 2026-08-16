def create_research_candidate(title: str, url: str, topic: str) -> dict:
    return {
        "title": title,
        "url": url,
        "topic": topic,
        "review_status": "candidate",
        "trusted_rule": False,
        "promotion_required": True,
    }

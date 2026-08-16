from dataclasses import dataclass, field
from typing import Any

@dataclass
class QueryAnalysis:
    original_query: str
    normalized_query: str
    intent: str = "informational"
    entity_type: str = "general"
    entity_name: str = ""
    needs_web: bool = True
    needs_youtube: bool = False
    exact_text_request: bool = False
    search_queries: list[str] = field(default_factory=list)

@dataclass
class Evidence:
    title: str
    url: str
    content: str
    source_type: str
    score: float = 0.0
    trust_status: str = "external"
    provider: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_source_dict(self) -> dict:
        result = {
            "title": self.title,
            "url": self.url,
            "source_type": self.source_type,
            "trust_status": self.trust_status,
            "provider": self.provider,
            "score": float(self.score),
        }
        if "similarity" in self.metadata:
            result["similarity"] = float(self.metadata["similarity"])
        if "thumbnail" in self.metadata:
            result["thumbnail"] = self.metadata["thumbnail"]
        if "channel_title" in self.metadata:
            result["channel_title"] = self.metadata["channel_title"]
        return result

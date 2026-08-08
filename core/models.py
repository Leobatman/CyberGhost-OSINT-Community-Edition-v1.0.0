import json
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class OsintResult:
    source: str
    category: str
    target: str
    status: str
    data: Any
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "category": self.category,
            "target": self.target,
            "status": self.status,
            "data": self.data,
            "errors": self.errors,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

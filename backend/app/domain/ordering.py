from collections import Counter
from typing import TypeVar

from app.domain.errors import InvalidReorderError

T = TypeVar("T", bound=object)


def validate_reorder(existing: list[str], requested: list[str]) -> None:
    if len(requested) != len(existing) or Counter(requested) != Counter(existing):
        raise InvalidReorderError("Reorder must include each current symbol exactly once.")

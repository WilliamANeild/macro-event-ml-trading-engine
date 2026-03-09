from __future__ import annotations

from .base import BaseExpert
from .mock_expert import MockExpert


def get_experts() -> list[BaseExpert]:
    return [MockExpert()]
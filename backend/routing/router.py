# backend/routing/router.py
"""
SatQuery AI — Query-Driven Routing Module (Convenience / Canonical Package)
Section 7: Separate, testable routing module.
"""

from backend.router.router import (
    SatQueryRouter,
    RoutingConfiguration,
    TaskCategory,
    ModelInvocationTrace
)
from backend.router.routing_engine import RoutingEngine
from backend.router.schemas import RoutingDecision, TaskType, InputType, ModalityType

__all__ = [
    "SatQueryRouter",
    "RoutingConfiguration",
    "TaskCategory",
    "ModelInvocationTrace",
    "RoutingEngine",
    "RoutingDecision",
    "TaskType",
    "InputType",
    "ModalityType"
]


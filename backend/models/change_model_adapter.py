# backend/models/change_model_adapter.py
"""
Backwards-compatible wrapper aliasing ChangeStarAdapter.
Maintains compatibility with existing tests and imports.
"""
from backend.models.changestar_adapter import ChangeStarAdapter

class ChangeModelAdapter(ChangeStarAdapter):
    """
    Backwards-compatible alias for ChangeStarAdapter.
    """
    pass

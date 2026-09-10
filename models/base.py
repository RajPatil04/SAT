"""
Base model abstraction for SatQuery AI specialist models.
Provides extensible interface for GeoChat, ChangeStar, and CROMA.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class AnalysisResult(BaseModel):
    task: str
    model: str
    input_type: str
    modality: str
    filename: str
    format: str
    dimensions: str
    bands: str
    acquisition_date: Optional[str] = None
    status: str
    answer: str
    confidence: float
    confidence_level: str
    detected_land_cover: List[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    execution_trace: List[Dict[str, Any]]

class SpecialistModel(ABC):
    """Abstract Base Class for all remote sensing specialist models."""
    
    def __init__(self, name: str, modality: str, supported_tasks: List[str]):
        self.name = name
        self.modality = modality
        self.supported_tasks = supported_tasks

    @abstractmethod
    def predict(self, input_metadata: Dict[str, Any], query: str) -> AnalysisResult:
        """Execute inference on satellite imagery inputs."""
        pass

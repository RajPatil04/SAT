# backend/router/schemas.py
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class TaskType(str, Enum):
    VQA = "VQA"
    CAPTIONING = "CAPTIONING"
    GROUNDING = "GROUNDING"
    OBJECT_ANALYSIS = "OBJECT_ANALYSIS"
    SCENE_ANALYSIS = "SCENE_ANALYSIS"
    CHANGE_DETECTION = "CHANGE_DETECTION"
    CHANGE_VQA = "CHANGE_VQA"
    OPTICAL_SAR_ANALYSIS = "OPTICAL_SAR_ANALYSIS"
    MULTI_TEMPORAL_ANALYSIS = "MULTI_TEMPORAL_ANALYSIS"
    UNKNOWN = "UNKNOWN"

class InputType(str, Enum):
    SINGLE_IMAGE = "SINGLE_IMAGE"
    BI_TEMPORAL = "BI_TEMPORAL"
    MULTI_TEMPORAL = "MULTI_TEMPORAL"
    OPTICAL_SAR_PAIR = "OPTICAL_SAR_PAIR"
    MULTIMODAL_MULTI_IMAGE = "MULTIMODAL_MULTI_IMAGE"
    UNKNOWN = "UNKNOWN"

class ModalityType(str, Enum):
    OPTICAL = "OPTICAL"
    MULTISPECTRAL = "MULTISPECTRAL"
    SAR = "SAR"
    OPTICAL_SAR = "OPTICAL_SAR"
    UNKNOWN = "UNKNOWN"

class ModelStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    MOCK = "MOCK"
    ERROR = "ERROR"

class StructuredTaskSpecification(BaseModel):
    """
    Structured Task Specification produced during Query Interpretation (Paper Section III-C & IV-A).
    Transforms natural-language intent into an explicit remote-sensing task specification.
    """
    task: str = "visual_question_answering"
    target: Optional[str] = None
    required_observations: int = 1
    expected_modality: ModalityType = ModalityType.OPTICAL
    temporal_comparison: bool = False
    requires_spatial_evidence: bool = False
    requires_area_measurement: bool = False
    requires_cross_modal_fusion: bool = False
    is_ambiguous: bool = False
    ambiguity_reason: Optional[str] = None

class ImageMetadata(BaseModel):
    filename: str
    format: str
    width: int
    height: int
    channels: int
    datatype: str
    is_geotiff: bool = False
    crs: Optional[str] = None
    bounds: Optional[List[float]] = None
    resolution: Optional[List[float]] = None
    detected_modality: ModalityType = ModalityType.UNKNOWN
    acquisition_date: Optional[str] = None
    file_size_bytes: int = 0
    preview_url: Optional[str] = None

class SpatialCompatibility(BaseModel):
    dimension_match: bool
    crs_match: Optional[bool] = None
    resolution_ratio: Optional[float] = None
    extent_overlap: Optional[bool] = None
    is_compatible: bool
    details: str

class TemporalCompatibility(BaseModel):
    has_distinct_dates: bool
    date_1: Optional[str] = None
    date_2: Optional[str] = None
    is_compatible: bool
    details: str

class ImageValidationItem(BaseModel):
    filename: str
    format: str
    width: int
    height: int
    channels: int
    file_size_bytes: int
    is_valid: bool
    detected_modality: ModalityType = ModalityType.UNKNOWN
    variance: Optional[float] = None
    error: Optional[str] = None

class ValidationResult(BaseModel):
    is_valid: bool
    input_mode: str
    relationship: Optional[str] = None
    images: List[ImageValidationItem] = []
    warnings: List[str] = []
    blocking_errors: List[str] = []
    validation_messages: List[str] = []
    spatial_aligned: Optional[bool] = None
    modality_compatible: Optional[bool] = None

class CompatibilityResult(BaseModel):
    is_compatible: bool
    input_type: InputType
    modality: ModalityType
    spatial: Optional[SpatialCompatibility] = None
    temporal: Optional[TemporalCompatibility] = None
    validation_messages: List[str] = []
    blocking_errors: List[str] = []
    validation_details: Optional[ValidationResult] = None

class ExecutionStep(BaseModel):
    step: int
    component: str
    status: str  # "completed", "in_progress", "failed", "skipped"
    duration_ms: float
    message: str
    details: Optional[Dict[str, Any]] = None

class ModelCandidateScore(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    display_name: str
    total_score: float
    task_match_score: float
    input_type_match_score: float
    modality_match_score: float
    capability_match_score: float
    compatibility_score: float
    availability_score: float
    availability_status: ModelStatus
    status_message: str
    # Paper Equation 9 & Hard Constraints: S(w_i|q,x) = alpha*I + beta*C_f + gamma*M - lambda*P
    intent_score: Optional[float] = None
    input_compatibility: Optional[float] = None
    modality_score: Optional[float] = None
    penalty: Optional[float] = None
    is_feasible: bool = True  # C(w, x) in {0, 1}

class RoutingDecision(BaseModel):
    selected_model_id: Optional[str] = None
    selected_model_name: Optional[str] = None
    detected_task: TaskType
    detected_input_type: InputType
    detected_modality: ModalityType
    task_confidence: Optional[float] = None
    reasons: List[str] = []
    candidate_scores: List[ModelCandidateScore] = []
    execution_plan: List[str] = []
    is_executable: bool = True
    blocking_issue: Optional[str] = None
    structured_task_spec: Optional[StructuredTaskSpecification] = None

class BoundingBox(BaseModel):
    box_2d: List[float] = Field(..., description="[ymin, xmin, ymax, xmax] coordinates normalized 0-1 or pixel coordinates")
    label: str
    confidence: Optional[float] = None

class SpatialQuadrantStats(BaseModel):
    name: str
    changed_pixels: int
    total_pixels: int
    quadrant_change_percentage: float
    percentage_of_total_change: float

class SpatialDistribution(BaseModel):
    total_changed_pixels: int
    total_pixels: int
    change_percentage: float
    quadrants: List[SpatialQuadrantStats] = []
    bounding_box: Optional[List[float]] = None
    bounding_box_pixels: Optional[List[int]] = None
    centroid: Optional[List[float]] = None
    centroid_pixels: Optional[List[float]] = None
    dominant_quadrant: Optional[str] = None
    summary: str = ""

class DownstreamFindings(BaseModel):
    task: str
    model_name: str
    semantic_classification_available: bool = False
    spatial_distribution: Optional[SpatialDistribution] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    findings_summary: str = ""

class Evidence(BaseModel):
    text: Optional[str] = None
    regions: List[Dict[str, Any]] = []
    boxes: List[BoundingBox] = []
    overlay_url: Optional[str] = None
    change_mask_url: Optional[str] = None
    change_percentage: Optional[float] = None
    changed_pixels: Optional[int] = None
    total_pixels: Optional[int] = None
    optical_feature_summary: Optional[str] = None
    sar_feature_summary: Optional[str] = None
    raw_model_metrics: Optional[Dict[str, Any]] = None
    spatial_distribution: Optional[SpatialDistribution] = None
    downstream_findings: Optional[DownstreamFindings] = None

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    request_id: str
    query: str
    task: TaskType
    input_type: InputType
    modality: ModalityType
    status: str  # "success", "unavailable", "rejected_incompatible", "error"
    answer: str
    models_used: List[str] = []
    evidence: Evidence
    confidence: Optional[float] = None
    router_confidence: Optional[float] = None
    model_confidence: Optional[float] = None
    system_confidence: Optional[float] = None
    routing: RoutingDecision
    metadata: List[ImageMetadata] = []
    compatibility: CompatibilityResult
    execution_trace: List[ExecutionStep] = []
    task_type: Optional[str] = None
    selected_models: List[str] = []
    limitations: List[str] = []
    validation: Optional[ValidationResult] = None
    structured_task_spec: Optional[StructuredTaskSpecification] = None
    timings: Dict[str, float] = {}
    routing_config: Optional[str] = None
    total_duration_ms: float
    timestamp: str

class ModelInfoResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: str
    display_name: str
    version: str
    description: str
    tasks: List[TaskType]
    input_types: List[InputType]
    modalities: List[ModalityType]
    status: ModelStatus
    status_message: str
    endpoint_type: str
    endpoint_configured: bool
    supports_visual_grounding: bool
    supports_change_maps: bool
    supports_cross_attention_fusion: bool
    license: str
    paper_reference: str

class SystemStatusResponse(BaseModel):
    app_name: str
    environment: str
    status: str
    fastapi: str
    router: str
    models: Dict[str, str]
    database: str
    experiment_logger: str
    active_experiments_count: int

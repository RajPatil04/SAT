// frontend/src/types/api.ts

export type TaskType =
  | 'VQA'
  | 'CAPTIONING'
  | 'GROUNDING'
  | 'OBJECT_ANALYSIS'
  | 'SCENE_ANALYSIS'
  | 'CHANGE_DETECTION'
  | 'CHANGE_VQA'
  | 'OPTICAL_SAR_ANALYSIS'
  | 'MULTI_TEMPORAL_ANALYSIS'
  | 'UNKNOWN';

export type InputType =
  | 'SINGLE_IMAGE'
  | 'BI_TEMPORAL'
  | 'MULTI_TEMPORAL'
  | 'OPTICAL_SAR_PAIR'
  | 'MULTIMODAL_MULTI_IMAGE'
  | 'UNKNOWN';

export type ModalityType =
  | 'OPTICAL'
  | 'MULTISPECTRAL'
  | 'SAR'
  | 'OPTICAL_SAR'
  | 'UNKNOWN';

export type ModelStatus =
  | 'AVAILABLE'
  | 'UNAVAILABLE'
  | 'NOT_CONFIGURED'
  | 'MOCK'
  | 'ERROR';

export interface ImageMetadata {
  filename: string;
  format: string;
  width: number;
  height: number;
  channels: number;
  datatype: string;
  is_geotiff: boolean;
  crs?: string | null;
  bounds?: number[] | null;
  resolution?: number[] | null;
  detected_modality: ModalityType;
  acquisition_date?: string | null;
  file_size_bytes: number;
  preview_url?: string | null;
}

export interface SpatialCompatibility {
  dimension_match: boolean;
  crs_match?: boolean | null;
  resolution_ratio?: number | null;
  extent_overlap?: boolean | null;
  is_compatible: boolean;
  details: string;
}

export interface TemporalCompatibility {
  has_distinct_dates: boolean;
  date_1?: string | null;
  date_2?: string | null;
  is_compatible: boolean;
  details: string;
}

export interface ImageValidationItem {
  filename: string;
  format: string;
  width: number;
  height: number;
  channels: number;
  file_size_bytes: number;
  is_valid: boolean;
  detected_modality: ModalityType;
  variance?: number | null;
  error?: string | null;
}

export interface ValidationResult {
  is_valid: boolean;
  input_mode: string;
  relationship?: string | null;
  images: ImageValidationItem[];
  warnings: string[];
  blocking_errors: string[];
  validation_messages: string[];
  spatial_aligned?: boolean | null;
  modality_compatible?: boolean | null;
}

export interface CompatibilityResult {
  is_compatible: boolean;
  input_type: InputType;
  modality: ModalityType;
  spatial?: SpatialCompatibility | null;
  temporal?: TemporalCompatibility | null;
  validation_messages: string[];
  blocking_errors: string[];
  validation_details?: ValidationResult | null;
}

export interface ExecutionStep {
  step: number;
  component: string;
  status: 'completed' | 'in_progress' | 'failed' | 'skipped';
  duration_ms: number;
  message: string;
  details?: Record<string, any> | null;
}

export interface StructuredTaskSpecification {
  task: string;
  target?: string | null;
  required_observations: number;
  expected_modality: ModalityType;
  temporal_comparison: boolean;
  requires_spatial_evidence: boolean;
  requires_area_measurement: boolean;
  requires_cross_modal_fusion: boolean;
  is_ambiguous: boolean;
  ambiguity_reason?: string | null;
}

export interface ModelCandidateScore {
  model_id: string;
  display_name: string;
  total_score: number;
  task_match_score: number;
  input_type_match_score: number;
  modality_match_score: number;
  capability_match_score: number;
  compatibility_score: number;
  availability_score: number;
  availability_status: ModelStatus;
  status_message: string;
  intent_score?: number | null;
  input_compatibility?: number | null;
  modality_score?: number | null;
  penalty?: number | null;
  is_feasible?: boolean;
}

export interface RoutingDecision {
  selected_model_id?: string | null;
  selected_model_name?: string | null;
  detected_task: TaskType;
  detected_input_type: InputType;
  detected_modality: ModalityType;
  task_confidence?: number | null;
  reasons: string[];
  candidate_scores: ModelCandidateScore[];
  execution_plan: string[];
  is_executable: boolean;
  blocking_issue?: string | null;
  structured_task_spec?: StructuredTaskSpecification | null;
}

export interface BoundingBox {
  box_2d: number[]; // [ymin, xmin, ymax, xmax]
  label: string;
  confidence?: number | null;
}

export interface SpatialQuadrantStats {
  name: string;
  changed_pixels: number;
  total_pixels: number;
  quadrant_change_percentage: number;
  percentage_of_total_change: number;
}

export interface SpatialDistribution {
  total_changed_pixels: number;
  total_pixels: number;
  change_percentage: number;
  quadrants: SpatialQuadrantStats[];
  bounding_box?: number[] | null;
  bounding_box_pixels?: number[] | null;
  centroid?: number[] | null;
  centroid_pixels?: number[] | null;
  dominant_quadrant?: string | null;
  summary: string;
}

export interface DownstreamFindings {
  task: string;
  model_name: string;
  semantic_classification_available: boolean;
  spatial_distribution?: SpatialDistribution | null;
  metrics: Record<string, any>;
  findings_summary: string;
}

export interface Evidence {
  text?: string | null;
  regions: Array<Record<string, any>>;
  boxes: BoundingBox[];
  overlay_url?: string | null;
  change_mask_url?: string | null;
  change_percentage?: number | null;
  changed_pixels?: number | null;
  total_pixels?: number | null;
  optical_feature_summary?: string | null;
  sar_feature_summary?: string | null;
  raw_model_metrics?: Record<string, any> | null;
  spatial_distribution?: SpatialDistribution | null;
  downstream_findings?: DownstreamFindings | null;
}

export interface AnalysisResponse {
  request_id: string;
  query: string;
  task: TaskType;
  input_type: InputType;
  modality: ModalityType;
  status: 'success' | 'unavailable' | 'rejected_incompatible' | 'error';
  answer: string;
  models_used: string[];
  evidence: Evidence;
  confidence?: number | null;
  router_confidence?: number | null;
  model_confidence?: number | null;
  system_confidence?: number | null;
  routing: RoutingDecision;
  metadata: ImageMetadata[];
  compatibility: CompatibilityResult;
  execution_trace: ExecutionStep[];
  task_type?: string;
  selected_models?: string[];
  limitations?: string[];
  validation?: ValidationResult | null;
  structured_task_spec?: StructuredTaskSpecification | null;
  timings?: Record<string, number>;
  routing_config?: string;
  total_duration_ms: number;
  timestamp: string;
}

export interface ModelInfoResponse {
  model_id: string;
  display_name: string;
  version: string;
  description: string;
  tasks: TaskType[];
  input_types: InputType[];
  modalities: ModalityType[];
  status: ModelStatus;
  status_message: string;
  endpoint_type: string;
  endpoint_configured: boolean;
  supports_visual_grounding: boolean;
  supports_change_maps: boolean;
  supports_cross_attention_fusion: boolean;
  license: string;
  paper_reference: string;
}

export interface SystemStatusResponse {
  app_name: string;
  environment: string;
  status: string;
  fastapi: string;
  router: string;
  models: Record<string, string>;
  database: string;
  experiment_logger: string;
  active_experiments_count: number;
}

export interface ExperimentSummary {
  id: number;
  request_id: string;
  timestamp: string;
  query: string;
  input_type: string;
  modality: string;
  detected_task: string;
  selected_model: string | null;
  total_latency_ms: number;
  model_latency_ms: number;
  routing_latency_ms: number;
  status: string;
  success: boolean;
  answer: string | null;
  confidence: number | null;
}

export interface SystemMetrics {
  total_experiments: number;
  success_rate: number;
  avg_total_latency_ms: number;
  avg_routing_latency_ms: number;
  avg_model_latency_ms: number;
  task_distribution: Record<string, number>;
  model_usage_distribution: Record<string, number>;
}

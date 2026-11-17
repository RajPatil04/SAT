# Research Methodology

## 1. Problem Definition & Motivation
Earth observation (EO) datasets are inherently heterogeneous, spanning diverse sensor modalities (panchromatic, multispectral optical, synthetic aperture radar (SAR), thermal) and temporal observations (single-epoch, bi-temporal, multi-temporal sequences). Existing remote-sensing AI architectures predominantly focus on narrow, single-task silos (e.g. isolated VQA models, task-specific change detection networks, or standalone optical-SAR registration algorithms).

Consequently, non-expert practitioners are forced to possess specialized knowledge to determine which model is appropriate for their analytical query.

The **proposed SatQuery AI framework** addresses this fragmentation by introducing a modular, research-oriented agentic vision-language system that unifies query understanding, raster validation, spatiotemporal compatibility checking, and deterministic model routing.

## 2. Research Prototype Architecture
The proposed architecture comprises six decoupled stages:
1. **Input Validation Layer**: Validates file integrity across standard and geospatial formats (GeoTIFF, TIFF, PNG, JPEG) without discarding unreferenced rasters.
2. **Metadata & Compatibility Engine**: Extracts spatial grid dimensions, channel counts, CRS projections, resolution ratios, and temporal timestamps. Evaluates whether image pairs are spatiotemporally compatible.
3. **Query Understanding & Task Classification**: Analyzes semantic tokens to infer intent across nine remote-sensing task classes (`VQA`, `CAPTIONING`, `GROUNDING`, `OBJECT_ANALYSIS`, `SCENE_ANALYSIS`, `CHANGE_DETECTION`, `CHANGE_VQA`, `OPTICAL_SAR_ANALYSIS`, `MULTI_TEMPORAL_ANALYSIS`).
4. **Intelligent Routing Formulation**: Scores registered specialist models against the proposed weighted formulation:
   $$\text{Score}(q, m) = \sum_{i=1}^6 w_i \cdot \text{Metric}_i$$
5. **Specialist Execution & Orchestration**: Executes the selected foundation specialist (e.g., GeoChat-7B, ChangeStar, CROMA) via standard adapters without coupling frontend to remote hosting URLs.
6. **Evidence Fusion & Response Normalization**: Unifies heterogeneous model outputs into an empirical response containing textual descriptions, quantified regional modifications, bounding coordinates, and deterministic execution trace telemetry.

## 3. Evaluation Protocol
The research prototype is evaluated across:
- **Task Classification Accuracy**: Ratio of correctly identified task families against query intents.
- **Routing Decision Accuracy**: Precision of selecting appropriate specialist models.
- **Invariance / Rejection Consistency**: Verification that inconsistent queries (e.g. bi-temporal queries with only one input) are rejected with domain-grounded explanations.
- **Computational Overhead**: Routing engine execution latency (target: $< 5$ ms).

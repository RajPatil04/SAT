# SatQuery AI: API Specification

## Base Endpoints

### 1. Health & Diagnostics
- `GET /api/health`: Returns system status and environment.
- `GET /api/system-status`: Detailed diagnostics for FastAPI, Router, Database, Experiment Logger, and individual specialist models.

### 2. Model Registry
- `GET /api/models`: Returns list of all registered foundation specialists with capabilities and operational status.
- `GET /api/models/{model_id}`: Returns metadata for a specific model ID.
- `GET /api/models/capabilities`: Returns supported tasks, input structures, modalities, and routing parameters.

### 3. Analysis Pipeline
- `POST /api/analyze`: Primary multimodal entrypoint.
  - **Content-Type**: `multipart/form-data`
  - **Form Fields**:
    - `images` (List[UploadFile], required)
    - `question` (str, required)
    - `input_type` (str, optional)
    - `modality` (str, optional)
    - `date_1` (str, optional)
    - `date_2` (str, optional)
  - **Returns**: `AnalysisResponse`
- `POST /api/analyze/single`: Single-image shortcut.
- `POST /api/analyze/change`: Bi-temporal change shortcut.
- `POST /api/analyze/optical-sar`: Optical-SAR multimodal shortcut.
- `POST /api/validate`: Performs format, spatial, and temporal validation without executing inference.

### 4. Research Telemetry & Reporting
- `GET /api/report/{request_id}?format=html|pdf`: Generates downloadable research reports.
- `GET /api/experiments`: Lists historical experiment trials.
- `GET /api/experiments/{request_id}`: Returns trace and telemetry for a specific execution.
- `GET /api/experiments/metrics/summary`: Aggregate metrics.
- `POST /api/experiments/evaluate-benchmark`: Runs automated benchmark suite.

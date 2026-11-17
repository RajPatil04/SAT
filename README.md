# SATQUERY AI — Agentic Remote-Sensing Intelligence Platform

> **Query-Driven Routing of Specialist Remote-Sensing Models with Input Validation, Evidence-Grounded Answers, and Selective Cross-Model Reasoning**

[![Python Tests](https://img.shields.io/badge/pytest-63%20passed-brightgreen.svg)](file:///c:/Users/rajnp/Desktop/SAT/backend/tests)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-blue.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178c6.svg)](https://www.typescriptlang.org)
[![Vite](https://img.shields.io/badge/Vite-5.4-646cff.svg)](https://vitejs.dev)

---

## 🎯 Authoritative Endpoint Configuration

All specialist model endpoints, API keys, and connection parameters are centrally and authoritatively configured in:

📁 **`backend/config/model_endpoints.yaml`**

To connect a remote or local GeoChat-7B instance (e.g., HuggingFace Space, RunPod, or local Gradio service), you only need to edit **this single file**:

```yaml
services:
  geochat-7b:
    enabled: true
    base_url: "https://your-geochat-instance.hf.space"  # Or http://127.0.0.1:7860
    api_type: "gradio"                                  # Or "rest"
    analyze_path: "predict"
    timeout_seconds: 120
    api_key_env_var: "GEOCHAT_API_KEY"
```

No Python files, `.env` files, routing components, or React frontend code need to be modified. When the backend starts up, `CentralConfigManager` verifies endpoint format, validates network reachability, and logs status to the console.

---

## 🛰️ 1. Project Overview & Research Motivation

Existing remote-sensing AI architectures are predominantly siloed into narrow single-task models:
- **General Vision-Language Models (VLMs)** cannot reliably detect pixel-level bi-temporal surface changes or ingest radar data.
- **Change detection networks** produce binary difference masks but lack natural-language question-answering capabilities.
- **Optical–SAR cross-modal models** produce multi-sensor feature embeddings but do not generate text or perform high-level conversational reasoning.

**SatQuery AI** is an agentic platform designed to answer the core remote-sensing research hypothesis:
> *Can natural-language questions, pre-flight data compatibility checks, and query-driven routing of specialist models outperform fixed single-model pipelines while enabling selective cross-model reasoning without hallucinating unverified facts?*

The system provides:
1. **Strictly Two Primary Input Modes in the UI**: **Single Image** and **Double Image** (with a contextual relationship selector).
2. **Dedicated Pre-Flight Input Validation**: Validates image decodability, spatial dimensions, channel counts, pixel alignment, and authentic radar properties before executing inference.
3. **Query-Driven Routing Algorithm (`router.py`)**: Evaluates user queries and image inputs across 3 comparative research configurations (`CONFIG_A`, `CONFIG_B`, `CONFIG_C`).
4. **Specialist Model Adapters**:
   - **GeoChat-7B**: Remote-sensing VLM for scene description, land-cover identification, and visual question answering.
   - **ChangeStar**: Siamese FarSeg ResNet-18 (LEVIR-CD pretrained) for dense bi-temporal change detection and change maps.
   - **CROMA**: Cross-Modality Autoencoder (ViT-Base) for optical–SAR 768-d joint embeddings and cross-sensor similarity metrics.
5. **Selective Cross-Model Reasoning**: Combines ChangeStar change masks with GeoChat region-level description only when technically justified, maintaining full execution transparency.
6. **Evidence-Grounded Answers**: Returns natural-language answers, visual evidence maps, selected model telemetry, per-stage timings, and explicit scientific limitations.

---

## 🏛️ 2. System Architecture

```
                                  USER / RESEARCHER
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │    React Frontend (Mission Control)   │
                      │  Mode A: Single Image │ Mode B: Double│
                      └───────────────────┬───────────────────┘
                                          │ POST /validate | POST /analyze
                                          ▼
                      ┌───────────────────────────────────────┐
                      │       FastAPI Gateway (Port 8000)     │
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │      Dedicated Input Validation       │
                      │ (Decodability, Alignment, SAR checks) │
                      └───────────────────┬───────────────────┘
                                          │
                                          ▼
                      ┌───────────────────────────────────────┐
                      │      SatQuery Intelligent Router      │
                      │  Config A: Fixed Mode Routing         │
                      │  Config B: Query-Driven Routing       │
                      │  Config C: Query-Driven + Cross-Model │
                      └───────────────────┬───────────────────┘
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 ▼                        ▼                        ▼
       ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
       │   GeoChat-7B     │     │    ChangeStar    │     │      CROMA       │
       │  VLM Specialist  │     │Change Specialist │     │Optical-SAR Cross │
       │ (Scene/VQA/Desc) │     │ (LEVIR-CD Mask)  │     │(768d Joint Embed)│
       └─────────┬────────┘     └────────┬─────────┘     └────────┬─────────┘
                 │                       │                        │
                 │                       ▼ (Change Mask)          │
                 │           ┌───────────────────────┐            │
                 └──────────►│  Selective Cross-     │◄───────────┘
                             │  Model Reasoner       │
                             └───────────┬───────────┘
                                         │
                                         ▼
                      ┌───────────────────────────────────────┐
                      │    Evidence Normalizer & Synthesizer  │
                      │  (Answer, Overlays, Trace, Timings)   │
                      └───────────────────┬───────────────────┘
                                         │ Structured JSON Response
                                         ▼
                      ┌───────────────────────────────────────┐
                      │     Evidence-Grounded UI Display      │
                      └───────────────────────────────────────┘
```

---

## 🖥️ 3. User Interface: Exactly Two Primary Input Modes

The Mission Control React UI is organized around **two primary input tabs**:

### Mode A: Single Image
- Upload one satellite or aerial image (`PNG`, `JPG`, `JPEG`, `TIFF`, `GeoTIFF`).
- Instant high-resolution preview with file format and dimensions.
- Natural-language query input with pre-populated example questions:
  - *"What objects and land-cover types are visible?"*
  - *"Describe the important features in this image."*
  - *"Identify visible roads, buildings, vegetation, and water bodies."*
  - *"Summarize the scene."*

### Mode B: Double Image
- Upload two remote-sensing images with side-by-side previews.
- **Contextual Relationship Selector**:
  - `BI_TEMPORAL`: Before-and-after / multi-temporal acquisition pair.
  - `OPTICAL_SAR`: Joint optical and synthetic aperture radar (SAR) pair.
  - `UNKNOWN`: Unspecified or exploratory image relationship.
- Natural-language query input with example questions:
  - *"What changes occurred between these two images?"*
  - *"Where have new buildings appeared?"*
  - *"Has vegetation or water coverage changed?"*
  - *"Compare the structural information visible in these images."*
  - *"What differences can be supported by the available evidence?"*

---

## 🛡️ 4. Dedicated Pre-Flight Input Validation

Before executing expensive neural models, the backend validation layer (`InputValidator`) verifies:
1. **File Count & Mode Conformity**: Single Image requires exactly 1 file; Double Image requires exactly 2 files.
2. **Decodability & Header Validation**: Validates image headers (PNG/JPEG via Pillow, GeoTIFF via Rasterio/Pillow, NumPy `.npy`/`.npz`).
3. **Spatial Dimension & Channel Integrity**: Extracts width, height, and band count ($C=1, 3, 4, 12$).
4. **Bi-Temporal Spatial Alignment**:
   - Checks dimensions ($W_1 = W_2$, $H_1 = H_2$) and Ground Sampling Distance (GSD).
   - If dimensions differ, returns a clear warning flag so unaligned rasters are not falsely interpreted as physical ground change.
5. **Optical–SAR Modality Verification**:
   - Inspects Sentinel-1 radar backscatter characteristics ($VV/VH$ channels, dB distributions).
   - Refuses to treat standard dual-RGB photographs as valid optical–SAR pairs.
6. **Transparent Validation Feedback**: Accessible immediately via `POST /validate` and displayed in the UI prior to submission.

---

## 🧠 5. Query-Driven Routing & Research Configurations

The routing module (`backend/router/router.py`) maps user input and questions to the optimal specialist model. It supports 3 distinct research configurations:

### Configuration A — Fixed Routing
- Routes purely based on the active input mode and user-declared relationship:
  - Single Image $\rightarrow$ GeoChat.
  - Double Image (Bi-temporal) $\rightarrow$ ChangeStar.
  - Double Image (Optical–SAR) $\rightarrow$ CROMA.
- Ignores question semantics.

### Configuration B — Query-Driven Routing (Recommended)
- Interprets question semantics (`task_classifier.py`), input mode, image relationship, validation results, and model capabilities.
- Prevents misrouting (e.g. asking a change question on a single image is rejected with an informative explanation rather than invoking an inappropriate model).
- Resolves ambiguous questions by surfacing clarifying assumptions in the response.

### Configuration C — Query-Driven Routing with Selective Cross-Model Reasoning
- Executes primary query-driven routing.
- When technically justified (e.g. ChangeStar produces a change map and the user asks a natural-language question explaining the difference), selectively invokes GeoChat on the affected regions.
- Transparently attributes each model's contribution and discloses any conflicting evidence.

---

## 🔬 6. Specialist Models & Hardware Constraints

### Hardware Target & Execution Strategy
The primary development machine is a Windows PC with:
- **System RAM**: 16 GB
- **GPU**: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM)
- **Disk Storage**: 512 GB NVMe SSD

### Model Capabilities & Deployment Matrix

| Model | Pretrained Weights | Memory Footprint | Runtime Strategy | Output Modality |
|---|---|---|---|---|
| **ChangeStar** (ResNet-18) | `pretrained_weights/changestar1x96_r18_ft_levircd.pth` (65.8 MB) | ~350 MB RAM | In-process PyTorch or microservice (`:8001`) | Binary change map, change pixel count, percentage |
| **CROMA** (ViT-Base) | `pretrained_weights/CROMA_base.pt` (777.6 MB) | ~1.6 GB RAM | In-process PyTorch or microservice (`:8002`) | 768-d joint optical-SAR embeddings, patch cosine similarity |
| **GeoChat-7B** (LLaVA-RS) | Remote checkpoint (7B parameters) | Requires $\ge 14$ GB VRAM (FP16) or $\ge 6$ GB (INT4) | Configurable microservice (`:8000`) or offline simulation fallback | Natural language scene descriptions, VQA answers |

> **Scientific Disclosure Regarding GeoChat**: Because GeoChat-7B requires at least 6 GB VRAM in 4-bit quantization, running it locally exceeds the RTX 3050 Laptop's 4 GB VRAM limit. SatQuery AI provides an explicit integration boundary: when an external GeoChat microservice is not configured, the system reports `NOT_CONFIGURED` status and returns an honest, transparent notice without fabricating live model output. Once configured in `model_endpoints.yaml`, real Gradio/REST inference is dispatched.

> **Scientific Disclosure Regarding CROMA**: CROMA is an encoder-only representation model that outputs 768-dimensional multimodal feature embeddings. SatQuery AI computes cross-sensor cosine similarities and never fabricates natural-language text for CROMA.

---

## 🚀 7. Quickstart Guide

### Prerequisites
- Python 3.10+ (tested on Python 3.12.5)
- Node.js 18+ and npm
- PyTorch 2.0+ (CPU or CUDA)

### 7.1 One-Click Windows Launch (Recommended)
You can start all 4 services (ChangeStar microservice, CROMA service, FastAPI gateway, and React frontend) using either:
```cmd
start_satquery.bat
```
or in PowerShell:
```powershell
.\start_satquery.ps1
```

### 7.2 Manual Multi-Service Startup
```bash
# Terminal 1: ChangeStar microservice
python -m uvicorn model_services.changestar_server:app --host 127.0.0.1 --port 8001

# Terminal 2: CROMA microservice
python -m uvicorn model_services.croma_server:app --host 127.0.0.1 --port 8002

# Terminal 3: FastAPI Gateway
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Terminal 4: React UI
cd frontend && npm run dev
```

- Mission Control UI: `http://localhost:3000`
- Interactive API Docs: `http://localhost:8000/docs`

### 7.3 Testing Suite
Run the comprehensive 63-test backend verification suite:
```bash
python -m pytest backend/tests -v
```

---

## 📡 8. API Specification

| Method | Endpoint | Description | Request Payload | Response |
|---|---|---|---|---|
| `GET` | `/health` or `/api/health` | Health and environment readiness | None | `{"status": "online", "environment": "development", "version": "1.0.0"}` |
| `GET` | `/api/models` | Live status of GeoChat, ChangeStar, CROMA, and Grounding | None | Array of `ModelInfoResponse` objects |
| `POST` | `/api/validate` | Pre-flight validation without inference | `multipart/form-data`: `images`, `input_mode`, `relationship` | `ValidationResult` (decodability, spatial alignment, radar channels) |
| `POST` | `/api/analyze` | Unified multimodal analysis and routing pipeline | `multipart/form-data`: `images`, `question`, `input_mode`, `relationship`, `routing_config` | `AnalysisResponse` ($R = \{A, E, C_f, P\}$) |
| `GET` | `/api/experiments/table-ii` | Comparative evaluation across Table II routing configurations | None | Comparative evaluation metrics ($RA, IRR, ESR, EER, L_{mean}$) |
| `POST` | `/api/experiments/evaluate-benchmark` | Automated evaluation across benchmark scenarios | None | Task classification accuracy, routing accuracy, and case traces |

---

## 📊 9. Research Evaluation Protocol (Paper Section V)

To rigorously evaluate the core hypothesis (*Query-Driven Routing with Selective Reasoning vs Fixed Routing*), the framework implements the exact evaluation methodology from Section V of the paper `SAT.pdf`:

### 9.1 Five Quantitative Metrics (Section V-F):
1. **Routing Accuracy (RA, Eq. 11)**: $RA = \frac{N_{correct}}{N_{valid}} \times 100$
2. **Invalid-Input Rejection Rate (IRR, Eq. 12)**: $IRR = \frac{N_{rejected}}{N_{invalid}} \times 100$
3. **Execution Success Rate (ESR, Eq. 13)**: $ESR = \frac{N_{successful}}{N_{valid}} \times 100$
4. **End-to-End Reliability (EER, Eq. 14)**: $EER = \frac{N_{complete}}{N_{total}} \times 100$
5. **Mean Latency ($L_{mean}$, Eq. 15)**: $L_{mean} = \frac{1}{N} \sum_{i=1}^N L_i$

### 9.2 Table II Comparative Routing Configurations (Section V-G):
- **Query-only Router**: Evaluates natural language intent without checking image count or spatial/temporal compatibility.
- **Metadata-only Router**: Routes strictly using observation counts and metadata without query intent analysis.
- **Query + Input Router**: Uses query and input counts without deep compatibility validation.
- **SatQuery AI (Full Compatibility-Aware)**: Enforces hard compatibility constraints $C(w, x) \in \{0, 1\}$ before ranking candidates with Equation 9 ($S = \alpha I + \beta C_f + \gamma M - \lambda P$).

### 9.3 Six Failure Analysis Stages (Section V-H):
1. *Query-intent identification errors*
2. *Incorrect candidate generation*
3. *Compatibility-validation failures*
4. *Incorrect workflow routing selection*
5. *Specialist execution failures*
6. *Response-integration formatting failures*

---

## 🔒 10. Security & Privacy Assurance
- **Zero Model URL Exposure**: No third-party model URLs or private endpoints are embedded in client-side code (`.tsx`, `.ts`). All communication traverses the secure backend gateway.
- **Temporary File Lifecycle**: All uploaded rasters are processed in isolated temporary directories and automatically cleaned up upon request completion.

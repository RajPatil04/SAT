# SatQuery AI: System Architecture

## Overview
**SatQuery AI** is an agentic vision-language framework designed for query-driven multimodal remote-sensing analysis. Rather than deploying an isolated model that assumes a fixed task, SatQuery AI dynamically understands natural-language queries, inspects available raster assets (optical, multispectral, SAR), validates spatial and temporal compatibility, routes to specialist foundation models, and synthesizes evidence-grounded answers accompanied by deterministic execution traces.

```
                         USER / RESEARCHER
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │ React Frontend (Vite) │
                     └───────────┬───────────┘
                                 │ Images + Query
                                 ▼
                     ┌───────────────────────┐
                     │    FastAPI Gateway    │
                     └───────────┬───────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │   Input Validation Layer    │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │ Metadata & Compatibility    │
                  │ Engine (Spatial & Temporal) │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │  Query Semantic Analyzer &  │
                  │       Task Classifier       │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │ Intelligent Routing Engine  │
                  │  (Formulation Optimization) │
                  └──────────────┬──────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│    GeoChat-7B    │    │    ChangeStar    │    │      CROMA       │
│  VLM Specialist  │    │Change Specialist │    │Optical-SAR Cross │
└────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │ Evidence Fusion & Normalizer│
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │ Research Experiment Logger  │
                  │   & Report Synthesis Engine │
                  └──────────────┬──────────────┘
                                 │
                    Grounded Findings + Evidence
                    + Confidence + Execution Trace
                                 ▼
                     ┌───────────────────────┐
                     │ React Frontend (Vite) │
                     └───────────────────────┘
```

## Architectural Principles
1. **Modularity & Decoupling**: Frontend never interfaces directly with model hosting URLs. All model communications occur via isolated adapters (`backend/models/`).
2. **Scientific Honesty**: If a model does not compute numerical confidence, the system returns `null` ("Confidence not provided by model"). If an asset is simulated, it is explicitly flagged as `MOCK`.
3. **Domain Constraint Enforcement**: Inconsistent inputs (e.g. asking "what changed" with a single image) are rejected before execution with clear domain guidance.

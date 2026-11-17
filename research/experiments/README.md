# SatQuery AI Research Experiment Logs

This directory contains empirical trial logs, execution telemetry, and routing formulation analyses collected during model benchmark evaluations.

## Log Schema
Each recorded experiment logs:
- `request_id`: Unique identifier
- `timestamp`: UTC ISO timestamp
- `query`: User query text
- `detected_task`: Classified remote-sensing task
- `input_type`: SINGLE_IMAGE, BI_TEMPORAL, OPTICAL_SAR_PAIR, MULTI_TEMPORAL
- `modality`: OPTICAL, MULTISPECTRAL, SAR, OPTICAL_SAR
- `selected_model`: Target specialist model invoked
- `routing_reasons`: Structured decision explanations
- `routing_latency_ms`: Routing and planning overhead (ms)
- `model_latency_ms`: Remote specialist execution latency (ms)
- `total_latency_ms`: End-to-end response time (ms)
- `confidence`: Empirical model confidence (None if unavailable)

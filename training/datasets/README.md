# Remote-Sensing VLM Adaptation Datasets

This module provides dataset loaders and manifest specifications for adapting/fine-tuning specialist remote-sensing models (e.g., GeoChat LoRA adapters or CROMA cross-attention projections).

## Supported Open Benchmarks
1. **RSVQA**: Remote Sensing Visual Question Answering on Sentinel-2 and high-resolution optical imagery.
2. **VRSBench**: Visual question answering and referring expression visual grounding for earth observation.
3. **CDVQA**: Bi-temporal Change Detection Visual Question Answering.
4. **BigEarthNet-MM**: Multi-modal Sentinel-1 (SAR) and Sentinel-2 (Optical) benchmark.

## Manifest Format (JSON)
```json
[
  {
    "sample_id": "rsvqa_001",
    "image_paths": ["images/rsvqa_001.tif"],
    "query": "Is there a highway visible in this sector?",
    "target_answer": "yes",
    "grounding_bbox": null
  }
]
```

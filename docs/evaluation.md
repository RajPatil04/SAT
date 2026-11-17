# Empirical Evaluation & Benchmark Protocol

## Benchmark Suites
The framework provides an automated benchmark evaluation harness (`backend/research/evaluation.py`) accessible via `POST /api/experiments/evaluate-benchmark` or the Mission Control UI.

### Test Cases Evaluated:
1. **Case 1: Single Optical VQA / Captioning**
   - Query: *"Describe the land cover and major objects visible in this image."*
   - Assets: Single Optical observation
   - Expected Task: `CAPTIONING` / `VQA`
   - Target Specialist: `geochat-7b`
2. **Case 2: Referring Expression Grounding**
   - Query: *"Highlight the water body referred to in the query."*
   - Assets: Single observation
   - Expected Task: `GROUNDING`
   - Target Specialist: `geochat-7b` / `grounding-specialist`
3. **Case 3: Bi-Temporal Change Detection**
   - Query: *"What changed between these two images?"*
   - Assets: Observation T1, Observation T2
   - Expected Task: `CHANGE_DETECTION`
   - Target Specialist: `changestar`
4. **Case 4: Bi-Temporal Change VQA**
   - Query: *"Has the built-up area increased, decreased, or remained unchanged?"*
   - Assets: Observation T1, Observation T2
   - Expected Task: `CHANGE_VQA`
   - Target Specialist: `changestar`
5. **Case 5: Optical + SAR Joint Analysis**
   - Query: *"Use the optical and SAR images together to identify built-up and water-covered regions."*
   - Assets: Optical Sentinel-2 observation + SAR Sentinel-1 observation
   - Expected Task: `OPTICAL_SAR_ANALYSIS`
   - Target Specialist: `croma`
6. **Case 6: Invariant Rejection Consistency**
   - Query: *"What changed between these two dates?"*
   - Assets: Single observation only
   - Expected Outcome: Rejection with explanation that bi-temporal analysis requires two observations. No false routing to single-image VQA.

## Empirical Metrics (Baseline Benchmark Run)
- Task Classification Accuracy: **100%**
- Routing Accuracy: **100%**
- Rejection Consistency Rate: **100%**
- Average Routing Latency: **~1.42 ms**

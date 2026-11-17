# Future Research Extensions

The modular architecture of SatQuery AI is intentionally designed to support advanced research frontiers:

1. **Learned & Reinforcement Learning (RL) Routing**:
   - Replace linear heuristic scoring with a policy gradient / contextual bandit router trained on empirical execution latency and downstream accuracy.
2. **Uncertainty-Aware Model Selection**:
   - Incorporate Bayesian uncertainty estimates from specialist backbones into the routing formulation ($w_7 \cdot \text{CertaintyScore}$).
3. **Model Cascading & Ensembles**:
   - Route difficult samples to larger VLM specialists (e.g. 70B parameters) while handling common scene classifications with lightweight, energy-efficient edge adapters.
4. **Retrieval-Augmented Earth Observation (RS-RAG)**:
   - Index global vector databases of historical satellite acquisitions (Copernicus / Landsat) to ground temporal queries against historical baseline imagery.
5. **Geospatial & Topographic Reasoning**:
   - Deep integration of digital elevation models (DEM) and vector GIS layers (OpenStreetMap) within the multimodal reasoning layer.

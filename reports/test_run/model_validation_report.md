# SatQuery AI — Model Validation Report
**Generated:** 2026-10-29 17:24:30 UTC  
**Environment:** Windows 11 (10.0.26200) | Python 3.12.5 | PyTorch 2.14.1+cpu  
**Execution Device:** CPU (Authentic weights loaded and executed)

---

## 1. ChangeStar-1x96 (ResNet-18, LEVIR-CD)
- **Status:** **VERIFIED & OPERATIONAL** (Port 8001 / In-Process Engine)
- **Checkpoint Location:** `C:\Users\rajnp\Desktop\SAT\pretrained_weights\changestar1x96_r18_ft_levircd.pth`
- **Checkpoint File Size:** `62.72 MB`
- **State Dict Tensor Count:** `250` parameters
- **Architecture:** ResNet-18 FarSeg + `ChangeMixinBiSupN1` + `ConvUpsampleHead (sigmoid)`
- **Input Convention:** `Bi-temporal 6-channel concatenation [B, 6, H, W]`
- **Training Baseline:** `LEVIR-CD (Zhuo Zheng et al.)`

### Quantitative Inference Verification:
| Test Scenario | Input Observations | Changed Pixels | Total Pixels | Change Area (%) | Latency (ms) | Result |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Identical Images** | Pair of identical synthetic scenes | 0 | 262144 | **0.0%** | 697.76 ms | **PASS** |
| **Modified Images** | Scene $T_1$ vs Modified Scene $T_2$ | 885 | 262144 | **0.3376%** | 650.12 ms | **PASS** |

- **Mask Generation:** Binary change mask successfully rendered as PNG data URI (`data:image/png;base64,...`).
- **Classification Threshold:** Fixed at 0.50 per paper formulation.

---

## 2. CROMA Foundation Model (ViT-Base Multimodal)
- **Status:** **VERIFIED & OPERATIONAL** (Port 8002 / In-Process Engine)
- **Checkpoint Location:** `C:\Users\rajnp\Desktop\SAT\pretrained_weights\CROMA_base.pt`
- **Checkpoint File Size:** `741.54 MB`
- **Architecture:** CROMA Base (Dual-stream ViT + Cross-Attention Joint Encoder)
- **Sub-Networks Loaded:** `s1_encoder, s1_GAP_FFN, s2_encoder, s2_GAP_FFN, joint_encoder`
- **Input Channels:** SAR: 2 channels (`VV, VH`), Optical: 12 channels, Spatial size: `120x120` pixels.

### Quantitative Representation & Downstream Task:
- **Output Joint Representation:** Global Average Pooled joint embedding: `[1, 768]` (768 dimensions)
- **Patch Sequence Length:** `225` patches ($15 \times 15$ grid)
- **Cross-Sensor Cosine Similarity:** **`-0.0636`** (Valid range $[-1.0, 1.0]$)
- **Cross-Sensor L2 Distance:** `N/A`
- **Inference Latency:** `596.85 ms`
- **RGB Fallback Mode:** When standard 3-channel RGB imagery is submitted, `croma_engine.py` replicates channels to 12 channels to allow geometric representation while transparently emitting a warning that genuine radar backscatter is missing.

---

## 3. GeoChat-7B Remote-Sensing VLM
- **Status:** **STANDBY / NOT CONFIGURED (HONEST DEGRADATION)**
- **Configuration Endpoint:** `None (Standby)` in `C:\Users\rajnp\Desktop\SAT\backend\config\model_endpoints.yaml`
- **Timeout:** `120s`
- **Hardware Audit:**
  - Host RAM: 16.0 GB
  - Host GPU: NVIDIA GeForce RTX 3050 Laptop GPU (4.0 GB VRAM)
  - **Memory Constraint:** GeoChat-7B requires $\ge 14.5$ GB VRAM (FP16) or $\approx 4.2$ GB (INT4). Windows desktop compositor allocates ~0.8 GB, leaving ~3.2 GB usable VRAM. Local loading causes CUDA OOM or 2–5 minute CPU paging latency.
- **Safety & Research Integrity Policy:**
  - Zero hallucinated descriptions or mock text are returned to the user.
  - When unconfigured, the router returns an honest `NOT_CONFIGURED` limitation message explaining that spatial quantitative change metrics are available and directing the user to set a remote endpoint.
  - GeoChat endpoint can be configured in a single YAML file: `backend/config/model_endpoints.yaml`.

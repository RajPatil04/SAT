# Model Specialist Registry

The SatQuery AI Model Registry manages foundation specialist models, their capabilities, hardware requirements, and communication protocols.

## Registered Specialists

### 1. GeoChat-7B
- **Architecture**: Grounded Large Vision-Language Model with ViT-G/14 and Vicuna-7B LLM backbone.
- **Tasks**: `VQA`, `CAPTIONING`, `SCENE_ANALYSIS`, `OBJECT_ANALYSIS`, `GROUNDING`.
- **Supported Inputs**: `SINGLE_IMAGE`.
- **Supported Modalities**: `OPTICAL`, `MULTISPECTRAL`, `UNKNOWN`.
- **Reference**: Kuckreja et al., "GeoChat: Grounded Large Vision-Language Model for Remote Sensing", CVPR 2024.
- **Environment Keys**: `GEOCHAT_API_URL`, `GEOCHAT_API_TYPE`, `GEOCHAT_API_ENDPOINT`.

### 2. ChangeStar
- **Architecture**: Dense bi-temporal feature comparison framework utilizing paired ResNet/Swin backbones and ChangeMixin multi-scale comparison heads.
- **Tasks**: `CHANGE_DETECTION`, `CHANGE_VQA`.
- **Supported Inputs**: `BI_TEMPORAL`.
- **Supported Modalities**: `OPTICAL`, `MULTISPECTRAL`.
- **Reference**: Zheng et al., "ChangeStar: A General Framework for Bi-temporal Earth Observation", ICLR 2021.
- **Environment Keys**: `CHANGE_MODEL_API_URL`, `CHANGE_MODEL_API_TYPE`, `CHANGE_MODEL_API_ENDPOINT`.

### 3. CROMA (Cross-Modal Contrastive Learning)
- **Architecture**: Cross-modal dual encoders featuring joint cross-attention blocks for Sentinel-1 SAR (IW GRD) and Sentinel-2 Optical (MSI) fusion.
- **Tasks**: `OPTICAL_SAR_ANALYSIS`.
- **Supported Inputs**: `OPTICAL_SAR_PAIR`.
- **Supported Modalities**: `OPTICAL_SAR`.
- **Reference**: Anthony et al., "CROMA: Cross-Modal Contrastive and Self-Supervised Learning for Optical and SAR", NeurIPS 2023.
- **Environment Keys**: `CROMA_API_URL`, `CROMA_API_TYPE`, `CROMA_API_ENDPOINT`.

### 4. RS-GroundingSpecialist
- **Architecture**: Vision-language spatial referring expression specialist.
- **Tasks**: `GROUNDING`, `OBJECT_ANALYSIS`.
- **Supported Inputs**: `SINGLE_IMAGE`.
- **Supported Modalities**: `OPTICAL`, `MULTISPECTRAL`.
- **Environment Keys**: `GROUNDING_API_URL`, `GROUNDING_API_TYPE`, `GROUNDING_API_ENDPOINT`.

## Dynamic URL Updating
To update a specialist URL at runtime:
1. Update `backend/.env` with the new endpoint (e.g. `GEOCHAT_API_URL=https://new-geochat-service.hf.space`).
2. Restart backend or trigger config reload.
3. The React frontend continues operating with zero code alterations.

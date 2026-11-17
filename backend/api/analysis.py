# backend/api/analysis.py
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.config.settings import settings
from backend.router.schemas import AnalysisResponse, CompatibilityResult, ValidationResult
from backend.services.input_validator import InputValidator
from backend.services.execution_service import ExecutionService
from backend.services.compatibility_engine import CompatibilityEngine
from backend.services.metadata_service import MetadataService

router = APIRouter(tags=["Analysis Engine"])

async def _save_uploaded_files(files: List[UploadFile]) -> List[str]:
    saved_paths = []
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    for f in files:
        safe_name = f"{uuid.uuid4().hex[:8]}_{os.path.basename(f.filename or 'image.png')}"
        dest_path = os.path.join(settings.UPLOAD_DIR, safe_name)
        content = await f.read()
        with open(dest_path, "wb") as out_file:
            out_file.write(content)
        saved_paths.append(dest_path)
    return saved_paths

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_multimodal_query(
    images: List[UploadFile] = File(...),
    question: str = Form(...),
    input_mode: Optional[str] = Form(None),
    relationship: Optional[str] = Form(None),
    routing_config: Optional[str] = Form("CONFIG_C"),
    input_type: Optional[str] = Form(None),
    modality: Optional[str] = Form(None),
    date_1: Optional[str] = Form(None),
    date_2: Optional[str] = Form(None)
):
    """
    Primary generic multimodal entrypoint for SatQuery AI.
    Accepts 1 or 2 satellite observations, natural language query, and optional research configuration (A/B/C).
    """
    effective_mode = input_mode or input_type or ("SINGLE_IMAGE" if len(images) == 1 else "DOUBLE_IMAGE")
    effective_rel = relationship or modality

    is_valid, validation_errors = InputValidator.validate_request_inputs(
        files=images,
        question=question,
        input_mode=effective_mode,
        relationship=effective_rel
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail={"errors": validation_errors})

    saved_paths = await _save_uploaded_files(images)

    response = await ExecutionService.execute_pipeline(
        file_paths=saved_paths,
        query=question,
        user_input_type=effective_mode,
        user_modality=effective_rel,
        date_1=date_1,
        date_2=date_2,
        routing_config=routing_config or "CONFIG_C"
    )

    return response

@router.post("/analyze/single", response_model=AnalysisResponse)
async def analyze_single_image(
    image: UploadFile = File(...),
    question: str = Form(...),
    routing_config: Optional[str] = Form("CONFIG_C"),
    modality: Optional[str] = Form(None)
):
    """
    Specialized shortcut for Single-Image Earth Observation analysis.
    """
    return await analyze_multimodal_query(
        images=[image],
        question=question,
        input_mode="SINGLE_IMAGE",
        routing_config=routing_config,
        modality=modality
    )

@router.post("/analyze/change", response_model=AnalysisResponse)
async def analyze_bitemporal_change(
    image_t1: UploadFile = File(...),
    image_t2: UploadFile = File(...),
    question: str = Form(...),
    routing_config: Optional[str] = Form("CONFIG_C"),
    date_1: Optional[str] = Form(None),
    date_2: Optional[str] = Form(None)
):
    """
    Specialized shortcut for Bi-temporal Earth Observation change detection.
    """
    return await analyze_multimodal_query(
        images=[image_t1, image_t2],
        question=question,
        input_mode="DOUBLE_IMAGE",
        relationship="BI_TEMPORAL",
        routing_config=routing_config,
        date_1=date_1,
        date_2=date_2
    )

@router.post("/analyze/optical-sar", response_model=AnalysisResponse)
async def analyze_optical_sar_pair(
    optical_image: UploadFile = File(...),
    sar_image: UploadFile = File(...),
    question: str = Form(...),
    routing_config: Optional[str] = Form("CONFIG_C")
):
    """
    Specialized shortcut for Joint Optical and SAR Multimodal analysis.
    """
    return await analyze_multimodal_query(
        images=[optical_image, sar_image],
        question=question,
        input_mode="DOUBLE_IMAGE",
        relationship="OPTICAL_SAR",
        routing_config=routing_config
    )

@router.post("/validate", response_model=ValidationResult)
async def validate_raster_inputs(
    images: List[UploadFile] = File(...),
    input_mode: Optional[str] = Form(None),
    relationship: Optional[str] = Form(None),
    question: Optional[str] = Form(None),
    input_type: Optional[str] = Form(None),
    modality: Optional[str] = Form(None)
):
    """
    Dedicated validation stage before model selection (Section 3).
    Validates number of images, formats, decodability, dimensions, channel count,
    spatial alignment for temporal pairs, and modality requirements for Optical-SAR.
    """
    saved_paths = await _save_uploaded_files(images)
    res = InputValidator.validate_saved_files(
        file_paths=saved_paths,
        question=question or "Validate",
        input_mode=input_mode or input_type,
        relationship=relationship or modality
    )
    return res

@router.post("/validate/compatibility", response_model=CompatibilityResult)
async def validate_compatibility_legacy(
    images: List[UploadFile] = File(...),
    input_type: Optional[str] = Form(None),
    modality: Optional[str] = Form(None),
    date_1: Optional[str] = Form(None),
    date_2: Optional[str] = Form(None)
):
    """
    Backwards-compatible legacy compatibility endpoint.
    """
    saved_paths = await _save_uploaded_files(images)
    res = CompatibilityEngine.validate_inputs(
        file_paths=saved_paths,
        user_input_type=input_type,
        user_modality=modality,
        date_1=date_1,
        date_2=date_2
    )
    return res

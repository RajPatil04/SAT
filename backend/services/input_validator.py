# backend/services/input_validator.py
import os
import re
from typing import List, Optional, Tuple, Dict, Any
from fastapi import UploadFile
from PIL import Image

from backend.router.schemas import (
    ValidationResult,
    ImageValidationItem,
    ModalityType,
    InputType
)
from backend.services.compatibility.format_checker import FormatChecker, SUPPORTED_EXTENSIONS
from backend.services.compatibility.metadata_checker import MetadataChecker
from backend.services.compatibility.modality_checker import ModalityChecker

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB max per file

class InputValidator:
    """
    Dedicated Pre-Routing Input Validation Engine for SatQuery AI.
    Implements Section 3 validation requirements:
    - Number of uploaded images
    - File type and size limits
    - Decodability and channel consistency
    - Relationship compatibility (Bi-temporal spatial alignment, Optical-SAR modality verification)
    - Query quality and ambiguity detection
    """

    @staticmethod
    def validate_request_inputs(
        files: List[UploadFile],
        question: Optional[str],
        input_mode: Optional[str] = None,
        relationship: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Quick HTTP request-level preflight validation.
        """
        errors = []

        if not question or not question.strip():
            errors.append("Query is required. Please provide a remote-sensing question or instruction.")

        if not files or len(files) == 0:
            errors.append("At least one satellite/remote-sensing image file is required.")
            return False, errors

        # Check input mode expectations
        normalized_mode = (input_mode or "").upper().strip()
        if normalized_mode in ("SINGLE_IMAGE", "SINGLE") and len(files) > 1:
            errors.append(f"Single Image mode received {len(files)} files. Please upload exactly 1 image.")
        elif normalized_mode in ("DOUBLE_IMAGE", "DOUBLE", "BI_TEMPORAL", "OPTICAL_SAR_PAIR") and len(files) < 2:
            errors.append(f"Double Image mode requires exactly 2 images, but received {len(files)}.")

        for idx, f in enumerate(files):
            if not f.filename:
                errors.append(f"Uploaded file {idx+1} does not have a valid filename.")
                continue

            ext = os.path.splitext(f.filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                errors.append(
                    f"File '{f.filename}' has unsupported extension '{ext}'. "
                    f"Supported formats: GeoTIFF (.tif/.tiff), PNG, JPEG, NumPy (.npy/.npz)."
                )

        return (len(errors) == 0), errors

    @staticmethod
    def validate_saved_files(
        file_paths: List[str],
        question: Optional[str],
        input_mode: Optional[str] = None,
        relationship: Optional[str] = None
    ) -> ValidationResult:
        """
        Comprehensive deep validation stage on persisted file assets.
        Validates decoding, channels, spatial alignment, and modality matching.
        """
        blocking_errors: List[str] = []
        warnings: List[str] = []
        messages: List[str] = []
        image_items: List[ImageValidationItem] = []

        mode = (input_mode or "SINGLE_IMAGE" if len(file_paths) == 1 else "DOUBLE_IMAGE").upper().strip()
        rel = (relationship or "UNKNOWN").upper().strip()

        # 1. Image count validation
        num_files = len(file_paths)
        if mode in ("SINGLE_IMAGE", "SINGLE") and num_files != 1:
            if num_files == 0:
                blocking_errors.append("No image uploaded for Single Image mode.")
            else:
                warnings.append(f"Single Image mode received {num_files} images. Only the primary image will be routed.")
        elif mode in ("DOUBLE_IMAGE", "DOUBLE") and num_files != 2:
            blocking_errors.append(f"Double Image mode requires exactly 2 images, but {num_files} were provided.")

        # 2. File size & decode validation for each image
        for idx, fp in enumerate(file_paths):
            fname = os.path.basename(fp)
            if not os.path.exists(fp):
                blocking_errors.append(f"Image {idx+1} file not found: {fname}")
                continue

            fsize = os.path.getsize(fp)
            if fsize > MAX_FILE_SIZE_BYTES:
                blocking_errors.append(f"Image '{fname}' ({fsize / (1024*1024):.1f} MB) exceeds maximum allowed size (50 MB).")

            # Validate decodability and extract dimensions & channels
            is_valid_fmt, fmt_name, fmt_err = FormatChecker.validate_file(fp)
            if not is_valid_fmt:
                blocking_errors.append(f"Image '{fname}' cannot be decoded: {fmt_err}")
                image_items.append(
                    ImageValidationItem(
                        filename=fname,
                        format="CORRUPT",
                        width=0,
                        height=0,
                        channels=0,
                        file_size_bytes=fsize,
                        is_valid=False,
                        detected_modality=ModalityType.UNKNOWN,
                        error=fmt_err
                    )
                )
                continue

            # Extract detailed structural metadata
            meta = MetadataChecker.extract_metadata(fp)
            meta.detected_modality = ModalityChecker.infer_modality(fp, meta)

            # Content verification: inspect decoded contents and check for blank / solid color
            pixel_std: Optional[float] = None
            content_error: Optional[str] = None
            try:
                import numpy as np
                ext_check = os.path.splitext(fp)[1].lower()
                if ext_check in (".npy", ".npz"):
                    arr_data = np.load(fp)
                    if isinstance(arr_data, np.lib.npyio.NpzFile):
                        first_key = arr_data.files[0]
                        arr_check = arr_data[first_key]
                        arr_data.close()
                    else:
                        arr_check = arr_data
                    pixel_std = float(np.std(arr_check))
                else:
                    with Image.open(fp) as img_check:
                        arr_check = np.array(img_check.convert("RGB"))
                        pixel_std = float(np.std(arr_check))

                if meta.width < 16 or meta.height < 16:
                    content_error = (
                        f"Image '{fname}' dimensions ({meta.width}x{meta.height}) are too small for satellite analysis. "
                        f"Minimum resolution is 16x16."
                    )
                elif pixel_std < 0.5:
                    content_error = (
                        f"Image '{fname}' contains a uniform solid color (std={pixel_std:.2f}) with zero discernible "
                        f"satellite features or terrain structure. Unsuitable for analysis."
                    )
            except Exception as e:
                warnings.append(f"Could not compute content variance for '{fname}': {str(e)}")

            if content_error:
                blocking_errors.append(content_error)
                image_items.append(
                    ImageValidationItem(
                        filename=fname,
                        format=meta.format,
                        width=meta.width,
                        height=meta.height,
                        channels=meta.channels,
                        file_size_bytes=fsize,
                        is_valid=False,
                        detected_modality=meta.detected_modality,
                        variance=round(pixel_std, 2) if pixel_std is not None else None,
                        error=content_error
                    )
                )
                continue

            image_items.append(
                ImageValidationItem(
                    filename=fname,
                    format=meta.format,
                    width=meta.width,
                    height=meta.height,
                    channels=meta.channels,
                    file_size_bytes=fsize,
                    is_valid=True,
                    detected_modality=meta.detected_modality,
                    variance=round(pixel_std, 2) if pixel_std is not None else None,
                    error=None
                )
            )
            messages.append(f"Image {idx+1} '{fname}': {meta.width}x{meta.height}, {meta.channels} bands, {meta.format} (pixel std: {pixel_std:.1f} if pixel_std else 'N/A').")

        # 3. Spatial alignment check for double images
        spatial_aligned: Optional[bool] = None
        if len(image_items) == 2:
            im1, im2 = image_items[0], image_items[1]
            dim_match = (im1.width == im2.width) and (im1.height == im2.height)
            aspect1 = round(im1.width / max(im1.height, 1), 3)
            aspect2 = round(im2.width / max(im2.height, 1), 3)
            aspect_match = abs(aspect1 - aspect2) < 0.05

            if dim_match:
                spatial_aligned = True
                messages.append("Spatial alignment check: Dimensions match identically between observation pair.")
            else:
                spatial_aligned = False
                if not aspect_match:
                    warnings.append(
                        f"Spatial mismatch: Image 1 is {im1.width}x{im1.height} (aspect {aspect1}) "
                        f"while Image 2 is {im2.width}x{im2.height} (aspect {aspect2}). "
                        "Resizing may cause geometric scale distortion."
                    )
                else:
                    warnings.append(
                        f"Dimension variance: Image 1 is {im1.width}x{im1.height} vs Image 2 is {im2.width}x{im2.height}. "
                        "Automated bilinear interpolation will be applied for model alignment."
                    )

                if rel in ("BI_TEMPORAL", "BEFORE_AFTER"):
                    warnings.append(
                        "Change Detection Notice: Images are not natively co-registered. "
                        "Differences in boundary edges may reflect misalignment rather than true physical change."
                    )

        # 4. Modality and relationship verification
        modality_compatible: Optional[bool] = None
        inferred_rel = rel
        if len(image_items) == 2:
            im1, im2 = image_items[0], image_items[1]
            modalities = {im1.detected_modality, im2.detected_modality}
            has_sar = ModalityType.SAR in modalities or im1.channels in (1, 2) or im2.channels in (1, 2) or im1.format == "NUMPY" or im2.format == "NUMPY"
            has_optical = ModalityType.OPTICAL in modalities or ModalityType.MULTISPECTRAL in modalities or im1.channels >= 3 or im2.channels >= 3

            q_lower = (question or "").lower()
            optical_sar_keywords = ["optical and sar", "sar and optical", "optical + sar", "radar and optical", "sentinel-1 and sentinel-2", "s1 and s2", "cross-modal", "radar", "sar"]
            is_optical_sar_query = any(kw in q_lower for kw in optical_sar_keywords)
            change_keywords = ["change", "changes", "changed", "difference", "differ", "diff", "increased", "decreased", "urban expansion", "expansion"]
            is_change_query = any(kw in q_lower for kw in change_keywords)

            # Auto-infer relationship when not explicitly specified
            if inferred_rel in ("UNKNOWN", "NONE", ""):
                if is_optical_sar_query or (has_sar and has_optical):
                    inferred_rel = "OPTICAL_SAR"
                elif is_change_query or (not has_sar and has_optical):
                    inferred_rel = "BI_TEMPORAL"
                else:
                    inferred_rel = "BI_TEMPORAL"

            if rel in ("OPTICAL_SAR", "OPTICAL_AND_SAR") or is_optical_sar_query:
                # Must have authentic optical + SAR data
                if has_sar and has_optical:
                    modality_compatible = True
                    messages.append("Modality check: Verified complementary Optical and SAR sensor inputs.")
                else:
                    modality_compatible = False
                    warnings.append(
                        "Optical-SAR Modality Alert: Both images appear to be standard optical RGB rasters "
                        "without radar backscatter channels. CROMA requires true multi-sensor radar and optical inputs. "
                        "Ordinary RGB pairs cannot produce genuine Optical-SAR representations."
                    )
            elif rel in ("BI_TEMPORAL", "BEFORE_AFTER") or is_change_query:
                # Temporal comparison expects same sensor modality
                if im1.detected_modality != ModalityType.UNKNOWN and im2.detected_modality != ModalityType.UNKNOWN:
                    if im1.detected_modality != im2.detected_modality:
                        warnings.append(
                            f"Cross-sensor alert: Image 1 is {im1.detected_modality.value} while Image 2 is {im2.detected_modality.value}. "
                            "Direct pixel differencing across different sensors can yield false-positive change maps."
                        )
                modality_compatible = True
            else:
                modality_compatible = True

        # 5. Question quality and ambiguity check
        if question:
            q_clean = question.strip()
            if len(q_clean) < 5 or q_clean in ("?", "what", "analyze", "test", "look"):
                warnings.append("Ambiguous query: Question is very brief. The router will fall back to general scene analysis.")
        else:
            blocking_errors.append("Question is required. Enter a natural language query.")

        is_valid = len(blocking_errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            input_mode=mode,
            relationship=inferred_rel if mode in ("DOUBLE_IMAGE", "DOUBLE") else None,
            images=image_items,
            warnings=warnings,
            blocking_errors=blocking_errors,
            validation_messages=messages,
            spatial_aligned=spatial_aligned,
            modality_compatible=modality_compatible
        )

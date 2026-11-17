# backend/services/compatibility_engine.py
from typing import List, Optional
from backend.router.schemas import (
    ImageMetadata,
    InputType,
    ModalityType,
    CompatibilityResult,
)
from backend.services.compatibility.format_checker import FormatChecker
from backend.services.compatibility.metadata_checker import MetadataChecker
from backend.services.compatibility.modality_checker import ModalityChecker
from backend.services.compatibility.spatial_checker import SpatialChecker
from backend.services.compatibility.temporal_checker import TemporalChecker

class CompatibilityEngine:
    @staticmethod
    def validate_inputs(
        file_paths: List[str],
        user_input_type: Optional[str] = None,
        user_modality: Optional[str] = None,
        date_1: Optional[str] = None,
        date_2: Optional[str] = None
    ) -> CompatibilityResult:
        """
        Executes end-to-end multi-image compatibility and metadata extraction.
        Evaluates format integrity, modality determination, spatial alignment, and temporal validity.
        """
        validation_messages = []
        blocking_errors = []

        if not file_paths:
            return CompatibilityResult(
                is_compatible=False,
                input_type=InputType.UNKNOWN,
                modality=ModalityType.UNKNOWN,
                validation_messages=["No image files provided."],
                blocking_errors=["Input image list is empty."]
            )

        # 1. Format validation & metadata extraction
        metadata_list: List[ImageMetadata] = []
        for idx, fp in enumerate(file_paths):
            is_valid, fmt, err = FormatChecker.validate_file(fp)
            if not is_valid:
                blocking_errors.append(f"Image {idx+1} ({fp}): {err}")
                continue

            meta = MetadataChecker.extract_metadata(fp)
            # Infer individual modality
            meta.detected_modality = ModalityChecker.infer_modality(fp, meta, user_modality)
            metadata_list.append(meta)

        if blocking_errors:
            return CompatibilityResult(
                is_compatible=False,
                input_type=InputType.UNKNOWN,
                modality=ModalityType.UNKNOWN,
                validation_messages=validation_messages,
                blocking_errors=blocking_errors
            )

        # 2. Determine InputType
        num_images = len(metadata_list)
        if num_images == 1:
            detected_input_type = InputType.SINGLE_IMAGE
            validation_messages.append("Single image analysis pipeline verified.")
        elif num_images == 2:
            # Check if one is SAR and one is OPTICAL
            modalities = {m.detected_modality for m in metadata_list}
            if ModalityType.SAR in modalities and (ModalityType.OPTICAL in modalities or ModalityType.MULTISPECTRAL in modalities):
                detected_input_type = InputType.OPTICAL_SAR_PAIR
                validation_messages.append("Multimodal Optical + SAR pair detected.")
            elif user_input_type == "OPTICAL_SAR_PAIR":
                detected_input_type = InputType.OPTICAL_SAR_PAIR
                validation_messages.append("User designated Optical + SAR pair.")
            else:
                detected_input_type = InputType.BI_TEMPORAL
                validation_messages.append("Bi-temporal observation pair detected.")
        else:
            detected_input_type = InputType.MULTI_TEMPORAL
            validation_messages.append(f"Multi-temporal observation sequence detected ({num_images} images).")

        # 3. Overall Modality Synthesis
        if detected_input_type == InputType.OPTICAL_SAR_PAIR:
            overall_modality = ModalityType.OPTICAL_SAR
        elif all(m.detected_modality == ModalityType.SAR for m in metadata_list):
            overall_modality = ModalityType.SAR
        elif all(m.detected_modality == ModalityType.MULTISPECTRAL for m in metadata_list):
            overall_modality = ModalityType.MULTISPECTRAL
        elif all(m.detected_modality in (ModalityType.OPTICAL, ModalityType.UNKNOWN) for m in metadata_list):
            overall_modality = ModalityType.OPTICAL
        else:
            overall_modality = ModalityType.OPTICAL

        # 4. Spatial Compatibility
        spatial_comp = SpatialChecker.check_spatial_compatibility(metadata_list)
        if not spatial_comp.is_compatible:
            validation_messages.append(f"Spatial notice: {spatial_comp.details}")
        else:
            validation_messages.append(f"Spatial compatibility: {spatial_comp.details}")

        # 5. Temporal Compatibility
        temporal_comp = None
        if detected_input_type in (InputType.BI_TEMPORAL, InputType.MULTI_TEMPORAL):
            temporal_comp = TemporalChecker.check_temporal_compatibility(metadata_list, date_1, date_2)
            if not temporal_comp.is_compatible:
                blocking_errors.append(f"Temporal incompatibility: {temporal_comp.details}")
            else:
                validation_messages.append(f"Temporal compatibility: {temporal_comp.details}")

        is_compatible = len(blocking_errors) == 0

        # Build validation details summary
        from backend.services.input_validator import InputValidator
        val_details = InputValidator.validate_saved_files(
            file_paths=file_paths,
            question="Validate",
            input_mode=user_input_type,
            relationship=user_input_type or user_modality
        )

        return CompatibilityResult(
            is_compatible=is_compatible,
            input_type=detected_input_type,
            modality=overall_modality,
            spatial=spatial_comp,
            temporal=temporal_comp,
            validation_messages=validation_messages,
            blocking_errors=blocking_errors,
            validation_details=val_details
        )

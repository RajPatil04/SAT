# backend/router/input_classifier.py
from typing import List, Optional
from backend.router.schemas import InputType, ModalityType, ImageMetadata

class InputClassifier:
    @staticmethod
    def classify_input(
        images_metadata: List[ImageMetadata],
        user_input_type: Optional[str] = None,
        query_cue_optical_sar: bool = False
    ) -> InputType:
        """
        Infers the structural input type from input assets and metadata.
        """
        if user_input_type:
            try:
                return InputType(user_input_type)
            except ValueError:
                pass

        count = len(images_metadata)
        if count == 0:
            return InputType.UNKNOWN
        if count == 1:
            return InputType.SINGLE_IMAGE

        if count == 2:
            mods = {img.detected_modality for img in images_metadata}
            if query_cue_optical_sar or (ModalityType.SAR in mods and (ModalityType.OPTICAL in mods or ModalityType.MULTISPECTRAL in mods)):
                return InputType.OPTICAL_SAR_PAIR
            return InputType.BI_TEMPORAL

        return InputType.MULTI_TEMPORAL

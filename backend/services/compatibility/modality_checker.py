# backend/services/compatibility/modality_checker.py
import os
import re
from typing import Optional
from PIL import Image
import numpy as np
from backend.router.schemas import ModalityType, ImageMetadata

SAR_KEYWORDS = {"sar", "sentinel-1", "s1", "grd", "slc", "vv", "vh", "hh", "hv", "radar", "terrasar", "palsar", "cosmo"}
OPTICAL_KEYWORDS = {"optical", "sentinel-2", "s2", "landsat", "rgb", "planet", "spot", "naip", "worldview", "truecolor"}

class ModalityChecker:
    @staticmethod
    def infer_modality(
        file_path: str,
        metadata: ImageMetadata,
        user_hint: Optional[str] = None
    ) -> ModalityType:
        """
        Infers the sensor modality of an image using:
        1. Explicit user/caller hint
        2. Filename and metadata indicators
        3. Band count, channel structure, and pixel statistics
        """
        # 1. User Hint (Only if specifying single modality)
        if user_hint:
            hint_upper = user_hint.upper().strip()
            if hint_upper in ("SAR", "SENTINEL-1", "S1", "RADAR"):
                return ModalityType.SAR
            if hint_upper in ("MULTISPECTRAL",):
                return ModalityType.MULTISPECTRAL
            if hint_upper in ("OPTICAL", "RGB", "SENTINEL-2", "S2"):
                return ModalityType.OPTICAL

        # 2. Filename Inspection
        fname_lower = os.path.basename(file_path).lower()
        tokens = set(re.split(r'[_.\-\s]+', fname_lower))

        if tokens.intersection(SAR_KEYWORDS):
            return ModalityType.SAR

        if tokens.intersection(OPTICAL_KEYWORDS):
            if metadata.channels > 3:
                return ModalityType.MULTISPECTRAL
            return ModalityType.OPTICAL

        # 3. Channel Structure & Pixel Statistics
        if metadata.channels > 4:
            return ModalityType.MULTISPECTRAL

        if metadata.channels == 1:
            # Single-band image: could be SAR amplitude or single-band panchromatic/DEM.
            # Analyze speckle/variance to provide an informed inference.
            try:
                with Image.open(file_path) as img:
                    arr = np.array(img, dtype=np.float32)
                    mean = np.mean(arr)
                    std = np.std(arr)
                    # Coefficient of variation (std/mean) in SAR speckle is often > 0.52
                    cv = (std / mean) if mean > 1e-4 else 0
                    if cv > 0.8:
                        return ModalityType.SAR
            except Exception:
                pass
            return ModalityType.OPTICAL

        if metadata.channels in (3, 4):
            return ModalityType.OPTICAL

        return ModalityType.UNKNOWN

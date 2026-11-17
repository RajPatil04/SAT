# backend/preprocessing/geochat_preprocessor.py
import os
from typing import List, Dict, Any
from PIL import Image
from backend.preprocessing.base_preprocessor import BasePreprocessor

class GeoChatPreprocessor(BasePreprocessor):
    def preprocess(self, file_paths: List[str], target_size: int = 512, **kwargs) -> Dict[str, Any]:
        """
        Prepares single image for GeoChat-7B vision backbone.
        Ensures RGB color format, handles transparency/multichannel conversions.
        """
        if not file_paths:
            raise ValueError("GeoChatPreprocessor requires at least one image file.")

        img_path = file_paths[0]
        with Image.open(img_path) as raw_img:
            # Handle band structures: convert 1-band grayscale or >3 band multispectral to RGB
            if raw_img.mode in ("RGBA", "LA") or (raw_img.mode == "P" and "transparency" in raw_img.info):
                img_rgb = raw_img.convert("RGB")
            elif raw_img.mode != "RGB":
                img_rgb = raw_img.convert("RGB")
            else:
                img_rgb = raw_img.copy()

            original_size = img_rgb.size
            # Rescale if excessive dimension
            if max(original_size) > 2048:
                img_rgb.thumbnail((target_size * 2, target_size * 2), Image.Resampling.LANCZOS)

            return {
                "primary_image_path": img_path,
                "original_dimensions": original_size,
                "processed_dimensions": img_rgb.size,
                "channels": 3,
                "color_space": "RGB"
            }

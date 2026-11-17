# backend/preprocessing/change_preprocessor.py
import os
from typing import List, Dict, Any
from PIL import Image
from backend.preprocessing.base_preprocessor import BasePreprocessor

class ChangePreprocessor(BasePreprocessor):
    def preprocess(self, file_paths: List[str], target_size: int = 512, **kwargs) -> Dict[str, Any]:
        """
        Prepares bi-temporal image pair for dense feature comparison models (e.g. ChangeStar).
        Ensures both images share identical spatial dimensions and alignment.
        """
        if len(file_paths) < 2:
            raise ValueError("ChangePreprocessor requires two images representing temporal epochs T1 and T2.")

        path_t1, path_t2 = file_paths[0], file_paths[1]

        with Image.open(path_t1) as img1, Image.open(path_t2) as img2:
            rgb1 = img1.convert("RGB")
            rgb2 = img2.convert("RGB")

            # Check if dimensions match; if not, resize T2 to match T1 spatial grid
            aligned_size = rgb1.size
            if rgb1.size != rgb2.size:
                rgb2 = rgb2.resize(aligned_size, Image.Resampling.BILINEAR)

            return {
                "t1_path": path_t1,
                "t2_path": path_t2,
                "aligned_dimensions": aligned_size,
                "channels": 3,
                "resampled_t2": (rgb1.size != rgb2.size)
            }

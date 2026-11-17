# backend/preprocessing/croma_preprocessor.py
import os
from typing import List, Dict, Any
from PIL import Image
from backend.preprocessing.base_preprocessor import BasePreprocessor

class CROMAPreprocessor(BasePreprocessor):
    def preprocess(self, file_paths: List[str], **kwargs) -> Dict[str, Any]:
        """
        Prepares paired Optical (e.g. Sentinel-2) and SAR (e.g. Sentinel-1) inputs for CROMA.
        Validates modalities and extracts channel representations.
        Supports standard raster images (.tif, .png, .jpg) and NumPy arrays (.npy, .npz).
        """
        if len(file_paths) < 2:
            raise ValueError("CROMAPreprocessor requires paired Optical and SAR imagery.")

        path1, path2 = file_paths[0], file_paths[1]

        def get_channel_info(fp: str):
            ext = os.path.splitext(fp)[1].lower()
            if ext in (".npy", ".npz"):
                import numpy as np
                arr = np.load(fp)
                if isinstance(arr, np.lib.npyio.NpzFile):
                    arr_data = arr[arr.files[0]]
                    arr.close()
                else:
                    arr_data = arr
                shape = arr_data.shape
                if len(shape) == 3:
                    if shape[0] in (1, 2, 3, 4, 12, 13):
                        c, h, w = int(shape[0]), int(shape[1]), int(shape[2])
                    else:
                        h, w, c = int(shape[0]), int(shape[1]), int(shape[2])
                elif len(shape) == 2:
                    h, w, c = int(shape[0]), int(shape[1]), 1
                else:
                    h, w, c = 120, 120, 1
                return c, (w, h)
            else:
                with Image.open(fp) as img:
                    return len(img.getbands()), img.size

        bands1, size1 = get_channel_info(path1)
        bands2, size2 = get_channel_info(path2)

        # Determine which is optical and which is SAR
        # Typically Optical has 3+ channels (or 12 for Sentinel-2), SAR has 1-2 channels (VV, VH)
        if bands1 >= 3 and bands2 <= 2:
            optical_path, sar_path = path1, path2
            optical_bands, sar_bands = bands1, bands2
        elif bands2 >= 3 and bands1 <= 2:
            optical_path, sar_path = path2, path1
            optical_bands, sar_bands = bands2, bands1
        else:
            optical_path, sar_path = path1, path2
            optical_bands, sar_bands = bands1, bands2

        return {
            "optical_path": optical_path,
            "sar_path": sar_path,
            "optical_channels": optical_bands,
            "sar_channels": sar_bands,
            "cross_modal_alignment_verified": (size1 == size2),
            "dimensions": size1
        }

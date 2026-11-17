# backend/services/compatibility/format_checker.py
import os
from typing import Tuple, Optional
from PIL import Image

SUPPORTED_FORMATS = {"TIFF", "GEOTIFF", "PNG", "JPEG", "JPG", "NUMPY"}
SUPPORTED_EXTENSIONS = {".tif", ".tiff", ".geotiff", ".png", ".jpg", ".jpeg", ".npy", ".npz"}

class FormatChecker:
    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validates file existence, format, and readability.
        Returns: (is_valid, format_name, error_message)
        """
        if not os.path.exists(file_path):
            return False, "UNKNOWN", f"File not found at path: {file_path}"
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return False, "UNKNOWN", f"Unsupported file extension '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"

        if ext in (".npy", ".npz"):
            try:
                import numpy as np
                arr = np.load(file_path)
                if isinstance(arr, np.lib.npyio.NpzFile):
                    arr.close()
                return True, "NUMPY", None
            except Exception as e:
                return False, "CORRUPT", f"Failed to load numpy array: {str(e)}"

        try:
            with Image.open(file_path) as img:
                raw_format = img.format.upper() if img.format else "UNKNOWN"
                is_geotiff = False
                if raw_format in ("TIFF", "TIF"):
                    # Check for GeoTIFF tags (e.g. ModelPixelScaleTag=33550, GeoKeyDirectoryTag=34735)
                    tags = getattr(img, "tag_v2", {})
                    if 33550 in tags or 34735 in tags or 33922 in tags:
                        is_geotiff = True
                
                fmt = "GEOTIFF" if is_geotiff else raw_format
                return True, fmt, None
        except Exception as e:
            return False, "CORRUPT", f"Failed to open image file: {str(e)}"

# backend/services/compatibility/metadata_checker.py
import os
from typing import Dict, Any, Optional, List
from PIL import Image, ExifTags
from backend.router.schemas import ImageMetadata, ModalityType

class MetadataChecker:
    @staticmethod
    def extract_metadata(file_path: str, preview_url: Optional[str] = None) -> ImageMetadata:
        """
        Extracts structural, geospatial, and temporal metadata from an image.
        Supports GeoTIFF, standard TIFF, PNG, and JPEG.
        """
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".npy", ".npz"):
            import numpy as np
            arr = np.load(file_path)
            if isinstance(arr, np.lib.npyio.NpzFile):
                first_key = arr.files[0]
                arr_data = arr[first_key]
                arr.close()
            else:
                arr_data = arr

            shape = arr_data.shape
            if len(shape) == 3:
                # Shape could be [C, H, W] or [H, W, C]
                if shape[0] in (1, 2, 3, 4, 12, 13):
                    channels, height, width = int(shape[0]), int(shape[1]), int(shape[2])
                else:
                    height, width, channels = int(shape[0]), int(shape[1]), int(shape[2])
            elif len(shape) == 2:
                height, width, channels = int(shape[0]), int(shape[1]), 1
            else:
                height, width, channels = 120, 120, 1

            detected_mod = ModalityType.SAR if channels in (1, 2) else (ModalityType.MULTISPECTRAL if channels > 3 else ModalityType.OPTICAL)
            return ImageMetadata(
                filename=filename,
                format="NUMPY",
                width=width,
                height=height,
                channels=channels,
                datatype=f"float32 ({channels} channel{'s' if channels > 1 else ''})",
                is_geotiff=False,
                crs=None,
                bounds=None,
                resolution=None,
                detected_modality=detected_mod,
                acquisition_date=None,
                file_size_bytes=file_size,
                preview_url=preview_url
            )

        with Image.open(file_path) as img:
            width, height = img.size
            mode = img.mode
            channels = len(mode) if mode else 3
            format_name = img.format.upper() if img.format else "UNKNOWN"
            datatype = str(img.getbands())

            is_geotiff = False
            crs = None
            bounds: Optional[List[float]] = None
            resolution: Optional[List[float]] = None
            acquisition_date: Optional[str] = None

            # Inspect TIFF tags
            if format_name in ("TIFF", "TIF"):
                tag_v2 = getattr(img, "tag_v2", {})
                # GeoKeyDirectoryTag = 34735, ModelPixelScaleTag = 33550, ModelTiepointTag = 33922
                if 33550 in tag_v2 or 34735 in tag_v2 or 33922 in tag_v2:
                    is_geotiff = True
                    format_name = "GEOTIFF"
                
                if 33550 in tag_v2:
                    scale = tag_v2[33550]
                    if len(scale) >= 2:
                        resolution = [float(scale[0]), float(scale[1])]
                
                # Check for EPSG code in GeoKeyDirectoryTag (34735) or standard tags
                if 34735 in tag_v2:
                    geo_keys = tag_v2[34735]
                    # Simple heuristic parser for ProjectedCSTypeGeoKey = 3072 or GeographicTypeGeoKey = 2048
                    crs = "EPSG:GeoTIFF-Referenced"

                # Check DateTime tag (306)
                if 306 in tag_v2:
                    acquisition_date = str(tag_v2[306]).strip()

            # Inspect EXIF if available (JPEG / TIFF)
            if not acquisition_date:
                try:
                    exif = img.getexif()
                    if exif:
                        for tag_id, val in exif.items():
                            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                            if tag_name in ("DateTime", "DateTimeOriginal", "DateTimeDigitized"):
                                acquisition_date = str(val).strip()
                                break
                except Exception:
                    pass

            return ImageMetadata(
                filename=filename,
                format=format_name,
                width=width,
                height=height,
                channels=channels,
                datatype=f"{mode} ({channels} band{'s' if channels > 1 else ''})",
                is_geotiff=is_geotiff,
                crs=crs,
                bounds=bounds,
                resolution=resolution,
                detected_modality=ModalityType.UNKNOWN,
                acquisition_date=acquisition_date,
                file_size_bytes=file_size,
                preview_url=preview_url
            )

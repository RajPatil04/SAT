# backend/services/metadata_service.py
from typing import List, Optional
from backend.router.schemas import ImageMetadata
from backend.services.compatibility.metadata_checker import MetadataChecker
from backend.services.compatibility.modality_checker import ModalityChecker

class MetadataService:
    @staticmethod
    def extract_all(
        file_paths: List[str],
        user_modality: Optional[str] = None
    ) -> List[ImageMetadata]:
        """
        Extracts structural, geospatial, and sensor metadata for each file in sequence.
        """
        results = []
        for fp in file_paths:
            meta = MetadataChecker.extract_metadata(fp)
            meta.detected_modality = ModalityChecker.infer_modality(fp, meta, user_modality)
            results.append(meta)
        return results

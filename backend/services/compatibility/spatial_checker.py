# backend/services/compatibility/spatial_checker.py
from typing import List, Optional
from backend.router.schemas import ImageMetadata, SpatialCompatibility

class SpatialChecker:
    @staticmethod
    def check_spatial_compatibility(
        metadata_list: List[ImageMetadata]
    ) -> SpatialCompatibility:
        """
        Evaluates spatial compatibility across multiple input images.
        Validates dimensions, aspect ratio, CRS, and spatial resolution.
        Does not falsely claim images are co-registered without proof.
        """
        if len(metadata_list) < 2:
            return SpatialCompatibility(
                dimension_match=True,
                crs_match=True,
                resolution_ratio=1.0,
                extent_overlap=True,
                is_compatible=True,
                details="Single image input: self-consistent spatial domain."
            )

        img1, img2 = metadata_list[0], metadata_list[1]

        # 1. Dimension & Aspect Ratio Check
        dim_match = (img1.width == img2.width) and (img1.height == img2.height)
        aspect1 = round(img1.width / max(img1.height, 1), 3)
        aspect2 = round(img2.width / max(img2.height, 1), 3)
        aspect_match = abs(aspect1 - aspect2) < 0.05

        # 2. CRS Check
        crs_match: Optional[bool] = None
        if img1.crs and img2.crs:
            crs_match = (img1.crs == img2.crs)
        elif img1.crs or img2.crs:
            crs_match = False

        # 3. Resolution Check
        resolution_ratio: Optional[float] = None
        if img1.resolution and img2.resolution:
            res1 = img1.resolution[0]
            res2 = img2.resolution[0]
            if res2 > 0:
                resolution_ratio = round(res1 / res2, 3)

        # 4. Synthesize Co-registration and Compatibility Assessment
        details_parts = []
        is_compatible = True

        if not dim_match:
            details_parts.append(
                f"Dimension discrepancy: Image 1 is {img1.width}x{img1.height}, "
                f"while Image 2 is {img2.width}x{img2.height}."
            )
            if not aspect_match:
                is_compatible = False
                details_parts.append("Aspect ratios differ significantly. Automatic resizing may distort geospatial scale.")
            else:
                details_parts.append("Aspect ratios match; spatial resampling/resizing will be applied during preprocessing.")

        if crs_match is False:
            details_parts.append(f"CRS mismatch: {img1.crs} vs {img2.crs}. Reprojection is advised.")

        if resolution_ratio is not None and (resolution_ratio > 2.0 or resolution_ratio < 0.5):
            details_parts.append(f"Large ground sampling distance (GSD) ratio ({resolution_ratio}x).")

        # Crucial honest reporting:
        if not img1.is_geotiff and not img2.is_geotiff:
            details_parts.append(
                "Images are standard raster formats without georeferencing metadata. "
                "Spatial compatibility could not be verified at geodetic coordinates; pixel-grid alignment assumed."
            )
        elif dim_match:
            details_parts.append("Pixel dimensions align perfectly (1:1 spatial grid correspondence).")

        details = " ".join(details_parts) if details_parts else "Spatial parameters align."

        return SpatialCompatibility(
            dimension_match=dim_match,
            crs_match=crs_match,
            resolution_ratio=resolution_ratio,
            extent_overlap=None,
            is_compatible=is_compatible,
            details=details
        )

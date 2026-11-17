# backend/tests/test_compatibility.py
import pytest
from backend.router.schemas import ImageMetadata, ModalityType, InputType
from backend.services.compatibility.spatial_checker import SpatialChecker
from backend.services.compatibility.temporal_checker import TemporalChecker
from backend.services.compatibility.modality_checker import ModalityChecker

def test_spatial_checker_identical_dimensions():
    m1 = ImageMetadata(filename="img1.png", format="PNG", width=512, height=512, channels=3, datatype="RGB")
    m2 = ImageMetadata(filename="img2.png", format="PNG", width=512, height=512, channels=3, datatype="RGB")

    res = SpatialChecker.check_spatial_compatibility([m1, m2])
    assert res.is_compatible is True
    assert res.dimension_match is True

def test_spatial_checker_differing_aspect_ratios():
    m1 = ImageMetadata(filename="img1.png", format="PNG", width=800, height=400, channels=3, datatype="RGB")
    m2 = ImageMetadata(filename="img2.png", format="PNG", width=400, height=800, channels=3, datatype="RGB")

    res = SpatialChecker.check_spatial_compatibility([m1, m2])
    assert res.is_compatible is False
    assert "Aspect ratios differ" in res.details

def test_temporal_checker_distinct_dates():
    m1 = ImageMetadata(filename="t1.tif", format="TIFF", width=512, height=512, channels=3, datatype="RGB", acquisition_date="2022-01-10")
    m2 = ImageMetadata(filename="t2.tif", format="TIFF", width=512, height=512, channels=3, datatype="RGB", acquisition_date="2023-01-10")

    res = TemporalChecker.check_temporal_compatibility([m1, m2])
    assert res.is_compatible is True
    assert res.has_distinct_dates is True

def test_temporal_checker_identical_dates():
    m1 = ImageMetadata(filename="t1.tif", format="TIFF", width=512, height=512, channels=3, datatype="RGB", acquisition_date="2022-01-10")
    m2 = ImageMetadata(filename="t2.tif", format="TIFF", width=512, height=512, channels=3, datatype="RGB", acquisition_date="2022-01-10")

    res = TemporalChecker.check_temporal_compatibility([m1, m2])
    assert res.is_compatible is False
    assert "identical timestamp" in res.details

def test_modality_inference_sar_by_name():
    m = ImageMetadata(filename="s1_grd_vv.tif", format="TIFF", width=512, height=512, channels=1, datatype="Grayscale")
    mod = ModalityChecker.infer_modality("s1_grd_vv.tif", m)
    assert mod == ModalityType.SAR

def test_modality_inference_optical_by_channels():
    m = ImageMetadata(filename="sentinel2_image.png", format="PNG", width=512, height=512, channels=3, datatype="RGB")
    mod = ModalityChecker.infer_modality("sentinel2_image.png", m)
    assert mod == ModalityType.OPTICAL

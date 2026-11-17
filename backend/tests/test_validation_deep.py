# backend/tests/test_validation_deep.py
import pytest
import os
import tempfile
from PIL import Image
from backend.services.input_validator import InputValidator

def test_validation_single_image_mode_valid():
    """Verify single image mode validation with a valid PNG."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (256, 256), color=(50, 100, 150))
        img.save(f.name)
        f_path = f.name

    try:
        val = InputValidator.validate_saved_files(
            file_paths=[f_path],
            question="What objects and land-cover types are visible?",
            input_mode="SINGLE_IMAGE"
        )
        assert val.is_valid is True
        assert len(val.images) == 1
        assert val.images[0].width == 256
        assert val.images[0].height == 256
        assert val.images[0].channels == 3
        assert len(val.blocking_errors) == 0
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)

def test_validation_double_image_mode_missing_image():
    """Verify double image mode rejects single image upload."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (256, 256), color=(50, 100, 150))
        img.save(f.name)
        f_path = f.name

    try:
        val = InputValidator.validate_saved_files(
            file_paths=[f_path],
            question="What changes occurred between these two images?",
            input_mode="DOUBLE_IMAGE"
        )
        assert val.is_valid is False
        assert any("Double Image mode requires exactly 2 images" in err for err in val.blocking_errors)
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)

def test_validation_bitemporal_dimension_mismatch_warning():
    """Verify spatial alignment check issues warning when bi-temporal dimensions differ."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f1, tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f2:
        img1 = Image.new("RGB", (256, 256), color=(10, 20, 30))
        img2 = Image.new("RGB", (512, 512), color=(40, 50, 60))
        img1.save(f1.name)
        img2.save(f2.name)
        p1, p2 = f1.name, f2.name

    try:
        val = InputValidator.validate_saved_files(
            file_paths=[p1, p2],
            question="What changes occurred between these two images?",
            input_mode="DOUBLE_IMAGE",
            relationship="BI_TEMPORAL"
        )
        assert val.spatial_aligned is False
        assert any("Dimension variance" in w or "Spatial mismatch" in w for w in val.warnings)
    finally:
        for p in (p1, p2):
            if os.path.exists(p):
                os.remove(p)

def test_validation_optical_sar_rgb_warning():
    """Verify optical-sar check warns when ordinary RGB pair is supplied without SAR backscatter."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f1, tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f2:
        img1 = Image.new("RGB", (256, 256), color=(100, 150, 200))
        img2 = Image.new("RGB", (256, 256), color=(120, 170, 220))
        img1.save(f1.name)
        img2.save(f2.name)
        p1, p2 = f1.name, f2.name

    try:
        val = InputValidator.validate_saved_files(
            file_paths=[p1, p2],
            question="Compare structural information",
            input_mode="DOUBLE_IMAGE",
            relationship="OPTICAL_SAR"
        )
        assert val.modality_compatible is False
        assert any("Optical-SAR Modality Alert" in w for w in val.warnings)
    finally:
        for p in (p1, p2):
            if os.path.exists(p):
                os.remove(p)

def test_validation_empty_query():
    """Verify query validation flags empty question."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (100, 100))
        img.save(f.name)
        p = f.name

    try:
        val = InputValidator.validate_saved_files(
            file_paths=[p],
            question="",
            input_mode="SINGLE_IMAGE"
        )
        assert val.is_valid is False
        assert any("Question is required" in err for err in val.blocking_errors)
    finally:
        if os.path.exists(p):
            os.remove(p)

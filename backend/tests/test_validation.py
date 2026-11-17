# backend/tests/test_validation.py
import pytest
import os
import tempfile
from PIL import Image
from backend.services.compatibility.format_checker import FormatChecker
from backend.services.input_validator import InputValidator

def test_format_checker_valid_png():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGB", (100, 100), color=(73, 109, 137))
        img.save(f.name)
        tmp_name = f.name

    try:
        is_valid, fmt, err = FormatChecker.validate_file(tmp_name)
        assert is_valid is True
        assert fmt == "PNG"
        assert err is None
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

def test_format_checker_unsupported_extension():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"not an image")
        tmp_name = f.name

    try:
        is_valid, fmt, err = FormatChecker.validate_file(tmp_name)
        assert is_valid is False
        assert "Unsupported file extension" in err
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)

def test_format_checker_nonexistent_file():
    is_valid, fmt, err = FormatChecker.validate_file("c:/nonexistent/path/file.png")
    assert is_valid is False
    assert "File not found" in err

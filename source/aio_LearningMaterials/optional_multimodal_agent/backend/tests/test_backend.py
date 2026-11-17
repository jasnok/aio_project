import io

import pytest
from PIL import Image
from pydantic import ValidationError

from backend.app.core.media_validation import validate
from backend.app.schemas import AdditionalInput, RunRequest


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (12, 12)).save(buffer, "PNG")
    return buffer.getvalue()


def test_image_validation_accepts_png_and_rejects_text():
    assert validate(png_bytes(), "image") == ".png"
    with pytest.raises(ValueError):
        validate(b"not an image", "image")


def test_run_schema_rejects_unknown_agent_and_blank_followup():
    with pytest.raises(ValidationError):
        RunRequest(agent="unknown", image_id="image.png")
    with pytest.raises(ValidationError):
        AdditionalInput(question="")

from pathlib import Path

import pytest

from ai_comp.domain.materials import MaterialFormat, MaterialInput, MaterialSource
from ai_comp.material.processing import MaterialProcessor


class FakeOCR:
    def __init__(self, text: str):
        self.text = text
        self.calls = []

    def extract_text(self, content, document_format):
        self.calls.append(document_format)
        return self.text


def test_text_note_becomes_normalized_material(tmp_path: Path):
    processor = MaterialProcessor(tmp_path)

    result = processor.process(
        MaterialProcessor.from_note(
            "  राजस्थान   का   सबसे बड़ा जिला कौन सा है?  ",
        )
    )

    assert result.source is MaterialSource.USER_NOTE
    assert result.format is MaterialFormat.TEXT
    assert result.text == "राजस्थान का सबसे बड़ा जिला कौन सा है?"
    assert result.extraction_method == "DIRECT_TEXT"
    assert len(result.sha256) == 64
    assert result.storage_key


def test_image_material_uses_injected_ocr(tmp_path: Path):
    ocr = FakeOCR("भारत की राजधानी नई दिल्ली है।")
    processor = MaterialProcessor(tmp_path, ocr=ocr)

    result = processor.process(
        MaterialInput(
            filename="notes.png",
            content_type="image/png",
            content=b"\x89PNG\r\n\x1a\nmaterial",
        )
    )

    assert result.format is MaterialFormat.IMAGE
    assert result.text == "भारत की राजधानी नई दिल्ली है।"
    assert result.extraction_method == "OCR"
    assert result.warnings == ()
    assert len(ocr.calls) == 1


def test_same_bytes_are_content_deduplicated(tmp_path: Path):
    processor = MaterialProcessor(tmp_path)
    material = MaterialProcessor.from_note(
        "भारत का संविधान",
        filename="a.txt",
    )

    first = processor.process(material)
    second = processor.process(
        MaterialInput(
            filename="different-name.txt",
            content=material.content,
            content_type=material.content_type,
        )
    )

    assert first.material_id == second.material_id
    assert first.sha256 == second.sha256
    assert first.storage_key == second.storage_key
    assert len(list(tmp_path.glob("*"))) == 2
    assert len(list(tmp_path.glob("metadata/*"))) == 1


def test_empty_note_is_rejected(tmp_path: Path):
    processor = MaterialProcessor(tmp_path)

    with pytest.raises(ValueError, match="note text must not be empty"):
        processor.from_note("   ")


def test_unknown_binary_material_is_preserved_but_not_falsely_understood(tmp_path: Path):
    processor = MaterialProcessor(tmp_path)

    result = processor.process(
        MaterialInput(
            filename="unknown.bin",
            content_type="application/octet-stream",
            content=b"binary-data",
        )
    )

    assert result.format is MaterialFormat.UNKNOWN
    assert result.text == ""
    assert result.warnings == (
        "no usable text was extracted; content-understanding cannot proceed",
    )

"""Tests para reader/dimension_detector.py — detección de cotas existentes."""

from pathlib import Path

import ezdxf
import pytest

from cad_copilot.reader.dimension_detector import detect_dimensions
from cad_copilot.schemas.detection import DetectedDimension

SAMPLE_DXF = Path(__file__).parent.parent.parent / "samples" / "Figueroa.dxf"


class TestDetectDimensions:
    @pytest.fixture
    def doc_with_dims(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Cota horizontal
        msp.add_aligned_dim(
            p1=(0, 0), p2=(5, 0), distance=0.5
        ).render()

        # Cota vertical
        msp.add_aligned_dim(
            p1=(0, 0), p2=(0, 3), distance=0.5
        ).render()

        return doc

    def test_detects_dimensions(self, doc_with_dims):
        dims = detect_dimensions(doc_with_dims)
        assert len(dims) == 2

    def test_dimension_type(self, doc_with_dims):
        dims = detect_dimensions(doc_with_dims)
        assert all(isinstance(d, DetectedDimension) for d in dims)

    def test_sequential_ids(self, doc_with_dims):
        dims = detect_dimensions(doc_with_dims)
        assert dims[0].id == "dim_0"
        assert dims[1].id == "dim_1"

    def test_dimension_has_layer(self, doc_with_dims):
        dims = detect_dimensions(doc_with_dims)
        for d in dims:
            assert isinstance(d.layer, str)

    def test_empty_dxf(self):
        doc = ezdxf.new("R2013")
        dims = detect_dimensions(doc)
        assert len(dims) == 0


@pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample DXF not available")
class TestDetectDimensionsFigueroa:
    @pytest.fixture(scope="class")
    def doc(self):
        return ezdxf.readfile(str(SAMPLE_DXF))

    def test_detects_dimensions(self, doc):
        dims = detect_dimensions(doc)
        assert len(dims) >= 100  # Figueroa has 162 DIMENSION entities

    def test_dimensions_have_values(self, doc):
        dims = detect_dimensions(doc)
        with_values = [d for d in dims if d.value > 0]
        assert len(with_values) > 50

    def test_dimensions_have_layers(self, doc):
        dims = detect_dimensions(doc)
        for d in dims:
            assert d.layer != ""

    def test_dimensions_have_handles(self, doc):
        dims = detect_dimensions(doc)
        for d in dims:
            assert d.entity_handle != ""

"""Tests para documenter/norm_compliance.py — tabla normativa."""

import ezdxf
import pytest

from cad_copilot.documenter.norm_compliance import (
    _detected_spaces_to_schema,
    add_norm_table_to_layout,
    calculate_norms_from_detected,
)
from cad_copilot.schemas.detection import DetectedSpace, SpaceCategory
from cad_copilot.standards.norms import ResultadoNormas


class TestDetectedSpacesToSchema:
    def test_converts_spaces(self):
        spaces = [
            DetectedSpace(id="s0", name="Cocina", category=SpaceCategory.cocina, area=8.0),
            DetectedSpace(id="s1", name="Dormitorio", category=SpaceCategory.dormitorio, area=12.0),
        ]
        schema_spaces, schema_walls = _detected_spaces_to_schema(spaces)
        assert len(schema_spaces) == 2
        assert len(schema_walls) == 2

    def test_skips_zero_area(self):
        spaces = [
            DetectedSpace(id="s0", name="Cocina", category=SpaceCategory.cocina, area=0.0),
        ]
        schema_spaces, _ = _detected_spaces_to_schema(spaces)
        assert len(schema_spaces) == 0

    def test_preserves_ids(self):
        spaces = [
            DetectedSpace(id="s0", name="Baño", category=SpaceCategory.bano, area=4.0),
        ]
        schema_spaces, _ = _detected_spaces_to_schema(spaces)
        assert schema_spaces[0].id == "s0"


class TestCalculateNormsFromDetected:
    def test_with_spaces(self):
        spaces = [
            DetectedSpace(id="s0", name="Cocina", category=SpaceCategory.cocina, area=8.0),
        ]
        result = calculate_norms_from_detected(spaces, "Test")
        assert isinstance(result, ResultadoNormas)
        assert result.proyecto == "Test"

    def test_no_spaces(self):
        result = calculate_norms_from_detected([], "Test")
        assert result is None

    def test_no_area_spaces(self):
        spaces = [DetectedSpace(id="s0", name="X", area=0.0)]
        result = calculate_norms_from_detected(spaces)
        assert result is None


class TestAddNormTableToLayout:
    def test_adds_table(self):
        doc = ezdxf.new("R2013")
        layout = doc.layouts.new("Test")

        spaces = [
            DetectedSpace(id="s0", name="Cocina", category=SpaceCategory.cocina, area=8.0),
        ]
        resultado = calculate_norms_from_detected(spaces, "Proyecto Test")
        assert resultado is not None

        add_norm_table_to_layout(doc, layout, resultado)

        # Verify entities were added to layout
        entities = list(layout)
        # Should have MTEXT and LWPOLYLINE for cells
        types = {e.dxftype() for e in entities}
        assert "MTEXT" in types or "LWPOLYLINE" in types

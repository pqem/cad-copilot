"""Tests para documenter/auto_dimensions.py — cotas automáticas."""

import ezdxf
import pytest

from cad_copilot.documenter.auto_dimensions import add_missing_dimensions
from cad_copilot.schemas.detection import DetectedDimension, DetectedWall


class TestAddMissingDimensions:
    @pytest.fixture
    def doc(self):
        return ezdxf.new("R2013")

    def test_adds_dimension_to_wall(self, doc):
        walls = [DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0)]
        count = add_missing_dimensions(doc, walls, [])
        assert count == 1

    def test_skips_already_dimensioned(self, doc):
        walls = [DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0)]
        dims = [DetectedDimension(id="d0", value=5.0, start=(0, 0.5), end=(5, 0.5))]
        count = add_missing_dimensions(doc, walls, dims)
        assert count == 0

    def test_skips_short_walls(self, doc):
        walls = [DetectedWall(id="w0", start=(0, 0), end=(0.3, 0), length=0.3)]
        count = add_missing_dimensions(doc, walls, [])
        assert count == 0

    def test_multiple_walls(self, doc):
        walls = [
            DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0),
            DetectedWall(id="w1", start=(0, 0), end=(0, 3), length=3.0),
            DetectedWall(id="w2", start=(0, 0), end=(0.2, 0), length=0.2),  # too short
        ]
        count = add_missing_dimensions(doc, walls, [])
        assert count == 2

    def test_creates_iram_dimstyle(self, doc):
        walls = [DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0)]
        add_missing_dimensions(doc, walls, [])
        dimstyle_names = [ds.dxf.name for ds in doc.dimstyles]
        assert "IRAM_ARQ" in dimstyle_names

    def test_creates_layers(self, doc):
        walls = [DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0)]
        add_missing_dimensions(doc, walls, [])
        layer_names = [l.dxf.name for l in doc.layers]
        assert "A-ANNO-DIMS" in layer_names

    def test_empty_walls(self, doc):
        count = add_missing_dimensions(doc, [], [])
        assert count == 0

    def test_dimension_entity_created(self, doc):
        walls = [DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0)]
        add_missing_dimensions(doc, walls, [])
        msp = doc.modelspace()
        dims = [e for e in msp if e.dxftype() == "DIMENSION"]
        assert len(dims) == 1

"""Tests para reader/wall_detector.py — detección de muros."""

import math
from pathlib import Path

import ezdxf
import pytest

from cad_copilot.reader.wall_detector import (
    MIN_WALL_LENGTH,
    MIN_WALL_THICKNESS,
    _Line,
    _distance_point_to_line,
    _lines_overlap_projection,
    _should_skip_layer,
    detect_walls,
)
from cad_copilot.schemas.detection import DetectedWall

SAMPLE_DXF = Path(__file__).parent.parent.parent / "samples" / "Figueroa.dxf"


# --- Helpers ---


class TestShouldSkipLayer:
    def test_skip_cotas(self):
        assert _should_skip_layer("COTAS") is True

    def test_skip_texto(self):
        assert _should_skip_layer("Textos") is True

    def test_skip_caratula(self):
        assert _should_skip_layer("Caratula") is True

    def test_skip_defpoints(self):
        assert _should_skip_layer("Defpoints") is True

    def test_skip_hatch(self):
        assert _should_skip_layer("E_HATCH") is True

    def test_keep_numeric_layer(self):
        assert _should_skip_layer("0.15") is False

    def test_keep_wall_layer(self):
        assert _should_skip_layer("A-WALL") is False


class TestDistancePointToLine:
    def test_point_on_line(self):
        assert _distance_point_to_line(5, 0, 0, 0, 10, 0) == pytest.approx(0.0)

    def test_perpendicular_distance(self):
        assert _distance_point_to_line(5, 3, 0, 0, 10, 0) == pytest.approx(3.0)

    def test_distance_to_endpoint(self):
        dist = _distance_point_to_line(0, 1, 0, 0, 10, 0)
        assert dist == pytest.approx(1.0)


class TestLinesOverlapProjection:
    def test_full_overlap(self):
        a = _Line(0, 0, 10, 0, "L", "h1")
        b = _Line(0, 1, 10, 1, "L", "h2")
        assert _lines_overlap_projection(a, b) == pytest.approx(10.0)

    def test_partial_overlap(self):
        a = _Line(0, 0, 10, 0, "L", "h1")
        b = _Line(5, 1, 15, 1, "L", "h2")
        assert _lines_overlap_projection(a, b) == pytest.approx(5.0)

    def test_no_overlap(self):
        a = _Line(0, 0, 5, 0, "L", "h1")
        b = _Line(6, 1, 10, 1, "L", "h2")
        assert _lines_overlap_projection(a, b) == pytest.approx(0.0)


# --- Detección con DXF sintético ---


class TestDetectWallsParallelLines:
    @pytest.fixture
    def doc_with_wall_lines(self):
        """DXF con un par de líneas paralelas que forman un muro."""
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        doc.layers.add("MUROS", color=1)

        # Muro horizontal: 2 líneas paralelas separadas 0.15m
        msp.add_line((0, 0), (5, 0), dxfattribs={"layer": "MUROS"})
        msp.add_line((0, 0.15), (5, 0.15), dxfattribs={"layer": "MUROS"})

        return doc

    def test_detects_parallel_wall(self, doc_with_wall_lines):
        walls = detect_walls(
            doc_with_wall_lines, include_polylines=False, include_line_pairs=True
        )
        assert len(walls) >= 1
        wall = walls[0]
        assert isinstance(wall, DetectedWall)
        assert wall.thickness == pytest.approx(0.15, abs=0.01)
        assert wall.length > 4.0

    def test_wall_has_two_handles(self, doc_with_wall_lines):
        walls = detect_walls(
            doc_with_wall_lines, include_polylines=False, include_line_pairs=True
        )
        assert len(walls[0].entity_handles) == 2

    def test_wall_center_axis(self, doc_with_wall_lines):
        walls = detect_walls(
            doc_with_wall_lines, include_polylines=False, include_line_pairs=True
        )
        wall = walls[0]
        # El eje central debe estar a y=0.075
        avg_y = (wall.start[1] + wall.end[1]) / 2
        assert avg_y == pytest.approx(0.075, abs=0.02)


class TestDetectWallsPolyline:
    @pytest.fixture
    def doc_with_wall_polyline(self):
        """DXF con un LWPOLYLINE rectangular que representa un muro."""
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        doc.layers.add("MUROS", color=1)

        # Muro como rectángulo: 5m x 0.15m
        msp.add_lwpolyline(
            [(0, 0), (5, 0), (5, 0.15), (0, 0.15)],
            close=True,
            dxfattribs={"layer": "MUROS"},
        )

        return doc

    def test_detects_rectangular_polyline(self, doc_with_wall_polyline):
        walls = detect_walls(
            doc_with_wall_polyline, include_polylines=True, include_line_pairs=False
        )
        assert len(walls) >= 1

    def test_wall_thickness_from_polyline(self, doc_with_wall_polyline):
        walls = detect_walls(
            doc_with_wall_polyline, include_polylines=True, include_line_pairs=False
        )
        wall = walls[0]
        assert wall.thickness == pytest.approx(0.15, abs=0.01)

    def test_wall_length_from_polyline(self, doc_with_wall_polyline):
        walls = detect_walls(
            doc_with_wall_polyline, include_polylines=True, include_line_pairs=False
        )
        wall = walls[0]
        assert wall.length == pytest.approx(5.0, abs=0.1)


class TestDetectWallsFiltering:
    def test_ignores_short_lines(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Líneas demasiado cortas
        msp.add_line((0, 0), (0.1, 0))
        msp.add_line((0, 0.15), (0.1, 0.15))

        walls = detect_walls(doc, include_polylines=False, include_line_pairs=True)
        assert len(walls) == 0

    def test_ignores_non_parallel_lines(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Líneas no paralelas
        msp.add_line((0, 0), (5, 0))
        msp.add_line((0, 0.15), (5, 1))

        walls = detect_walls(doc, include_polylines=False, include_line_pairs=True)
        assert len(walls) == 0

    def test_ignores_lines_too_far_apart(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Líneas paralelas pero demasiado separadas (>0.60m)
        msp.add_line((0, 0), (5, 0))
        msp.add_line((0, 1.0), (5, 1.0))

        walls = detect_walls(doc, include_polylines=False, include_line_pairs=True)
        assert len(walls) == 0

    def test_ignores_non_rectangular_polyline(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Polígono con 6 vértices (no rectangular)
        msp.add_lwpolyline(
            [(0, 0), (3, 0), (3, 1), (2, 1), (2, 2), (0, 2)],
            close=True,
        )

        walls = detect_walls(doc, include_polylines=True, include_line_pairs=False)
        assert len(walls) == 0

    def test_ignores_square_polyline(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Cuadrado 0.15 x 0.15 (proporción < 2.0)
        msp.add_lwpolyline(
            [(0, 0), (0.15, 0), (0.15, 0.15), (0, 0.15)],
            close=True,
        )

        walls = detect_walls(doc, include_polylines=True, include_line_pairs=False)
        assert len(walls) == 0

    def test_skips_excluded_layers(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        doc.layers.add("COTAS", color=1)

        msp.add_line((0, 0), (5, 0), dxfattribs={"layer": "COTAS"})
        msp.add_line((0, 0.15), (5, 0.15), dxfattribs={"layer": "COTAS"})

        walls = detect_walls(doc, include_polylines=False, include_line_pairs=True)
        assert len(walls) == 0

    def test_layer_filter(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        doc.layers.add("MUROS", color=1)
        doc.layers.add("OTHER", color=2)

        # Muro en MUROS
        msp.add_line((0, 0), (5, 0), dxfattribs={"layer": "MUROS"})
        msp.add_line((0, 0.15), (5, 0.15), dxfattribs={"layer": "MUROS"})

        # Muro en OTHER
        msp.add_line((0, 2), (5, 2), dxfattribs={"layer": "OTHER"})
        msp.add_line((0, 2.15), (5, 2.15), dxfattribs={"layer": "OTHER"})

        walls = detect_walls(
            doc, layers=["MUROS"], include_polylines=False, include_line_pairs=True
        )
        assert len(walls) == 1
        assert walls[0].layer == "MUROS"


class TestDetectWallsVertical:
    def test_detects_vertical_wall(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Muro vertical
        msp.add_line((0, 0), (0, 5))
        msp.add_line((0.20, 0), (0.20, 5))

        walls = detect_walls(doc, include_polylines=False, include_line_pairs=True)
        assert len(walls) >= 1
        assert walls[0].thickness == pytest.approx(0.20, abs=0.01)

    def test_detects_angled_wall(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Muro a 45 grados
        msp.add_line((0, 0), (5, 5))
        d = 0.15 / math.sqrt(2)
        msp.add_line((d, -d), (5 + d, 5 - d))

        walls = detect_walls(doc, include_polylines=False, include_line_pairs=True)
        assert len(walls) >= 1
        assert walls[0].thickness == pytest.approx(0.15, abs=0.02)


class TestDetectWallsMultiple:
    def test_detects_multiple_walls(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Muro 1 (horizontal)
        msp.add_line((0, 0), (5, 0))
        msp.add_line((0, 0.15), (5, 0.15))

        # Muro 2 (vertical, bien separado)
        msp.add_line((10, 0), (10, 5))
        msp.add_line((10.20, 0), (10.20, 5))

        walls = detect_walls(doc, include_polylines=False, include_line_pairs=True)
        assert len(walls) == 2
        thicknesses = sorted([w.thickness for w in walls])
        assert thicknesses[0] == pytest.approx(0.15, abs=0.01)
        assert thicknesses[1] == pytest.approx(0.20, abs=0.01)


class TestDetectWallsIds:
    def test_sequential_ids(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        msp.add_line((0, 0), (5, 0))
        msp.add_line((0, 0.15), (5, 0.15))
        msp.add_lwpolyline(
            [(10, 0), (15, 0), (15, 0.15), (10, 0.15)], close=True
        )

        walls = detect_walls(doc)
        ids = [w.id for w in walls]
        assert ids == [f"wall_{i}" for i in range(len(walls))]


# --- Test con Figueroa.dxf ---


@pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample DXF not available")
class TestDetectWallsFigueroa:
    @pytest.fixture(scope="class")
    def doc(self):
        return ezdxf.readfile(str(SAMPLE_DXF))

    def test_detects_some_walls(self, doc):
        """El detector debe encontrar al menos algunos muros en el plano real."""
        walls = detect_walls(doc)
        assert len(walls) > 0

    def test_wall_thicknesses_reasonable(self, doc):
        """Los espesores detectados deben estar en rango razonable."""
        walls = detect_walls(doc)
        for wall in walls:
            assert MIN_WALL_THICKNESS <= wall.thickness <= 0.60

    def test_wall_lengths_positive(self, doc):
        """Las longitudes deben ser positivas."""
        walls = detect_walls(doc)
        for wall in walls:
            assert wall.length > 0

    def test_walls_have_layers(self, doc):
        walls = detect_walls(doc)
        for wall in walls:
            assert wall.layer != ""

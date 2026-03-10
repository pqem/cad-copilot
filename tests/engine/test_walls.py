"""Tests para engine/walls.py — _perpendicular_offset, draw_wall, draw_walls."""

import pytest
import math

from cad_copilot.engine.walls import _perpendicular_offset, _get_hatch_pattern, draw_wall, draw_walls
from cad_copilot.schemas.wall import Wall, WallClassification


class TestPerpendicularOffset:
    def test_horizontal_wall_returns_4_vertices(self):
        verts = _perpendicular_offset((0, 0), (6, 0), 0.30)
        assert len(verts) == 4

    def test_horizontal_wall_vertices(self):
        verts = _perpendicular_offset((0, 0), (4, 0), 0.20)
        # p1 y p2 en la línea del muro
        assert verts[0] == pytest.approx((0, 0))
        assert verts[1] == pytest.approx((4, 0))
        # p3 y p4 desplazados en Y+ (perpendicular izquierda de X+)
        assert verts[2] == pytest.approx((4, 0.20))
        assert verts[3] == pytest.approx((0, 0.20))

    def test_vertical_wall_vertices(self):
        verts = _perpendicular_offset((0, 0), (0, 4), 0.20)
        assert verts[0] == pytest.approx((0, 0))
        assert verts[1] == pytest.approx((0, 4))
        # Perpendicular izquierda de Y+ es X-
        assert verts[2] == pytest.approx((-0.20, 4))
        assert verts[3] == pytest.approx((-0.20, 0))

    def test_zero_length_wall_returns_empty(self):
        verts = _perpendicular_offset((2, 3), (2, 3), 0.15)
        assert verts == []

    def test_diagonal_wall_returns_4_vertices(self):
        verts = _perpendicular_offset((0, 0), (3, 4), 0.15)
        assert len(verts) == 4

    def test_perpendicular_distance_is_correct(self):
        """La distancia entre p1 y p4 debe ser igual al espesor."""
        verts = _perpendicular_offset((0, 0), (6, 0), 0.30)
        dist = math.hypot(verts[3][0] - verts[0][0], verts[3][1] - verts[0][1])
        assert dist == pytest.approx(0.30)


class TestGetHatchPattern:
    def test_exterior_portante_returns_solid(self):
        p = _get_hatch_pattern(WallClassification.exterior_portante)
        assert p == "SOLID"

    def test_medianera_returns_ansi31(self):
        p = _get_hatch_pattern(WallClassification.medianera)
        assert p == "ANSI31"

    def test_interior_returns_none(self):
        p = _get_hatch_pattern(WallClassification.interior)
        assert p is None

    def test_tabique_returns_none(self):
        p = _get_hatch_pattern(WallClassification.tabique)
        assert p is None


class TestDrawWall:
    def test_draws_lwpolyline_on_awall(self, doc, msp):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30)
        draw_wall(msp, wall)
        polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-WALL"]
        assert len(polylines) == 1

    def test_exterior_wall_has_hatch(self, doc, msp):
        wall = Wall(
            id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30,
            classification=WallClassification.exterior_portante,
        )
        draw_wall(msp, wall)
        hatches = [e for e in msp if e.dxftype() == "HATCH" and e.dxf.layer == "A-WALL-PATT"]
        assert len(hatches) == 1

    def test_interior_wall_no_hatch(self, doc, msp):
        wall = Wall(
            id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.15,
            classification=WallClassification.interior,
        )
        draw_wall(msp, wall)
        hatches = [e for e in msp if e.dxftype() == "HATCH" and e.dxf.layer == "A-WALL-PATT"]
        assert len(hatches) == 0

    def test_zero_length_wall_skipped(self, doc, msp):
        wall = Wall(id="W1", start=(2.0, 2.0), end=(2.0, 2.0), thickness=0.15)
        draw_wall(msp, wall)
        polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
        assert len(polylines) == 0

    def test_polyline_is_closed(self, doc, msp):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30)
        draw_wall(msp, wall)
        polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
        assert polylines[0].closed is True


class TestDrawWalls:
    def test_draws_multiple_walls(self, doc, msp, four_walls):
        draw_walls(msp, four_walls)
        polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-WALL"]
        assert len(polylines) == 4

    def test_empty_list_no_error(self, doc, msp):
        draw_walls(msp, [])
        polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE"]
        assert len(polylines) == 0

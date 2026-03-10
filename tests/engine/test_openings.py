"""Tests para engine/openings.py — _get_wall_angle, _position_on_wall, draw_opening, draw_openings."""

import pytest
import math

from cad_copilot.engine.openings import (
    _get_wall_angle,
    _get_wall_length,
    _position_on_wall,
    draw_opening,
    draw_openings,
)
from cad_copilot.schemas.wall import Wall, WallClassification
from cad_copilot.schemas.opening import Opening, OpeningType, OpeningMechanism


class TestGetWallAngle:
    def test_horizontal_wall_angle_0(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0))
        angle = _get_wall_angle(wall)
        assert angle == pytest.approx(0.0)

    def test_vertical_wall_angle_90(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(0.0, 4.0))
        angle = _get_wall_angle(wall)
        assert angle == pytest.approx(90.0)

    def test_wall_pointing_left_angle_180(self):
        wall = Wall(id="W1", start=(6.0, 0.0), end=(0.0, 0.0))
        angle = _get_wall_angle(wall)
        assert angle == pytest.approx(180.0)

    def test_diagonal_wall_angle_45(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(1.0, 1.0))
        angle = _get_wall_angle(wall)
        assert angle == pytest.approx(45.0)


class TestGetWallLength:
    def test_horizontal_wall_6m(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0))
        assert _get_wall_length(wall) == pytest.approx(6.0)

    def test_vertical_wall_4m(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(0.0, 4.0))
        assert _get_wall_length(wall) == pytest.approx(4.0)

    def test_diagonal_3_4_5(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(3.0, 4.0))
        assert _get_wall_length(wall) == pytest.approx(5.0)

    def test_zero_length(self):
        wall = Wall(id="W1", start=(2.0, 2.0), end=(2.0, 2.0))
        assert _get_wall_length(wall) == pytest.approx(0.0)


class TestPositionOnWall:
    def test_horizontal_wall_midpoint(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0))
        pos = _position_on_wall(wall, 3.0)
        assert pos == pytest.approx((3.0, 0.0))

    def test_horizontal_wall_start(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0))
        pos = _position_on_wall(wall, 0.0)
        assert pos == pytest.approx((0.0, 0.0))

    def test_horizontal_wall_end(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0))
        pos = _position_on_wall(wall, 6.0)
        assert pos == pytest.approx((6.0, 0.0))

    def test_vertical_wall_quarter(self):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(0.0, 4.0))
        pos = _position_on_wall(wall, 1.0)
        assert pos == pytest.approx((0.0, 1.0))

    def test_zero_length_returns_start(self):
        wall = Wall(id="W1", start=(2.0, 3.0), end=(2.0, 3.0))
        pos = _position_on_wall(wall, 0.0)
        assert pos == wall.start


class TestDrawOpening:
    def test_hinged_door_inserts_block(self, doc, msp):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30)
        opening = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        draw_opening(doc, msp, wall, opening)
        inserts = [e for e in msp if e.dxftype() == "INSERT"]
        assert len(inserts) == 1

    def test_door_block_on_adoor_layer(self, doc, msp):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30)
        opening = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        draw_opening(doc, msp, wall, opening)
        inserts = [e for e in msp if e.dxftype() == "INSERT"]
        assert inserts[0].dxf.layer == "A-DOOR"

    def test_window_block_on_aglaz_layer(self, doc, msp):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30)
        opening = Opening(type=OpeningType.window, width=1.20, position_along_wall=2.0)
        draw_opening(doc, msp, wall, opening)
        inserts = [e for e in msp if e.dxftype() == "INSERT"]
        assert inserts[0].dxf.layer == "A-GLAZ"

    def test_door_block_rotation_matches_wall_angle(self, doc, msp):
        # Muro vertical → ángulo 90°
        wall = Wall(id="W1", start=(0.0, 0.0), end=(0.0, 4.0), thickness=0.15)
        opening = Opening(type=OpeningType.door, width=0.80, position_along_wall=1.0)
        draw_opening(doc, msp, wall, opening)
        inserts = [e for e in msp if e.dxftype() == "INSERT"]
        assert inserts[0].dxf.rotation == pytest.approx(90.0)

    def test_door_insert_position_on_wall(self, doc, msp):
        wall = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30)
        opening = Opening(type=OpeningType.door, width=0.90, position_along_wall=2.0)
        draw_opening(doc, msp, wall, opening)
        inserts = [e for e in msp if e.dxftype() == "INSERT"]
        # Posición debe estar en x=2.0, y=0.0
        assert inserts[0].dxf.insert[0] == pytest.approx(2.0)
        assert inserts[0].dxf.insert[1] == pytest.approx(0.0)


class TestDrawOpenings:
    def test_draws_all_openings_for_all_walls(self, doc, msp):
        walls = [
            Wall(
                id="W1",
                start=(0.0, 0.0),
                end=(6.0, 0.0),
                thickness=0.30,
                openings=[
                    Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0),
                    Opening(type=OpeningType.window, width=1.20, position_along_wall=3.0),
                ],
            ),
            Wall(
                id="W2",
                start=(6.0, 0.0),
                end=(6.0, 4.0),
                thickness=0.30,
                openings=[
                    Opening(type=OpeningType.window, width=1.20, position_along_wall=1.0),
                ],
            ),
        ]
        draw_openings(doc, msp, walls)
        inserts = [e for e in msp if e.dxftype() == "INSERT"]
        assert len(inserts) == 3

    def test_no_openings_no_inserts(self, doc, msp, four_walls):
        draw_openings(doc, msp, four_walls)
        inserts = [e for e in msp if e.dxftype() == "INSERT"]
        assert len(inserts) == 0

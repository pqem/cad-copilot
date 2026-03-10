"""Tests para schemas/base.py — Point2D y Unit."""

from cad_copilot.schemas.base import Point2D, Unit


def test_unit_enum_values():
    assert Unit.meters == "meters"
    assert Unit.millimeters == "millimeters"
    assert Unit.centimeters == "centimeters"


def test_point2d_is_tuple():
    point: Point2D = (1.0, 2.5)
    assert point[0] == 1.0
    assert point[1] == 2.5


def test_unit_is_str_enum():
    # StrEnum debe comportarse como string
    assert str(Unit.meters) == "meters"
    assert Unit.meters == "meters"

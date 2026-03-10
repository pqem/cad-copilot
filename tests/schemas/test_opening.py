"""Tests para schemas/opening.py — Opening con defaults condicionales."""

import pytest
from pydantic import ValidationError

from cad_copilot.schemas.opening import Opening, OpeningType, OpeningMechanism


class TestOpeningDefaults:
    def test_door_default_height(self):
        o = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        assert o.height == pytest.approx(2.10)

    def test_door_default_sill_height(self):
        o = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        assert o.sill_height == pytest.approx(0.0)

    def test_door_default_mechanism(self):
        o = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        assert o.mechanism == OpeningMechanism.hinged

    def test_window_default_height(self):
        o = Opening(type=OpeningType.window, width=1.20, position_along_wall=0.5)
        assert o.height == pytest.approx(1.10)

    def test_window_default_sill_height(self):
        o = Opening(type=OpeningType.window, width=1.20, position_along_wall=0.5)
        assert o.sill_height == pytest.approx(0.90)

    def test_window_default_mechanism(self):
        o = Opening(type=OpeningType.window, width=1.20, position_along_wall=0.5)
        assert o.mechanism == OpeningMechanism.sliding


class TestOpeningExplicitValues:
    def test_door_explicit_height_preserved(self):
        o = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0, height=2.00)
        assert o.height == pytest.approx(2.00)

    def test_door_explicit_mechanism_preserved(self):
        o = Opening(
            type=OpeningType.door,
            width=1.60,
            position_along_wall=0.0,
            mechanism=OpeningMechanism.double_hinged,
        )
        assert o.mechanism == OpeningMechanism.double_hinged

    def test_window_explicit_sill_height_preserved(self):
        o = Opening(
            type=OpeningType.window, width=1.0, position_along_wall=0.0, sill_height=1.20
        )
        assert o.sill_height == pytest.approx(1.20)

    def test_window_explicit_mechanism_fixed(self):
        o = Opening(
            type=OpeningType.window,
            width=0.60,
            position_along_wall=0.5,
            mechanism=OpeningMechanism.fixed,
        )
        assert o.mechanism == OpeningMechanism.fixed


class TestOpeningValidation:
    def test_width_must_be_positive(self):
        with pytest.raises(ValidationError):
            Opening(type=OpeningType.door, width=0.0, position_along_wall=1.0)

    def test_width_negative_rejected(self):
        with pytest.raises(ValidationError):
            Opening(type=OpeningType.door, width=-0.5, position_along_wall=1.0)

    def test_position_negative_rejected(self):
        with pytest.raises(ValidationError):
            Opening(type=OpeningType.door, width=0.90, position_along_wall=-1.0)

    def test_position_zero_allowed(self):
        o = Opening(type=OpeningType.door, width=0.90, position_along_wall=0.0)
        assert o.position_along_wall == 0.0

    def test_block_name_optional(self):
        o = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        assert o.block_name is None

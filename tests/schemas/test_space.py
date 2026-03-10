"""Tests para schemas/space.py — Space con auto_id y SpaceFunction."""

import pytest
from pydantic import ValidationError

from cad_copilot.schemas.space import Space, SpaceFunction


class TestSpaceAutoId:
    def test_auto_id_from_name_simple(self):
        s = Space(name="DORMITORIO", function=SpaceFunction.dormitorio, bounded_by=["W1"])
        assert s.id == "dormitorio"

    def test_auto_id_replaces_spaces(self):
        s = Space(name="LIVING COMEDOR", function=SpaceFunction.living, bounded_by=["W1"])
        assert s.id == "living_comedor"

    def test_auto_id_replaces_hyphens(self):
        s = Space(name="LIVING-COMEDOR", function=SpaceFunction.living, bounded_by=["W1"])
        assert s.id == "living_comedor"

    def test_explicit_id_preserved(self):
        s = Space(id="S1", name="COCINA", function=SpaceFunction.cocina, bounded_by=["W1"])
        assert s.id == "S1"

    def test_empty_id_triggers_auto(self):
        s = Space(id="", name="BAÑO", function=SpaceFunction.bano, bounded_by=["W1"])
        assert s.id == "baño"


class TestSpaceFields:
    def test_name_required(self):
        with pytest.raises(ValidationError):
            Space(function=SpaceFunction.dormitorio, bounded_by=["W1"])

    def test_function_required(self):
        with pytest.raises(ValidationError):
            Space(name="DORMITORIO", bounded_by=["W1"])

    def test_bounded_by_required(self):
        with pytest.raises(ValidationError):
            Space(name="DORMITORIO", function=SpaceFunction.dormitorio)

    def test_default_level(self):
        s = Space(name="LIVING", function=SpaceFunction.living, bounded_by=["W1"])
        assert s.level == pytest.approx(0.0)

    def test_custom_level(self):
        s = Space(
            name="SUBSUELO", function=SpaceFunction.deposito, bounded_by=["W1"], level=-3.0
        )
        assert s.level == pytest.approx(-3.0)


class TestSpaceFunctions:
    def test_all_functions_valid(self):
        functions = list(SpaceFunction)
        assert len(functions) == 13

    def test_dormitorio_value(self):
        assert SpaceFunction.dormitorio == "dormitorio"

    def test_bano_value(self):
        assert SpaceFunction.bano == "bano"

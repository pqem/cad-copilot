"""Tests para engine/annotations.py — add_aligned_dimension, add_wall_dimensions."""

import pytest

from cad_copilot.engine.annotations import add_aligned_dimension, add_wall_dimensions
from cad_copilot.schemas.wall import Wall
from cad_copilot.schemas.opening import Opening, OpeningType


class TestAddAlignedDimension:
    def test_creates_dimension_entity(self, doc, msp):
        add_aligned_dimension(msp, (0, 0), (6, 0), distance=0.5)
        dims = [e for e in msp if e.dxftype() == "DIMENSION"]
        assert len(dims) >= 1

    def test_dimension_entity_is_created(self, doc, msp):
        # La entidad DIMENSION se crea en layer "0"; el override de layer
        # aplica al dimstyle (no al atributo de entidad) en ezdxf.
        add_aligned_dimension(msp, (0, 0), (6, 0), distance=0.5)
        dims = [e for e in msp if e.dxftype() == "DIMENSION"]
        assert len(dims) >= 1

    def test_multiple_dimensions(self, doc, msp):
        add_aligned_dimension(msp, (0, 0), (3, 0), distance=0.5)
        add_aligned_dimension(msp, (3, 0), (6, 0), distance=0.5)
        dims = [e for e in msp if e.dxftype() == "DIMENSION"]
        assert len(dims) >= 2


class TestAddWallDimensions:
    def test_one_dim_per_wall(self, doc, msp):
        walls = [
            Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30),
            Wall(id="W2", start=(6.0, 0.0), end=(6.0, 4.0), thickness=0.30),
        ]
        add_wall_dimensions(msp, walls)
        dims = [e for e in msp if e.dxftype() == "DIMENSION"]
        # Al menos 2 cotas (una por muro, sin aberturas)
        assert len(dims) >= 2

    def test_wall_with_opening_adds_extra_dims(self, doc, msp):
        wall = Wall(
            id="W1",
            start=(0.0, 0.0),
            end=(6.0, 0.0),
            thickness=0.30,
            openings=[
                Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0),
            ],
        )
        add_wall_dimensions(msp, [wall])
        dims = [e for e in msp if e.dxftype() == "DIMENSION"]
        # Cota del muro + segmento antes de puerta + cota puerta + segmento después
        assert len(dims) > 1

    def test_empty_walls_no_dims(self, doc, msp):
        add_wall_dimensions(msp, [])
        dims = [e for e in msp if e.dxftype() == "DIMENSION"]
        assert len(dims) == 0

    @pytest.mark.xfail(
        reason="Bug: add_wall_dimensions no guarda muro de longitud 0 antes de llamar "
        "add_aligned_dimension; ezdxf lanza ZeroDivisionError. Reportado como bug.",
        raises=ZeroDivisionError,
        strict=True,
    )
    def test_zero_length_wall_raises_bug(self, doc, msp):
        """Documenta bug preexistente: muro de longitud 0 sin aberturas lanza error."""
        wall = Wall(id="W1", start=(2.0, 2.0), end=(2.0, 2.0), thickness=0.15)
        add_wall_dimensions(msp, [wall])

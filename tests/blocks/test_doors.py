"""Tests para blocks/doors.py — bloques paramétricos de puertas."""

import pytest
import ezdxf

from cad_copilot.blocks.doors import create_hinged_door, create_sliding_door, create_double_door


@pytest.fixture
def fresh_doc():
    return ezdxf.new("R2013", setup=True)


class TestHingedDoor:
    def test_creates_block(self, fresh_doc):
        name = create_hinged_door(fresh_doc, 0.90)
        assert name in fresh_doc.blocks

    def test_name_format_090(self, fresh_doc):
        name = create_hinged_door(fresh_doc, 0.90)
        assert name == "DOOR_HINGED_090"

    def test_name_format_080(self, fresh_doc):
        name = create_hinged_door(fresh_doc, 0.80)
        assert name == "DOOR_HINGED_080"

    def test_name_format_120(self, fresh_doc):
        name = create_hinged_door(fresh_doc, 1.20)
        assert name == "DOOR_HINGED_120"

    def test_block_has_entities(self, fresh_doc):
        name = create_hinged_door(fresh_doc, 0.90)
        block = fresh_doc.blocks[name]
        entities = list(block)
        assert len(entities) > 0

    def test_block_has_arc(self, fresh_doc):
        name = create_hinged_door(fresh_doc, 0.90)
        block = fresh_doc.blocks[name]
        arcs = [e for e in block if e.dxftype() == "ARC"]
        assert len(arcs) >= 1

    def test_arc_radius_equals_width(self, fresh_doc):
        width = 0.90
        name = create_hinged_door(fresh_doc, width)
        block = fresh_doc.blocks[name]
        arcs = [e for e in block if e.dxftype() == "ARC"]
        assert arcs[0].dxf.radius == pytest.approx(width)

    def test_idempotent_returns_same_name(self, fresh_doc):
        name1 = create_hinged_door(fresh_doc, 0.90)
        name2 = create_hinged_door(fresh_doc, 0.90)
        assert name1 == name2

    def test_all_entities_on_layer_0(self, fresh_doc):
        name = create_hinged_door(fresh_doc, 0.90)
        block = fresh_doc.blocks[name]
        for entity in block:
            assert entity.dxf.layer == "0", f"Entidad {entity.dxftype()} no está en layer 0"


class TestSlidingDoor:
    def test_creates_block(self, fresh_doc):
        name = create_sliding_door(fresh_doc, 0.90)
        assert name in fresh_doc.blocks

    def test_name_format(self, fresh_doc):
        name = create_sliding_door(fresh_doc, 0.90)
        assert name == "DOOR_SLIDING_090"

    def test_no_arc_in_sliding_door(self, fresh_doc):
        name = create_sliding_door(fresh_doc, 0.90)
        block = fresh_doc.blocks[name]
        arcs = [e for e in block if e.dxftype() == "ARC"]
        assert len(arcs) == 0

    def test_has_lines(self, fresh_doc):
        name = create_sliding_door(fresh_doc, 0.90)
        block = fresh_doc.blocks[name]
        lines = [e for e in block if e.dxftype() == "LINE"]
        assert len(lines) > 0

    def test_idempotent(self, fresh_doc):
        name1 = create_sliding_door(fresh_doc, 1.20)
        name2 = create_sliding_door(fresh_doc, 1.20)
        assert name1 == name2


class TestDoubleDoor:
    def test_creates_block(self, fresh_doc):
        name = create_double_door(fresh_doc, 1.60)
        assert name in fresh_doc.blocks

    def test_name_format(self, fresh_doc):
        name = create_double_door(fresh_doc, 1.60)
        assert name == "DOOR_DOUBLE_160"

    def test_has_two_arcs(self, fresh_doc):
        name = create_double_door(fresh_doc, 1.60)
        block = fresh_doc.blocks[name]
        arcs = [e for e in block if e.dxftype() == "ARC"]
        assert len(arcs) == 2

    def test_arc_radius_is_half_width(self, fresh_doc):
        width = 1.60
        name = create_double_door(fresh_doc, width)
        block = fresh_doc.blocks[name]
        arcs = [e for e in block if e.dxftype() == "ARC"]
        for arc in arcs:
            assert arc.dxf.radius == pytest.approx(width / 2)

    def test_idempotent(self, fresh_doc):
        name1 = create_double_door(fresh_doc, 1.60)
        name2 = create_double_door(fresh_doc, 1.60)
        assert name1 == name2

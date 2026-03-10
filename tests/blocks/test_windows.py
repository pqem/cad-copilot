"""Tests para blocks/windows.py — bloques paramétricos de ventanas."""

import pytest
import ezdxf

from cad_copilot.blocks.windows import (
    create_sliding_window,
    create_hinged_window,
    create_fixed_window,
)


@pytest.fixture
def fresh_doc():
    return ezdxf.new("R2013", setup=True)


class TestSlidingWindow:
    def test_creates_block(self, fresh_doc):
        name = create_sliding_window(fresh_doc, 1.20)
        assert name in fresh_doc.blocks

    def test_name_format_120(self, fresh_doc):
        name = create_sliding_window(fresh_doc, 1.20)
        assert name == "WIN_SLIDING_120"

    def test_name_format_150(self, fresh_doc):
        name = create_sliding_window(fresh_doc, 1.50)
        assert name == "WIN_SLIDING_150"

    def test_has_5_lines(self, fresh_doc):
        # 2 vidrios + 2 marcos en extremos + 1 división central
        name = create_sliding_window(fresh_doc, 1.20)
        block = fresh_doc.blocks[name]
        lines = [e for e in block if e.dxftype() == "LINE"]
        assert len(lines) == 5

    def test_all_entities_on_layer_0(self, fresh_doc):
        name = create_sliding_window(fresh_doc, 1.20)
        block = fresh_doc.blocks[name]
        for entity in block:
            assert entity.dxf.layer == "0"

    def test_idempotent(self, fresh_doc):
        name1 = create_sliding_window(fresh_doc, 1.20)
        name2 = create_sliding_window(fresh_doc, 1.20)
        assert name1 == name2

    def test_no_arcs(self, fresh_doc):
        name = create_sliding_window(fresh_doc, 1.20)
        block = fresh_doc.blocks[name]
        arcs = [e for e in block if e.dxftype() == "ARC"]
        assert len(arcs) == 0


class TestHingedWindow:
    def test_creates_block(self, fresh_doc):
        name = create_hinged_window(fresh_doc, 1.00)
        assert name in fresh_doc.blocks

    def test_name_format(self, fresh_doc):
        name = create_hinged_window(fresh_doc, 1.00)
        assert name == "WIN_HINGED_100"

    def test_has_6_lines(self, fresh_doc):
        # 2 vidrios + 2 marcos + 2 diagonales de apertura
        name = create_hinged_window(fresh_doc, 1.00)
        block = fresh_doc.blocks[name]
        lines = [e for e in block if e.dxftype() == "LINE"]
        assert len(lines) == 6

    def test_idempotent(self, fresh_doc):
        name1 = create_hinged_window(fresh_doc, 0.80)
        name2 = create_hinged_window(fresh_doc, 0.80)
        assert name1 == name2


class TestFixedWindow:
    def test_creates_block(self, fresh_doc):
        name = create_fixed_window(fresh_doc, 0.60)
        assert name in fresh_doc.blocks

    def test_name_format(self, fresh_doc):
        name = create_fixed_window(fresh_doc, 0.60)
        assert name == "WIN_FIXED_060"

    def test_has_6_lines(self, fresh_doc):
        # 2 vidrios + 2 marcos + 2 diagonales en cruz
        name = create_fixed_window(fresh_doc, 0.60)
        block = fresh_doc.blocks[name]
        lines = [e for e in block if e.dxftype() == "LINE"]
        assert len(lines) == 6

    def test_no_arcs(self, fresh_doc):
        name = create_fixed_window(fresh_doc, 0.60)
        block = fresh_doc.blocks[name]
        arcs = [e for e in block if e.dxftype() == "ARC"]
        assert len(arcs) == 0

    def test_idempotent(self, fresh_doc):
        name1 = create_fixed_window(fresh_doc, 1.50)
        name2 = create_fixed_window(fresh_doc, 1.50)
        assert name1 == name2

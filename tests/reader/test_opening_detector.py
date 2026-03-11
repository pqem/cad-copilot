"""Tests para reader/opening_detector.py — detección de aberturas."""

from pathlib import Path

import ezdxf
import pytest

from cad_copilot.reader.opening_detector import (
    _block_has_arc,
    _classify_block_name,
    _estimate_block_width,
    detect_openings,
    detect_openings_from_arcs,
)
from cad_copilot.schemas.detection import DetectedOpening, OpeningKind

SAMPLE_DXF = Path(__file__).parent.parent.parent / "samples" / "Figueroa.dxf"


class TestClassifyBlockName:
    def test_door_spanish(self):
        assert _classify_block_name("Puerta_090") == OpeningKind.door

    def test_door_english(self):
        assert _classify_block_name("DOOR_HINGED") == OpeningKind.door

    def test_window_spanish(self):
        assert _classify_block_name("Ventana_150") == OpeningKind.window

    def test_window_english(self):
        assert _classify_block_name("WIN_SLIDING") == OpeningKind.window

    def test_exclude_toilet(self):
        assert _classify_block_name("Inodoro") == OpeningKind.unknown

    def test_exclude_sink(self):
        assert _classify_block_name("Lavamanos frente") == OpeningKind.unknown

    def test_exclude_north(self):
        assert _classify_block_name("NORTE3") == OpeningKind.unknown

    def test_exclude_cota(self):
        assert _classify_block_name("cota nivel vista") == OpeningKind.unknown

    def test_exclude_archtick(self):
        assert _classify_block_name("_ArchTick") == OpeningKind.unknown

    def test_unknown_generic(self):
        assert _classify_block_name("RANDOM_BLOCK") == OpeningKind.unknown


class TestBlockHasArc:
    def test_block_with_arc(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("DOOR_TEST")
        block.add_arc((0, 0), 0.9, 0, 90)
        assert _block_has_arc(doc, "DOOR_TEST") is True

    def test_block_without_arc(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("BOX")
        block.add_line((0, 0), (1, 0))
        assert _block_has_arc(doc, "BOX") is False

    def test_nonexistent_block(self):
        doc = ezdxf.new("R2013")
        assert _block_has_arc(doc, "NOEXIST") is False


class TestEstimateBlockWidth:
    def test_line_block_width(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("DOOR_090")
        block.add_line((0, 0), (0.9, 0))
        block.add_line((0, 0), (0, 0.9))
        width = _estimate_block_width(doc, "DOOR_090")
        assert width == pytest.approx(0.9, abs=0.01)

    def test_arc_block_width(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("DOOR_ARC")
        block.add_arc((0, 0), 0.8, 0, 90)
        width = _estimate_block_width(doc, "DOOR_ARC")
        assert width == pytest.approx(1.6, abs=0.01)

    def test_nonexistent_block(self):
        doc = ezdxf.new("R2013")
        assert _estimate_block_width(doc, "NOEXIST") == 0.0


class TestDetectOpenings:
    @pytest.fixture
    def doc_with_door(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("Puerta_090")
        block.add_line((0, 0), (0.9, 0))
        block.add_arc((0, 0), 0.9, 0, 90)

        msp = doc.modelspace()
        msp.add_blockref("Puerta_090", (5, 0))
        return doc

    @pytest.fixture
    def doc_with_window(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("Ventana_150")
        block.add_line((0, 0), (1.5, 0))
        block.add_line((0, 0.1), (1.5, 0.1))

        msp = doc.modelspace()
        msp.add_blockref("Ventana_150", (3, 2))
        return doc

    def test_detects_door(self, doc_with_door):
        openings = detect_openings(doc_with_door)
        assert len(openings) == 1
        assert openings[0].kind == OpeningKind.door
        assert openings[0].block_name == "Puerta_090"

    def test_detects_window(self, doc_with_window):
        openings = detect_openings(doc_with_window)
        assert len(openings) == 1
        assert openings[0].kind == OpeningKind.window

    def test_door_position(self, doc_with_door):
        openings = detect_openings(doc_with_door)
        assert openings[0].position[0] == pytest.approx(5.0)
        assert openings[0].position[1] == pytest.approx(0.0)

    def test_door_width_estimated(self, doc_with_door):
        openings = detect_openings(doc_with_door)
        assert openings[0].width > 0.5

    def test_ignores_sanitarios(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("Inodoro")
        block.add_line((0, 0), (0.4, 0))
        msp = doc.modelspace()
        msp.add_blockref("Inodoro", (1, 1))

        openings = detect_openings(doc)
        assert len(openings) == 0

    def test_detects_unnamed_door_by_arc(self):
        """Un bloque sin nombre de puerta pero CON arco se detecta como puerta."""
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("CUSTOM_BLOCK")
        block.add_line((0, 0), (0.8, 0))
        block.add_arc((0, 0), 0.8, 0, 90)

        msp = doc.modelspace()
        msp.add_blockref("CUSTOM_BLOCK", (2, 3))

        openings = detect_openings(doc)
        assert len(openings) == 1
        assert openings[0].kind == OpeningKind.door

    def test_sequential_ids(self):
        doc = ezdxf.new("R2013")
        for i, name in enumerate(["Puerta_A", "Ventana_B"]):
            block = doc.blocks.new(name)
            block.add_line((0, 0), (0.9, 0))
            doc.modelspace().add_blockref(name, (i * 5, 0))

        openings = detect_openings(doc)
        assert len(openings) == 2
        assert openings[0].id == "opening_0"
        assert openings[1].id == "opening_1"


class TestDetectOpeningsFromArcs:
    def test_detects_door_arc(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_arc((5, 0), 0.9, 0, 90)

        openings = detect_openings_from_arcs(doc)
        assert len(openings) == 1
        assert openings[0].kind == OpeningKind.door
        assert openings[0].width == pytest.approx(0.9)

    def test_ignores_small_arc(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_arc((5, 0), 0.1, 0, 90)  # too small

        openings = detect_openings_from_arcs(doc)
        assert len(openings) == 0

    def test_ignores_large_arc(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_arc((5, 0), 5.0, 0, 90)  # too large

        openings = detect_openings_from_arcs(doc)
        assert len(openings) == 0

    def test_ignores_full_circle_arc(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_arc((5, 0), 0.9, 0, 350)  # nearly full circle

        openings = detect_openings_from_arcs(doc)
        assert len(openings) == 0


@pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample DXF not available")
class TestDetectOpeningsFigueroa:
    @pytest.fixture(scope="class")
    def doc(self):
        return ezdxf.readfile(str(SAMPLE_DXF))

    def test_detects_some_openings(self, doc):
        openings = detect_openings(doc)
        # Figueroa has sanitarios blocks (Inodoro, Lavamanos, etc.)
        # but those should be excluded; there might be door-like blocks with ARCs
        # At minimum it should not crash
        assert isinstance(openings, list)

    def test_detects_arcs_as_doors(self, doc):
        openings = detect_openings_from_arcs(doc)
        assert len(openings) > 0  # Figueroa has 191 ARC entities

    def test_arc_widths_reasonable(self, doc):
        openings = detect_openings_from_arcs(doc)
        for o in openings:
            assert 0.5 <= o.width <= 1.5

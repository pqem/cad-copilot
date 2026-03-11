"""Tests para reader/space_detector.py — detección de espacios."""

from pathlib import Path

import ezdxf
import pytest

from cad_copilot.reader.space_detector import (
    _classify_space_name,
    _extract_area_from_text,
    detect_spaces,
)
from cad_copilot.schemas.detection import SpaceCategory

SAMPLE_DXF = Path(__file__).parent.parent.parent / "samples" / "Figueroa.dxf"


class TestClassifySpaceName:
    def test_dormitorio(self):
        cat, name = _classify_space_name("DORMITORIO 1")
        assert cat == SpaceCategory.dormitorio
        assert name == "DORMITORIO 1"

    def test_cocina(self):
        cat, _ = _classify_space_name("cocina")
        assert cat == SpaceCategory.cocina

    def test_bano_with_tilde(self):
        cat, _ = _classify_space_name("BAÑO")
        assert cat == SpaceCategory.bano

    def test_bano_without_tilde(self):
        cat, _ = _classify_space_name("BANO PRINCIPAL")
        assert cat == SpaceCategory.bano

    def test_living(self):
        cat, _ = _classify_space_name("Living - Comedor")
        assert cat == SpaceCategory.living

    def test_garage(self):
        cat, _ = _classify_space_name("GARAGE")
        assert cat == SpaceCategory.garage

    def test_lavadero(self):
        cat, _ = _classify_space_name("Lavadero")
        assert cat == SpaceCategory.lavadero

    def test_pasillo(self):
        cat, _ = _classify_space_name("PASILLO")
        assert cat == SpaceCategory.pasillo

    def test_hall(self):
        cat, _ = _classify_space_name("hall de entrada")
        assert cat == SpaceCategory.hall

    def test_estar(self):
        cat, _ = _classify_space_name("ESTAR")
        assert cat == SpaceCategory.estar

    def test_escritorio(self):
        cat, _ = _classify_space_name("Escritorio")
        assert cat == SpaceCategory.escritorio

    def test_deposito(self):
        cat, _ = _classify_space_name("DEPÓSITO")
        assert cat == SpaceCategory.deposito

    def test_unknown(self):
        cat, name = _classify_space_name("CALLE ARISTOBULO")
        assert cat == SpaceCategory.otro
        assert name == ""

    def test_short_text(self):
        cat, _ = _classify_space_name("AB")
        assert cat == SpaceCategory.otro

    def test_empty_text(self):
        cat, _ = _classify_space_name("")
        assert cat == SpaceCategory.otro

    def test_toilette(self):
        cat, _ = _classify_space_name("TOILETTE")
        assert cat == SpaceCategory.bano


class TestExtractAreaFromText:
    def test_m2_with_superscript(self):
        assert _extract_area_from_text("12.50 m²") == pytest.approx(12.50)

    def test_m2_number(self):
        assert _extract_area_from_text("8.30 m2") == pytest.approx(8.30)

    def test_sup_equals(self):
        assert _extract_area_from_text("Sup.= 15.20") == pytest.approx(15.20)

    def test_area_equals(self):
        assert _extract_area_from_text("área= 9.00") == pytest.approx(9.00)

    def test_comma_decimal(self):
        assert _extract_area_from_text("10,50 m²") == pytest.approx(10.50)

    def test_no_area(self):
        assert _extract_area_from_text("COCINA") is None

    def test_empty(self):
        assert _extract_area_from_text("") is None


class TestDetectSpaces:
    @pytest.fixture
    def doc_with_spaces(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        msp.add_text(
            "COCINA", dxfattribs={"layer": "TEXTOS", "insert": (5, 3)}
        )
        msp.add_text(
            "DORMITORIO 1", dxfattribs={"layer": "TEXTOS", "insert": (10, 8)}
        )
        msp.add_mtext(
            "BAÑO\\P3.50 m²",
            dxfattribs={"layer": "TEXTOS", "insert": (2, 2)},
        )

        return doc

    def test_detects_spaces(self, doc_with_spaces):
        spaces = detect_spaces(doc_with_spaces)
        assert len(spaces) == 3

    def test_space_categories(self, doc_with_spaces):
        spaces = detect_spaces(doc_with_spaces)
        categories = {s.category for s in spaces}
        assert SpaceCategory.cocina in categories
        assert SpaceCategory.dormitorio in categories
        assert SpaceCategory.bano in categories

    def test_space_positions(self, doc_with_spaces):
        spaces = detect_spaces(doc_with_spaces)
        cocina = next(s for s in spaces if s.category == SpaceCategory.cocina)
        assert cocina.centroid[0] == pytest.approx(5.0)

    def test_sequential_ids(self, doc_with_spaces):
        spaces = detect_spaces(doc_with_spaces)
        assert spaces[0].id == "space_0"
        assert spaces[1].id == "space_1"

    def test_ignores_non_space_text(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_text("F.O.S. 0.60", dxfattribs={"insert": (0, 0)})
        msp.add_text("CALLE ARISTOBULO", dxfattribs={"insert": (0, 0)})

        spaces = detect_spaces(doc)
        assert len(spaces) == 0

    def test_empty_dxf(self):
        doc = ezdxf.new("R2013")
        spaces = detect_spaces(doc)
        assert len(spaces) == 0


@pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample DXF not available")
class TestDetectSpacesFigueroa:
    @pytest.fixture(scope="class")
    def doc(self):
        return ezdxf.readfile(str(SAMPLE_DXF))

    def test_detects_some_spaces(self, doc):
        spaces = detect_spaces(doc)
        # Figueroa should have labeled rooms
        assert isinstance(spaces, list)

    def test_spaces_have_layers(self, doc):
        spaces = detect_spaces(doc)
        for s in spaces:
            assert s.layer != ""

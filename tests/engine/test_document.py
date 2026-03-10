"""Tests para engine/document.py — create_document."""

import pytest
from ezdxf.document import Drawing

from cad_copilot.engine.document import create_document


class TestCreateDocument:
    def test_returns_drawing_instance(self):
        doc = create_document()
        assert isinstance(doc, Drawing)

    def test_insunits_is_meters(self):
        doc = create_document()
        assert doc.header["$INSUNITS"] == 6

    def test_measurement_is_metric(self):
        doc = create_document()
        assert doc.header["$MEASUREMENT"] == 1

    def test_lunits_decimal(self):
        doc = create_document()
        assert doc.header["$LUNITS"] == 2

    def test_luprec_two_decimals(self):
        doc = create_document()
        assert doc.header["$LUPREC"] == 2

    def test_has_iram_arq_dimstyle(self):
        doc = create_document()
        assert "IRAM_ARQ" in doc.dimstyles

    def test_has_wall_layer(self):
        doc = create_document()
        assert "A-WALL" in doc.layers

    def test_has_door_layer(self):
        doc = create_document()
        assert "A-DOOR" in doc.layers

    def test_custom_scale_50(self):
        doc = create_document(scale=50)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimscale == pytest.approx(50.0)

    def test_custom_scale_100(self):
        doc = create_document(scale=100)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimscale == pytest.approx(100.0)

    def test_modelspace_accessible(self):
        doc = create_document()
        msp = doc.modelspace()
        assert msp is not None

    def test_default_version_r2013(self):
        doc = create_document()
        # R2013 = AC1027
        assert doc.dxfversion == "AC1027"

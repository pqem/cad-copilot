"""Tests para standards/dimstyles.py — setup_dimstyles."""

import pytest
import ezdxf

from cad_copilot.standards.dimstyles import setup_dimstyles, DIMSTYLE_IRAM


class TestDimstyleDict:
    def test_name_is_iram_arq(self):
        assert DIMSTYLE_IRAM["name"] == "IRAM_ARQ"

    def test_has_dimscale(self):
        assert "dimscale" in DIMSTYLE_IRAM

    def test_has_dimtxt(self):
        assert "dimtxt" in DIMSTYLE_IRAM

    def test_dimtad_above_line(self):
        # DIMTAD=1 = texto arriba de la línea (convención Argentina)
        assert DIMSTYLE_IRAM["dimtad"] == 1


class TestSetupDimstyles:
    def test_creates_iram_arq_style(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=50)
        assert "IRAM_ARQ" in doc.dimstyles

    def test_dimscale_matches_scale_50(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=50)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimscale == pytest.approx(50.0)

    def test_dimscale_matches_scale_100(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=100)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimscale == pytest.approx(100.0)

    def test_dimscale_matches_scale_25(self):
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=25)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimscale == pytest.approx(25.0)

    def test_idempotent_no_error_on_double_call(self):
        """Llamar dos veces no debe lanzar error."""
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=50)
        setup_dimstyles(doc, scale=50)  # segunda llamada ignorada
        assert "IRAM_ARQ" in doc.dimstyles

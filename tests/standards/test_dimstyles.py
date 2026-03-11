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

    def test_dimscale_always_one(self):
        """DIMSCALE=1 siempre — los valores ya están en metros."""
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=50)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimscale == pytest.approx(1.0)

    def test_dimtxt_scaled_to_meters_50(self):
        """A escala 1:50, dimtxt = 2.5mm × 50 / 1000 = 0.125m."""
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=50)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimtxt == pytest.approx(0.125)

    def test_dimtxt_scaled_to_meters_100(self):
        """A escala 1:100, dimtxt = 2.5mm × 100 / 1000 = 0.25m."""
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=100)
        style = doc.dimstyles.get("IRAM_ARQ")
        assert style.dxf.dimtxt == pytest.approx(0.25)

    def test_idempotent_no_error_on_double_call(self):
        """Llamar dos veces no debe lanzar error."""
        doc = ezdxf.new("R2013", setup=True)
        setup_dimstyles(doc, scale=50)
        setup_dimstyles(doc, scale=50)  # segunda llamada ignorada
        assert "IRAM_ARQ" in doc.dimstyles

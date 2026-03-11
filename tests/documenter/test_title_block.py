"""Tests para documenter/title_block.py — cartela CPTN."""

import ezdxf
import pytest

from cad_copilot.documenter.title_block import add_title_block_to_existing
from cad_copilot.schemas.layout import TitleBlock


class TestAddTitleBlockToExisting:
    @pytest.fixture
    def doc(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_line((0, 0), (10, 0))
        msp.add_line((0, 0), (0, 5))
        return doc

    @pytest.fixture
    def title_block(self):
        return TitleBlock(
            project="Casa Figueroa",
            location="Plottier, Neuquén",
            owner="Cliente",
            professional="Arq. Pablo Quevedo",
            license_number="CPTN 1234",
            date="2026-03",
            sheet="1/1",
            drawing_name="Planta Baja",
        )

    def test_creates_layout(self, doc, title_block):
        layout = add_title_block_to_existing(doc, title_block)
        assert layout is not None
        assert "Documentacion" in [l.name for l in doc.layouts]

    def test_inserts_cartela_block(self, doc, title_block):
        layout = add_title_block_to_existing(doc, title_block)
        inserts = [e for e in layout if e.dxftype() == "INSERT"]
        assert len(inserts) >= 1
        assert inserts[0].dxf.name == "CARTELA_CPTN"

    def test_creates_aia_layers(self, doc, title_block):
        add_title_block_to_existing(doc, title_block)
        layer_names = [l.dxf.name for l in doc.layers]
        assert "A-ANNO-TTLB" in layer_names

    def test_default_paper_config(self, doc, title_block):
        layout = add_title_block_to_existing(doc, title_block)
        # Should have a viewport
        viewports = [e for e in layout if e.dxftype() == "VIEWPORT"]
        assert len(viewports) >= 1

    def test_empty_doc(self, title_block):
        doc = ezdxf.new("R2013")
        layout = add_title_block_to_existing(doc, title_block)
        assert layout is not None

    def test_custom_layout_name(self, doc, title_block):
        layout = add_title_block_to_existing(
            doc, title_block, layout_name="MiPlano"
        )
        assert layout is not None
        assert "MiPlano" in [l.name for l in doc.layouts]

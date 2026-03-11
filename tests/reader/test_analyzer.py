"""Tests para reader/analyzer.py — análisis general de DXF."""

from pathlib import Path

import ezdxf
import pytest

from cad_copilot.reader.analyzer import analyze_dxf, read_dxf
from cad_copilot.schemas.detection import DxfAnalysis

SAMPLE_DXF = Path(__file__).parent.parent.parent / "samples" / "Figueroa.dxf"


# --- read_dxf ---


class TestReadDxf:
    def test_read_valid_dxf(self, tmp_path):
        doc = ezdxf.new("R2013")
        path = tmp_path / "test.dxf"
        doc.saveas(str(path))
        result = read_dxf(path)
        assert result is not None

    def test_read_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            read_dxf("/nonexistent/file.dxf")

    def test_read_non_dxf_extension(self, tmp_path):
        path = tmp_path / "file.txt"
        path.write_text("not a dxf")
        with pytest.raises(ValueError, match="no es DXF"):
            read_dxf(path)


# --- analyze_dxf con DXF sintético ---


class TestAnalyzeDxfSynthetic:
    @pytest.fixture
    def simple_dxf(self, tmp_path):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        doc.layers.add("WALLS", color=1)
        doc.layers.add("TEXT", color=2)

        msp.add_line((0, 0), (10, 0), dxfattribs={"layer": "WALLS"})
        msp.add_line((10, 0), (10, 5), dxfattribs={"layer": "WALLS"})
        msp.add_line((0, 0), (0, 5), dxfattribs={"layer": "WALLS"})
        msp.add_lwpolyline(
            [(0, 5), (10, 5), (10, 0)], dxfattribs={"layer": "WALLS"}
        )
        msp.add_text("COCINA", dxfattribs={"layer": "TEXT", "insert": (5, 2.5)})

        path = tmp_path / "simple.dxf"
        doc.saveas(str(path))
        return path

    def test_returns_dxf_analysis(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        assert isinstance(result, DxfAnalysis)

    def test_metadata(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        assert result.metadata.dxf_version == "AC1027"
        assert result.metadata.file_size_bytes > 0
        assert "simple.dxf" in result.metadata.file_path

    def test_layers(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        names = result.layer_names
        assert "WALLS" in names
        assert "TEXT" in names

    def test_layer_entity_count(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        walls_layer = next(l for l in result.layers if l.name == "WALLS")
        assert walls_layer.entity_count == 4  # 3 lines + 1 lwpolyline

    def test_entity_stats(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        assert result.total_entities == 5
        types = {s.entity_type: s.count for s in result.entity_stats}
        assert types["LINE"] == 3
        assert types["LWPOLYLINE"] == 1
        assert types["TEXT"] == 1

    def test_bounding_box(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        bb = result.bounding_box
        assert bb.min_point[0] == pytest.approx(0.0)
        assert bb.min_point[1] == pytest.approx(0.0)
        assert bb.max_point[0] == pytest.approx(10.0)
        assert bb.max_point[1] == pytest.approx(5.0)
        assert bb.width == pytest.approx(10.0)
        assert bb.height == pytest.approx(5.0)

    def test_dimstyles(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        assert "Standard" in result.dimstyles

    def test_textstyles(self, simple_dxf):
        result = analyze_dxf(simple_dxf)
        assert "Standard" in result.textstyles

    def test_empty_dxf(self, tmp_path):
        doc = ezdxf.new("R2013")
        path = tmp_path / "empty.dxf"
        doc.saveas(str(path))
        result = analyze_dxf(path)
        assert result.total_entities == 0
        assert result.bounding_box.width == 0.0


# --- analyze_dxf con Figueroa.dxf ---


@pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample DXF not available")
class TestAnalyzeFigueroa:
    @pytest.fixture(scope="class")
    def analysis(self):
        return analyze_dxf(SAMPLE_DXF)

    def test_total_entities(self, analysis):
        assert analysis.total_entities > 30000

    def test_layer_count(self, analysis):
        assert len(analysis.layers) >= 40

    def test_dxf_version(self, analysis):
        assert analysis.metadata.dxf_version == "AC1032"

    def test_encoding(self, analysis):
        assert analysis.metadata.encoding == "cp1252"

    def test_insunits(self, analysis):
        assert analysis.metadata.insunits == 6  # metros

    def test_has_dimensions(self, analysis):
        types = {s.entity_type: s.count for s in analysis.entity_stats}
        assert types.get("DIMENSION", 0) >= 100

    def test_has_lines(self, analysis):
        types = {s.entity_type: s.count for s in analysis.entity_stats}
        assert types.get("LINE", 0) > 20000

    def test_has_blocks(self, analysis):
        assert len(analysis.blocks) > 10

    def test_bounding_box_nonzero(self, analysis):
        assert analysis.bounding_box.width > 0
        assert analysis.bounding_box.height > 0

    def test_has_dimstyles(self, analysis):
        assert len(analysis.dimstyles) >= 1

    def test_file_size(self, analysis):
        assert analysis.metadata.file_size_bytes > 1_000_000  # >1MB

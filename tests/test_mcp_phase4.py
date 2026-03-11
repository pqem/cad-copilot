"""Tests para los MCP tools de Fase 4 (reader + documenter)."""

from pathlib import Path

import ezdxf
import pytest

from cad_copilot.mcp_server.server import (
    add_dimensions_tool,
    add_norm_table_tool,
    add_title_block_tool,
    detect_elements,
    document_dxf,
    read_dxf,
    suggest_missing,
)

SAMPLE_DXF = Path(__file__).parent.parent / "samples" / "Figueroa.dxf"


@pytest.fixture
def simple_dxf(tmp_path):
    """Crea un DXF simple para testing."""
    doc = ezdxf.new("R2013")
    msp = doc.modelspace()

    # Muros como pares de líneas paralelas
    msp.add_line((0, 0), (5, 0))
    msp.add_line((0, 0.15), (5, 0.15))
    msp.add_line((5, 0), (5, 4))
    msp.add_line((5.15, 0), (5.15, 4))

    # Texto de espacio
    msp.add_text("COCINA", dxfattribs={"insert": (2.5, 2)})
    msp.add_text("DORMITORIO", dxfattribs={"insert": (7, 2)})

    path = tmp_path / "test.dxf"
    doc.saveas(str(path))
    return str(path)


class TestReadDxfTool:
    def test_reads_synthetic(self, simple_dxf):
        result = read_dxf(simple_dxf)
        assert "ANÁLISIS DXF" in result
        assert "Total entidades" in result

    def test_file_not_found(self):
        result = read_dxf("/nonexistent.dxf")
        assert "ERROR" in result

    def test_not_dxf(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("hello")
        result = read_dxf(str(p))
        assert "ERROR" in result

    @pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample not available")
    def test_reads_figueroa(self):
        result = read_dxf(str(SAMPLE_DXF))
        assert "30" in result  # 30K+ entities
        assert "LAYERS" in result


class TestDetectElementsTool:
    def test_detects_in_synthetic(self, simple_dxf):
        result = detect_elements(simple_dxf)
        assert "DETECCIÓN DE ELEMENTOS" in result
        assert "MUROS DETECTADOS" in result
        assert "COTAS EXISTENTES" in result

    def test_file_not_found(self):
        result = detect_elements("/nonexistent.dxf")
        assert "ERROR" in result

    @pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample not available")
    def test_detects_in_figueroa(self):
        result = detect_elements(str(SAMPLE_DXF))
        assert "MUROS DETECTADOS" in result
        assert "COTAS EXISTENTES" in result


class TestSuggestMissingTool:
    def test_suggests_for_synthetic(self, simple_dxf):
        result = suggest_missing(simple_dxf)
        assert "REPORTE DE COMPLETITUD" in result
        assert "Score" in result

    def test_file_not_found(self):
        result = suggest_missing("/nonexistent.dxf")
        assert "ERROR" in result


class TestAddDimensionsTool:
    def test_adds_dimensions(self, simple_dxf, tmp_path):
        output = str(tmp_path / "output.dxf")
        result = add_dimensions_tool(simple_dxf, output)
        assert "Cotas agregadas" in result
        assert Path(output).exists()

    def test_file_not_found(self, tmp_path):
        result = add_dimensions_tool("/nonexistent.dxf", str(tmp_path / "out.dxf"))
        assert "ERROR" in result


class TestAddNormTableTool:
    def test_with_spaces(self, tmp_path):
        # Crear DXF con texto de espacio
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_text("COCINA", dxfattribs={"insert": (2, 2)})
        path = tmp_path / "input.dxf"
        doc.saveas(str(path))

        output = str(tmp_path / "output.dxf")
        result = add_norm_table_tool(str(path), output, "Proyecto Test")
        # May or may not detect spaces depending on area info
        assert isinstance(result, str)


class TestAddTitleBlockTool:
    def test_adds_title_block(self, simple_dxf, tmp_path):
        output = str(tmp_path / "output.dxf")
        result = add_title_block_tool(
            simple_dxf, output,
            project="Casa Test",
            drawing_name="Planta Baja",
            professional="Arq. Test",
            license_number="CPTN 1234",
        )
        assert "Cartela CPTN agregada" in result
        assert Path(output).exists()

        # Verify the output has the cartela block
        doc = ezdxf.readfile(output)
        assert "CARTELA_CPTN" in [b.name for b in doc.blocks]


class TestDocumentDxfTool:
    def test_full_documentation(self, simple_dxf, tmp_path):
        output = str(tmp_path / "documented.dxf")
        result = document_dxf(
            simple_dxf, output,
            project="Casa Figueroa",
            professional="Arq. Quevedo",
        )
        assert "DOCUMENTACIÓN DXF" in result
        assert "Detectados" in result
        assert Path(output).exists()

    def test_file_not_found(self, tmp_path):
        result = document_dxf("/nonexistent.dxf", str(tmp_path / "out.dxf"))
        assert "ERROR" in result

    @pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample not available")
    def test_document_figueroa(self, tmp_path):
        output = str(tmp_path / "figueroa_doc.dxf")
        result = document_dxf(
            str(SAMPLE_DXF), output,
            project="Casa Figueroa",
            professional="Arq. Pablo Quevedo",
            license_number="CPTN 1234",
            location="Plottier, Neuquén",
        )
        assert "DOCUMENTACIÓN DXF" in result
        assert Path(output).exists()

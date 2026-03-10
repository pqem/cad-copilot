"""Tests de integración para engine/renderer.py — render_floor_plan, render_from_json."""

import json
import pytest
from pathlib import Path

from cad_copilot.engine.renderer import render_floor_plan, render_from_json
from cad_copilot.schemas.project import FloorPlan
from cad_copilot.schemas.wall import Wall, WallClassification
from cad_copilot.schemas.opening import Opening, OpeningType
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.layout import PaperConfig, TitleBlock, PaperSize, Orientation


@pytest.fixture
def output_dir(tmp_path):
    """Directorio temporal para archivos DXF generados."""
    return tmp_path


@pytest.fixture
def minimal_floor_plan():
    """FloorPlan mínimo para tests de integración."""
    return FloorPlan(
        walls=[
            Wall(id="W1", start=(0.0, 0.0), end=(4.0, 0.0), thickness=0.20,
                 classification=WallClassification.exterior_portante),
            Wall(id="W2", start=(4.0, 0.0), end=(4.0, 3.0), thickness=0.20,
                 classification=WallClassification.exterior_portante),
            Wall(id="W3", start=(4.0, 3.0), end=(0.0, 3.0), thickness=0.20,
                 classification=WallClassification.exterior_portante),
            Wall(id="W4", start=(0.0, 3.0), end=(0.0, 0.0), thickness=0.20,
                 classification=WallClassification.exterior_portante),
        ]
    )


@pytest.fixture
def full_floor_plan(title_block, paper_config):
    """FloorPlan completo con espacios, aberturas y cartela."""
    return FloorPlan(
        walls=[
            Wall(
                id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30,
                classification=WallClassification.exterior_portante,
                openings=[
                    Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0),
                    Opening(type=OpeningType.window, width=1.50, position_along_wall=3.5),
                ],
            ),
            Wall(id="W2", start=(6.0, 0.0), end=(6.0, 4.0), thickness=0.30,
                 classification=WallClassification.exterior_portante),
            Wall(id="W3", start=(6.0, 4.0), end=(0.0, 4.0), thickness=0.30,
                 classification=WallClassification.exterior_portante),
            Wall(id="W4", start=(0.0, 4.0), end=(0.0, 0.0), thickness=0.30,
                 classification=WallClassification.exterior_portante),
        ],
        spaces=[
            Space(id="S1", name="LIVING", function=SpaceFunction.living,
                  bounded_by=["W1", "W2", "W3", "W4"]),
        ],
        title_block=title_block,
        paper_config=paper_config,
    )


class TestRenderFloorPlan:
    def test_creates_dxf_file(self, minimal_floor_plan, output_dir):
        out = str(output_dir / "test.dxf")
        result = render_floor_plan(minimal_floor_plan, out)
        assert Path(result).exists()

    def test_returns_absolute_path(self, minimal_floor_plan, output_dir):
        out = str(output_dir / "test.dxf")
        result = render_floor_plan(minimal_floor_plan, out)
        assert Path(result).is_absolute()

    def test_creates_output_directory(self, minimal_floor_plan, tmp_path):
        out = str(tmp_path / "subdir" / "test.dxf")
        result = render_floor_plan(minimal_floor_plan, out)
        assert Path(result).exists()

    def test_dxf_is_valid(self, minimal_floor_plan, output_dir):
        import ezdxf
        out = str(output_dir / "test.dxf")
        render_floor_plan(minimal_floor_plan, out)
        doc = ezdxf.readfile(out)
        assert doc is not None

    def test_full_floor_plan_renders(self, full_floor_plan, output_dir):
        """Test E2E con todo: muros, aberturas, espacios, cartela."""
        out = str(output_dir / "full.dxf")
        result = render_floor_plan(full_floor_plan, out)
        assert Path(result).exists()

    def test_full_dxf_has_walls(self, full_floor_plan, output_dir):
        import ezdxf
        out = str(output_dir / "walls.dxf")
        render_floor_plan(full_floor_plan, out)
        doc = ezdxf.readfile(out)
        msp = doc.modelspace()
        polylines = [e for e in msp if e.dxftype() == "LWPOLYLINE" and e.dxf.layer == "A-WALL"]
        assert len(polylines) >= 4

    def test_full_dxf_has_doors(self, full_floor_plan, output_dir):
        import ezdxf
        out = str(output_dir / "doors.dxf")
        render_floor_plan(full_floor_plan, out)
        doc = ezdxf.readfile(out)
        msp = doc.modelspace()
        inserts = [e for e in msp if e.dxftype() == "INSERT" and e.dxf.layer == "A-DOOR"]
        assert len(inserts) >= 1

    def test_full_dxf_has_space_labels(self, full_floor_plan, output_dir):
        import ezdxf
        out = str(output_dir / "labels.dxf")
        render_floor_plan(full_floor_plan, out)
        doc = ezdxf.readfile(out)
        msp = doc.modelspace()
        mtexts = [e for e in msp if e.dxftype() == "MTEXT"]
        assert len(mtexts) >= 1

    def test_paper_space_layout_created(self, full_floor_plan, output_dir):
        import ezdxf
        out = str(output_dir / "layout.dxf")
        render_floor_plan(full_floor_plan, out)
        doc = ezdxf.readfile(out)
        # Debe haber al menos un layout además del Model
        assert len(doc.layouts) >= 2


class TestRenderFromJson:
    def test_renders_template(self, output_dir):
        template = Path(__file__).parents[2] / "templates" / "vivienda_simple.json"
        if not template.exists():
            pytest.skip("Template no encontrado")
        out = str(output_dir / "vivienda.dxf")
        result = render_from_json(str(template), out)
        assert Path(result).exists()

    def test_template_produces_valid_dxf(self, output_dir):
        import ezdxf
        template = Path(__file__).parents[2] / "templates" / "vivienda_simple.json"
        if not template.exists():
            pytest.skip("Template no encontrado")
        out = str(output_dir / "vivienda.dxf")
        render_from_json(str(template), out)
        doc = ezdxf.readfile(out)
        msp = doc.modelspace()
        entities = list(msp)
        assert len(entities) > 0

    def test_invalid_json_raises_error(self, output_dir, tmp_path):
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{invalid json")
        with pytest.raises(Exception):
            render_from_json(str(bad_json), str(output_dir / "out.dxf"))

    def test_missing_required_field_raises_error(self, output_dir, tmp_path):
        from pydantic import ValidationError
        bad_json = tmp_path / "no_walls.json"
        bad_json.write_text('{"spaces": []}')
        with pytest.raises(ValidationError):
            render_from_json(str(bad_json), str(output_dir / "out.dxf"))

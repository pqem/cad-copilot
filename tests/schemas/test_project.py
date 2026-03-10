"""Tests para schemas/project.py — FloorPlan (modelo raíz)."""

import pytest
from pydantic import ValidationError

from cad_copilot.schemas.project import FloorPlan
from cad_copilot.schemas.wall import Wall
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.annotation import AnnotationConfig
from cad_copilot.schemas.layout import PaperConfig, TitleBlock


class TestFloorPlanDefaults:
    def test_walls_required(self):
        with pytest.raises(ValidationError):
            FloorPlan()

    def test_minimal_floor_plan(self):
        w = Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0))
        fp = FloorPlan(walls=[w])
        assert len(fp.walls) == 1
        assert fp.spaces == []
        assert isinstance(fp.annotations, AnnotationConfig)
        assert fp.title_block is None
        assert isinstance(fp.paper_config, PaperConfig)

    def test_floor_plan_with_spaces(self):
        w = Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0))
        s = Space(name="DORMITORIO", function=SpaceFunction.dormitorio, bounded_by=["W1"])
        fp = FloorPlan(walls=[w], spaces=[s])
        assert len(fp.spaces) == 1

    def test_floor_plan_with_title_block(self):
        w = Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0))
        tb = TitleBlock(
            project="TEST",
            location="TEST",
            professional="ARQ. TEST",
            license_number="99",
            date="2026-01-01",
            drawing_name="PLANTA",
        )
        fp = FloorPlan(walls=[w], title_block=tb)
        assert fp.title_block is not None
        assert fp.title_block.project == "TEST"

    def test_floor_plan_multiple_walls(self):
        walls = [
            Wall(id=f"W{i}", start=(float(i), 0.0), end=(float(i + 1), 0.0))
            for i in range(5)
        ]
        fp = FloorPlan(walls=walls)
        assert len(fp.walls) == 5

    def test_from_json_template(self):
        """Verifica que el template vivienda_simple.json parsea correctamente."""
        import json
        from pathlib import Path

        template = Path(__file__).parents[2] / "templates" / "vivienda_simple.json"
        if not template.exists():
            pytest.skip("Template no encontrado")

        data = json.loads(template.read_text())
        fp = FloorPlan.model_validate(data)
        assert len(fp.walls) == 5
        assert len(fp.spaces) == 2
        assert fp.title_block is not None

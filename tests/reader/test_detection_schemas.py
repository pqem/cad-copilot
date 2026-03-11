"""Tests para schemas/detection.py — modelos Pydantic de detección."""

import pytest

from cad_copilot.schemas.detection import (
    BlockInfo,
    BoundingBox,
    DetectedDimension,
    DetectedOpening,
    DetectedSpace,
    DetectedWall,
    DetectionResult,
    DxfAnalysis,
    DxfMetadata,
    EntityStats,
    LayerInfo,
    OpeningKind,
    SpaceCategory,
    Suggestion,
    SuggestionKind,
    SuggestionReport,
)


class TestLayerInfo:
    def test_defaults(self):
        layer = LayerInfo(name="TEST")
        assert layer.color == 7
        assert layer.lineweight == -3
        assert layer.entity_count == 0
        assert layer.is_frozen is False

    def test_full(self):
        layer = LayerInfo(name="A-WALL", color=1, lineweight=50, entity_count=100)
        assert layer.name == "A-WALL"
        assert layer.entity_count == 100


class TestBlockInfo:
    def test_defaults(self):
        block = BlockInfo(name="DOOR")
        assert block.entity_count == 0
        assert block.insert_count == 0


class TestBoundingBox:
    def test_dimensions(self):
        bb = BoundingBox(min_point=(0.0, 0.0), max_point=(10.0, 5.0))
        assert bb.width == pytest.approx(10.0)
        assert bb.height == pytest.approx(5.0)

    def test_default_zero(self):
        bb = BoundingBox()
        assert bb.width == 0.0
        assert bb.height == 0.0


class TestDxfAnalysis:
    def test_layer_names_property(self):
        analysis = DxfAnalysis(
            metadata=DxfMetadata(file_path="test.dxf"),
            layers=[LayerInfo(name="A"), LayerInfo(name="B")],
        )
        assert analysis.layer_names == ["A", "B"]

    def test_empty_analysis(self):
        analysis = DxfAnalysis(metadata=DxfMetadata(file_path="test.dxf"))
        assert analysis.total_entities == 0
        assert analysis.layers == []


class TestDetectedWall:
    def test_basic(self):
        wall = DetectedWall(start=(0, 0), end=(5, 0), thickness=0.15, layer="0.15")
        assert wall.thickness == pytest.approx(0.15)
        assert wall.layer == "0.15"

    def test_defaults(self):
        wall = DetectedWall(start=(0, 0), end=(1, 1))
        assert wall.id == ""
        assert wall.thickness == 0.0
        assert wall.entity_handles == []


class TestDetectedOpening:
    def test_door(self):
        opening = DetectedOpening(kind=OpeningKind.door, position=(2, 0), width=0.8)
        assert opening.kind == "door"
        assert opening.width == pytest.approx(0.8)

    def test_default_unknown(self):
        opening = DetectedOpening()
        assert opening.kind == OpeningKind.unknown


class TestDetectedSpace:
    def test_with_category(self):
        space = DetectedSpace(
            name="Cocina", category=SpaceCategory.cocina, area=8.5
        )
        assert space.category == "cocina"
        assert space.area == pytest.approx(8.5)


class TestDetectedDimension:
    def test_basic(self):
        dim = DetectedDimension(value=3.5, start=(0, 0), end=(3.5, 0))
        assert dim.value == pytest.approx(3.5)


class TestDetectionResult:
    def test_empty(self):
        result = DetectionResult(
            analysis=DxfAnalysis(metadata=DxfMetadata(file_path="test.dxf"))
        )
        assert result.walls == []
        assert result.openings == []
        assert result.spaces == []
        assert result.dimensions == []


class TestSuggestion:
    def test_basic(self):
        s = Suggestion(
            kind=SuggestionKind.missing_dimension,
            description="Muro sin cotar",
            priority=1,
        )
        assert s.kind == "missing_dimension"

    def test_priority_validation(self):
        with pytest.raises(Exception):
            Suggestion(
                kind=SuggestionKind.missing_dimension,
                description="test",
                priority=5,
            )


class TestSuggestionReport:
    def test_completeness_score_empty(self):
        report = SuggestionReport()
        # has_title_block=False, has_north_arrow=False, walls ok (0/0), spaces ok (0/0)
        assert report.completeness_score == pytest.approx(50.0)

    def test_completeness_score_full(self):
        report = SuggestionReport(
            has_title_block=True,
            has_north_arrow=True,
            total_walls=5,
            walls_with_dimensions=5,
            total_spaces=3,
            spaces_with_area_labels=3,
        )
        assert report.completeness_score == pytest.approx(100.0)

    def test_completeness_score_partial(self):
        report = SuggestionReport(
            has_title_block=True,
            has_north_arrow=False,
            total_walls=5,
            walls_with_dimensions=3,  # incomplete
        )
        assert report.completeness_score < 100.0

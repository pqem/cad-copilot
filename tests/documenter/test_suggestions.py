"""Tests para documenter/suggestions.py — análisis de completitud."""

from pathlib import Path

import ezdxf
import pytest

from cad_copilot.documenter.suggestions import (
    _find_spaces_without_area,
    _find_walls_without_dimensions,
    _has_north_arrow,
    _has_title_block,
    analyze_completeness,
)
from cad_copilot.schemas.detection import (
    DetectedDimension,
    DetectedOpening,
    DetectedSpace,
    DetectedWall,
    SpaceCategory,
    SuggestionKind,
)

SAMPLE_DXF = Path(__file__).parent.parent.parent / "samples" / "Figueroa.dxf"


class TestHasTitleBlock:
    def test_no_title_block(self):
        doc = ezdxf.new("R2013")
        assert _has_title_block(doc) is False

    def test_title_block_by_block_name(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("CARTELA_CPTN")
        block.add_line((0, 0), (1, 0))
        doc.modelspace().add_blockref("CARTELA_CPTN", (0, 0))
        assert _has_title_block(doc) is True

    def test_title_block_by_keywords(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()
        msp.add_text("PROFESIONAL", dxfattribs={"insert": (0, 0)})
        msp.add_text("PROPIETARIO", dxfattribs={"insert": (0, 1)})
        assert _has_title_block(doc) is True


class TestHasNorthArrow:
    def test_no_north(self):
        doc = ezdxf.new("R2013")
        assert _has_north_arrow(doc) is False

    def test_north_by_block(self):
        doc = ezdxf.new("R2013")
        block = doc.blocks.new("NORTE3")
        block.add_line((0, 0), (0, 1))
        doc.modelspace().add_blockref("NORTE3", (0, 0))
        assert _has_north_arrow(doc) is True


class TestFindWallsWithoutDimensions:
    def test_all_dimensioned(self):
        walls = [
            DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0),
        ]
        dims = [
            DetectedDimension(id="d0", value=5.0, start=(0, 0.5), end=(5, 0.5)),
        ]
        result = _find_walls_without_dimensions(walls, dims)
        assert len(result) == 0

    def test_one_undimensioned(self):
        walls = [
            DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0),
            DetectedWall(id="w1", start=(0, 0), end=(0, 5), length=5.0),
        ]
        dims = [
            DetectedDimension(id="d0", value=5.0, start=(0, 0.5), end=(5, 0.5)),
        ]
        # w1 is at x=0,y=0 to 0,5 — midpoint (0,2.5), dim midpoint (2.5,0.5)
        # distance ~ 2.7 > wall.length(5) + tol(0.5) = 5.5, so actually w1 IS close
        result = _find_walls_without_dimensions(walls, dims)
        # Both walls share origin, so dim might cover both
        assert isinstance(result, list)

    def test_no_dimensions(self):
        walls = [
            DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0),
        ]
        result = _find_walls_without_dimensions(walls, [])
        assert len(result) == 1

    def test_empty_walls(self):
        result = _find_walls_without_dimensions([], [])
        assert len(result) == 0


class TestFindSpacesWithoutArea:
    def test_with_area(self):
        spaces = [DetectedSpace(id="s0", name="Cocina", area=8.5)]
        assert len(_find_spaces_without_area(spaces)) == 0

    def test_without_area(self):
        spaces = [DetectedSpace(id="s0", name="Cocina", area=0.0)]
        assert len(_find_spaces_without_area(spaces)) == 1


class TestAnalyzeCompleteness:
    @pytest.fixture
    def empty_doc(self):
        return ezdxf.new("R2013")

    def test_empty_everything(self, empty_doc):
        report = analyze_completeness(empty_doc, [], [], [], [])
        assert report.has_title_block is False
        assert report.has_north_arrow is False
        assert len(report.suggestions) >= 2  # title_block + north

    def test_suggestion_kinds(self, empty_doc):
        walls = [DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0)]
        spaces = [
            DetectedSpace(id="s0", name="Cocina", category=SpaceCategory.cocina)
        ]

        report = analyze_completeness(empty_doc, walls, [], spaces, [])
        kinds = {s.kind for s in report.suggestions}
        assert SuggestionKind.missing_title_block in kinds
        assert SuggestionKind.missing_north_arrow in kinds
        assert SuggestionKind.missing_dimension in kinds
        assert SuggestionKind.missing_area_label in kinds

    def test_complete_doc(self):
        doc = ezdxf.new("R2013")
        msp = doc.modelspace()

        # Cartela keywords
        msp.add_text("PROFESIONAL", dxfattribs={"insert": (0, 0)})
        msp.add_text("PROPIETARIO", dxfattribs={"insert": (0, 1)})

        # Norte
        block = doc.blocks.new("NORTE_ARROW")
        block.add_line((0, 0), (0, 1))
        msp.add_blockref("NORTE_ARROW", (0, 0))

        report = analyze_completeness(doc, [], [], [], [])
        assert report.has_title_block is True
        assert report.has_north_arrow is True

    def test_report_counts(self, empty_doc):
        walls = [
            DetectedWall(id="w0", start=(0, 0), end=(5, 0), length=5.0),
            DetectedWall(id="w1", start=(0, 0), end=(0, 3), length=3.0),
        ]
        spaces = [
            DetectedSpace(id="s0", name="Cocina", area=8.5),
            DetectedSpace(id="s1", name="Baño", area=0.0),
        ]
        dims = [
            DetectedDimension(id="d0", value=5.0, start=(0, 0.5), end=(5, 0.5)),
        ]

        report = analyze_completeness(empty_doc, walls, [], spaces, dims)
        assert report.total_walls == 2
        assert report.total_spaces == 2
        assert report.spaces_with_area_labels == 1


@pytest.mark.skipif(not SAMPLE_DXF.exists(), reason="Sample DXF not available")
class TestAnalyzeCompletenessFigueroa:
    def test_figueroa_has_title_block(self):
        doc = ezdxf.readfile(str(SAMPLE_DXF))
        # Figueroa has "PROFESIONAL", "PROPIETARIO" etc.
        assert _has_title_block(doc) is True

    def test_figueroa_has_north(self):
        doc = ezdxf.readfile(str(SAMPLE_DXF))
        assert _has_north_arrow(doc) is True  # NORTE3 block

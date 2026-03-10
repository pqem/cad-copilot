"""Tests para schemas/annotation.py — DimensionConfig y AnnotationConfig."""

import pytest

from cad_copilot.schemas.annotation import (
    AnnotationConfig,
    DimensionConfig,
    DimensionType,
    AnnotationType,
)


class TestDimensionConfig:
    def test_default_type(self):
        d = DimensionConfig()
        assert d.type == DimensionType.linear

    def test_default_offset(self):
        d = DimensionConfig()
        assert d.offset == pytest.approx(0.5)

    def test_custom_values(self):
        d = DimensionConfig(type=DimensionType.aligned, offset=1.0)
        assert d.type == DimensionType.aligned
        assert d.offset == pytest.approx(1.0)


class TestAnnotationConfig:
    def test_default_north_angle(self):
        a = AnnotationConfig()
        assert a.north_angle == pytest.approx(0.0)

    def test_default_scale(self):
        a = AnnotationConfig()
        assert a.scale == "1:50"

    def test_default_dimensions_none(self):
        a = AnnotationConfig()
        assert a.dimensions is None

    def test_custom_scale(self):
        a = AnnotationConfig(scale="1:100")
        assert a.scale == "1:100"

    def test_with_dimensions(self):
        a = AnnotationConfig(dimensions=DimensionConfig(type=DimensionType.aligned))
        assert a.dimensions is not None
        assert a.dimensions.type == DimensionType.aligned


class TestDimensionType:
    def test_enum_values(self):
        assert DimensionType.linear == "linear"
        assert DimensionType.aligned == "aligned"
        assert DimensionType.angular == "angular"


class TestAnnotationType:
    def test_enum_values(self):
        assert AnnotationType.level_mark == "level_mark"
        assert AnnotationType.north == "north"

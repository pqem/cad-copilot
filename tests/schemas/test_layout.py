"""Tests para schemas/layout.py — PaperConfig y TitleBlock."""

import pytest
from pydantic import ValidationError

from cad_copilot.schemas.layout import PaperConfig, TitleBlock, PaperSize, Orientation


class TestPaperConfig:
    def test_defaults(self):
        p = PaperConfig()
        assert p.size == PaperSize.A2
        assert p.orientation == Orientation.landscape
        assert p.scale == 50
        assert p.margins == (25.0, 5.0, 5.0, 5.0)

    def test_custom_size(self):
        p = PaperConfig(size=PaperSize.A3)
        assert p.size == PaperSize.A3

    def test_portrait_orientation(self):
        p = PaperConfig(orientation=Orientation.portrait)
        assert p.orientation == Orientation.portrait

    def test_scale_must_be_positive(self):
        with pytest.raises(ValidationError):
            PaperConfig(scale=0)

    def test_scale_negative_rejected(self):
        with pytest.raises(ValidationError):
            PaperConfig(scale=-50)

    def test_custom_margins(self):
        p = PaperConfig(margins=(30.0, 10.0, 10.0, 10.0))
        assert p.margins == (30.0, 10.0, 10.0, 10.0)


class TestPaperSize:
    def test_all_sizes(self):
        sizes = list(PaperSize)
        assert len(sizes) == 5
        assert PaperSize.A4 in sizes
        assert PaperSize.A0 in sizes

    def test_string_values(self):
        assert PaperSize.A4 == "A4"
        assert PaperSize.A3 == "A3"


class TestTitleBlock:
    def test_required_fields(self):
        tb = TitleBlock(
            project="VIVIENDA",
            location="PLOTTIER",
            professional="ARQ. TEST",
            license_number="CPTN 999",
            date="2026-01-01",
            drawing_name="PLANTA BAJA",
        )
        assert tb.project == "VIVIENDA"
        assert tb.sheet == "1/1"  # default

    def test_project_required(self):
        with pytest.raises(ValidationError):
            TitleBlock(
                location="PLOTTIER",
                professional="ARQ. TEST",
                license_number="CPTN 999",
                date="2026-01-01",
                drawing_name="PLANTA BAJA",
            )

    def test_default_owner_empty(self):
        tb = TitleBlock(
            project="VIVIENDA",
            location="PLOTTIER",
            professional="ARQ. TEST",
            license_number="CPTN 999",
            date="2026-01-01",
            drawing_name="PLANTA BAJA",
        )
        assert tb.owner == ""

    def test_custom_sheet(self):
        tb = TitleBlock(
            project="VIVIENDA",
            location="PLOTTIER",
            professional="ARQ. TEST",
            license_number="CPTN 999",
            date="2026-01-01",
            drawing_name="PLANTA BAJA",
            sheet="2/3",
        )
        assert tb.sheet == "2/3"

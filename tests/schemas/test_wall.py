"""Tests para schemas/wall.py — Wall y WallClassification."""

import pytest
from pydantic import ValidationError

from cad_copilot.schemas.wall import Wall, WallClassification
from cad_copilot.schemas.opening import Opening, OpeningType


class TestWallDefaults:
    def test_default_thickness(self):
        w = Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0))
        assert w.thickness == pytest.approx(0.15)

    def test_default_classification(self):
        w = Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0))
        assert w.classification == WallClassification.interior

    def test_default_openings_empty(self):
        w = Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0))
        assert w.openings == []


class TestWallFields:
    def test_id_required(self):
        with pytest.raises(ValidationError):
            Wall(start=(0.0, 0.0), end=(5.0, 0.0))

    def test_start_required(self):
        with pytest.raises(ValidationError):
            Wall(id="W1", end=(5.0, 0.0))

    def test_end_required(self):
        with pytest.raises(ValidationError):
            Wall(id="W1", start=(0.0, 0.0))

    def test_thickness_must_be_positive(self):
        with pytest.raises(ValidationError):
            Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0), thickness=0.0)

    def test_thickness_negative_rejected(self):
        with pytest.raises(ValidationError):
            Wall(id="W1", start=(0.0, 0.0), end=(5.0, 0.0), thickness=-0.10)


class TestWallClassifications:
    def test_all_classifications(self):
        for cls in WallClassification:
            w = Wall(id="W1", start=(0.0, 0.0), end=(1.0, 0.0), classification=cls)
            assert w.classification == cls

    def test_exterior_portante(self):
        w = Wall(
            id="W1",
            start=(0.0, 0.0),
            end=(6.0, 0.0),
            classification=WallClassification.exterior_portante,
        )
        assert w.classification == WallClassification.exterior_portante

    def test_medianera(self):
        w = Wall(
            id="W1",
            start=(0.0, 0.0),
            end=(6.0, 0.0),
            classification=WallClassification.medianera,
        )
        assert w.classification == WallClassification.medianera


class TestWallWithOpenings:
    def test_wall_accepts_openings(self):
        door = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        w = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), openings=[door])
        assert len(w.openings) == 1

    def test_wall_with_multiple_openings(self):
        door = Opening(type=OpeningType.door, width=0.90, position_along_wall=1.0)
        window = Opening(type=OpeningType.window, width=1.50, position_along_wall=3.0)
        w = Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), openings=[door, window])
        assert len(w.openings) == 2

    def test_wall_diagonal(self):
        """Muro diagonal es válido."""
        w = Wall(id="W1", start=(0.0, 0.0), end=(3.0, 4.0))
        assert w.start == (0.0, 0.0)
        assert w.end == (3.0, 4.0)

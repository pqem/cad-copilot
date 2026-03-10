"""Tests para engine/spaces.py — calculate_space_area, _space_centroid, add_space_labels."""

import pytest

from cad_copilot.engine.spaces import calculate_space_area, _space_centroid, add_space_labels
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.wall import Wall, WallClassification


@pytest.fixture
def square_walls():
    """4 muros formando un cuadrado de 4x4m."""
    return [
        Wall(id="W1", start=(0.0, 0.0), end=(4.0, 0.0), thickness=0.15),
        Wall(id="W2", start=(4.0, 0.0), end=(4.0, 4.0), thickness=0.15),
        Wall(id="W3", start=(4.0, 4.0), end=(0.0, 4.0), thickness=0.15),
        Wall(id="W4", start=(0.0, 4.0), end=(0.0, 0.0), thickness=0.15),
    ]


@pytest.fixture
def square_space(square_walls):
    return Space(
        id="S1",
        name="AMBIENTE",
        function=SpaceFunction.living,
        bounded_by=["W1", "W2", "W3", "W4"],
    )


class TestCalculateSpaceArea:
    def test_square_area_16(self, square_space, square_walls):
        area = calculate_space_area(square_space, square_walls)
        assert area == pytest.approx(16.0)

    def test_rectangle_area(self):
        walls = [
            Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.15),
            Wall(id="W2", start=(6.0, 0.0), end=(6.0, 4.0), thickness=0.15),
            Wall(id="W3", start=(6.0, 4.0), end=(0.0, 4.0), thickness=0.15),
            Wall(id="W4", start=(0.0, 4.0), end=(0.0, 0.0), thickness=0.15),
        ]
        space = Space(
            id="S1",
            name="LIVING",
            function=SpaceFunction.living,
            bounded_by=["W1", "W2", "W3", "W4"],
        )
        area = calculate_space_area(space, walls)
        assert area == pytest.approx(24.0)

    def test_area_with_missing_walls_returns_zero(self):
        space = Space(
            id="S1",
            name="X",
            function=SpaceFunction.otro,
            bounded_by=["INEXISTENTE"],
        )
        area = calculate_space_area(space, [])
        assert area == pytest.approx(0.0)

    def test_area_with_two_walls_returns_zero(self):
        """Menos de 3 muros no forman polígono."""
        walls = [
            Wall(id="W1", start=(0.0, 0.0), end=(4.0, 0.0), thickness=0.15),
            Wall(id="W2", start=(4.0, 0.0), end=(4.0, 4.0), thickness=0.15),
        ]
        space = Space(
            id="S1",
            name="X",
            function=SpaceFunction.otro,
            bounded_by=["W1", "W2"],
        )
        area = calculate_space_area(space, walls)
        assert area == pytest.approx(0.0)


class TestSpaceCentroid:
    def test_centroid_square(self, square_space, square_walls):
        cx, cy = _space_centroid(square_space, square_walls)
        assert cx == pytest.approx(2.0)
        assert cy == pytest.approx(2.0)

    def test_centroid_with_missing_walls(self):
        """Fallback cuando no se puede calcular el polígono."""
        walls = [
            Wall(id="W1", start=(0.0, 0.0), end=(2.0, 0.0), thickness=0.15),
            Wall(id="W2", start=(2.0, 0.0), end=(2.0, 2.0), thickness=0.15),
        ]
        space = Space(
            id="S1",
            name="X",
            function=SpaceFunction.otro,
            bounded_by=["W1", "W2"],
        )
        cx, cy = _space_centroid(space, walls)
        # Fallback: promedio de start points (0,0) y (2,0)
        assert cx == pytest.approx(1.0)
        assert cy == pytest.approx(0.0)


class TestAddSpaceLabels:
    def test_adds_mtext_for_each_space(self, doc, msp, square_space, square_walls):
        add_space_labels(msp, [square_space], square_walls)
        mtexts = [e for e in msp if e.dxftype() == "MTEXT"]
        assert len(mtexts) == 1

    def test_mtext_contains_name(self, doc, msp, square_space, square_walls):
        add_space_labels(msp, [square_space], square_walls)
        mtexts = [e for e in msp if e.dxftype() == "MTEXT"]
        assert "AMBIENTE" in mtexts[0].dxf.text

    def test_mtext_on_correct_layer(self, doc, msp, square_space, square_walls):
        add_space_labels(msp, [square_space], square_walls)
        mtexts = [e for e in msp if e.dxftype() == "MTEXT"]
        assert mtexts[0].dxf.layer == "A-ANNO-TEXT"

    def test_no_spaces_no_mtext(self, doc, msp, square_walls):
        add_space_labels(msp, [], square_walls)
        mtexts = [e for e in msp if e.dxftype() == "MTEXT"]
        assert len(mtexts) == 0

    def test_multiple_spaces_multiple_mtexts(self, doc, msp, square_walls):
        spaces = [
            Space(id="S1", name="LIVING", function=SpaceFunction.living, bounded_by=["W1", "W2", "W3", "W4"]),
            Space(id="S2", name="DORMITORIO", function=SpaceFunction.dormitorio, bounded_by=["W1", "W2", "W3", "W4"]),
        ]
        add_space_labels(msp, spaces, square_walls)
        mtexts = [e for e in msp if e.dxftype() == "MTEXT"]
        assert len(mtexts) == 2

"""Fixtures compartidas para toda la suite de tests de cad_copilot."""

import pytest
import ezdxf

from cad_copilot.schemas.opening import Opening, OpeningType, OpeningMechanism
from cad_copilot.schemas.wall import Wall, WallClassification
from cad_copilot.schemas.space import Space, SpaceFunction
from cad_copilot.schemas.annotation import AnnotationConfig, DimensionConfig
from cad_copilot.schemas.layout import PaperConfig, TitleBlock, PaperSize, Orientation
from cad_copilot.schemas.project import FloorPlan
from cad_copilot.engine.document import create_document


@pytest.fixture
def doc():
    """Documento DXF base creado con create_document (escala 1:50)."""
    return create_document(scale=50)


@pytest.fixture
def msp(doc):
    """Model Space del documento DXF base."""
    return doc.modelspace()


@pytest.fixture
def raw_doc():
    """Documento ezdxf sin configurar (para tests de standards)."""
    return ezdxf.new("R2013", setup=True)


@pytest.fixture
def simple_door():
    """Puerta abatible 0.90m con defaults."""
    return Opening(
        type=OpeningType.door,
        width=0.90,
        position_along_wall=1.0,
    )


@pytest.fixture
def simple_window():
    """Ventana corrediza 1.50m con defaults."""
    return Opening(
        type=OpeningType.window,
        width=1.50,
        position_along_wall=2.0,
    )


@pytest.fixture
def wall_horizontal():
    """Muro horizontal exterior de 6m."""
    return Wall(
        id="W1",
        start=(0.0, 0.0),
        end=(6.0, 0.0),
        thickness=0.30,
        classification=WallClassification.exterior_portante,
    )


@pytest.fixture
def wall_with_door():
    """Muro horizontal con una puerta abatible."""
    return Wall(
        id="W1",
        start=(0.0, 0.0),
        end=(6.0, 0.0),
        thickness=0.30,
        classification=WallClassification.exterior_portante,
        openings=[
            Opening(
                type=OpeningType.door,
                width=0.90,
                position_along_wall=1.0,
            )
        ],
    )


@pytest.fixture
def wall_with_window():
    """Muro horizontal con una ventana corrediza."""
    return Wall(
        id="W2",
        start=(0.0, 0.0),
        end=(6.0, 0.0),
        thickness=0.30,
        classification=WallClassification.exterior_portante,
        openings=[
            Opening(
                type=OpeningType.window,
                width=1.50,
                position_along_wall=2.0,
            )
        ],
    )


@pytest.fixture
def four_walls():
    """Cuatro muros formando un rectángulo 6x4m."""
    return [
        Wall(id="W1", start=(0.0, 0.0), end=(6.0, 0.0), thickness=0.30,
             classification=WallClassification.exterior_portante),
        Wall(id="W2", start=(6.0, 0.0), end=(6.0, 4.0), thickness=0.30,
             classification=WallClassification.exterior_portante),
        Wall(id="W3", start=(6.0, 4.0), end=(0.0, 4.0), thickness=0.30,
             classification=WallClassification.exterior_portante),
        Wall(id="W4", start=(0.0, 4.0), end=(0.0, 0.0), thickness=0.30,
             classification=WallClassification.exterior_portante),
    ]


@pytest.fixture
def simple_space(four_walls):
    """Espacio delimitado por los cuatro muros del rectángulo."""
    return Space(
        id="S1",
        name="LIVING-COMEDOR",
        function=SpaceFunction.living,
        bounded_by=["W1", "W2", "W3", "W4"],
    )


@pytest.fixture
def title_block():
    """Cartela de ejemplo."""
    return TitleBlock(
        project="VIVIENDA UNIFAMILIAR",
        drawing_name="PLANTA BAJA",
        location="PLOTTIER, NEUQUEN",
        professional="ARQ. PABLO QUEVEDO",
        license_number="CPTN 1234",
        date="2026-03-10",
        sheet="1/1",
    )


@pytest.fixture
def paper_config():
    """Configuración de papel A3 landscape 1:50."""
    return PaperConfig(
        size=PaperSize.A3,
        orientation=Orientation.landscape,
        scale=50,
        margins=(25.0, 10.0, 10.0, 10.0),
    )


@pytest.fixture
def floor_plan(four_walls, simple_space, title_block, paper_config):
    """FloorPlan completo para tests de integración."""
    return FloorPlan(
        walls=four_walls,
        spaces=[simple_space],
        title_block=title_block,
        paper_config=paper_config,
    )

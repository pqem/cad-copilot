"""Creacion y configuracion del documento DXF base."""

import ezdxf
from ezdxf.document import Drawing

from cad_copilot.standards import (
    setup_dimstyles,
    setup_layers,
    setup_linetypes,
    setup_textstyles,
)


def create_document(version: str = "R2013", scale: int = 50) -> Drawing:
    """Crea un documento DXF configurado para planos arquitectonicos.

    Args:
        version: Version DXF (default R2013 para maxima compatibilidad).
        scale: Denominador de escala (50 para 1:50, 100 para 1:100).

    Returns:
        Documento ezdxf listo para dibujar.
    """
    doc = ezdxf.new(version, setup=True)

    # Configurar variables de encabezado
    doc.header["$INSUNITS"] = 6  # Metros
    doc.header["$MEASUREMENT"] = 1  # Metrico
    doc.header["$LUNITS"] = 2  # Decimal
    doc.header["$LUPREC"] = 2  # 2 decimales

    # Aplicar standards
    setup_layers(doc)
    setup_dimstyles(doc, scale=scale)
    setup_textstyles(doc)
    setup_linetypes(doc)

    return doc

"""Tipos de línea estándar para planos arquitectónicos.

ezdxf con setup=True ya carga los tipos de línea básicos (CENTER, DASHED, etc.).
Este módulo define las descripciones en español y verifica que existan en el documento.
"""

from __future__ import annotations

from ezdxf.document import Drawing

# Tipos de línea estándar con su descripción en español.
# ezdxf los crea automáticamente al usar ezdxf.new(..., setup=True).
LINETYPES: dict[str, str] = {
    "CENTER": "Centro ____ _ ____ _ ____",
    "DASHED": "Trazos _ _ _ _ _ _",
    "PHANTOM": "Fantasma ____ _ _ ____ _ _",
    "DASHDOT": "Trazo punto _._._._",
}

# Alias: en AutoCAD "HIDDEN" existe, en ezdxf setup=True se llama "DASHED"
LINETYPE_ALIASES: dict[str, str] = {
    "HIDDEN": "DASHED",
}


def setup_linetypes(doc: Drawing) -> None:
    """Verifica que los tipos de línea estándar existan en el documento DXF.

    Los tipos de línea se crean automáticamente cuando el documento se genera
    con ``ezdxf.new(setup=True)``. Esta función solo verifica su existencia
    y emite un warning si falta alguno.

    Args:
        doc: Documento ezdxf donde verificar los tipos de línea.

    Raises:
        ValueError: Si falta algún tipo de línea requerido y el documento
            no fue creado con setup=True.
    """
    missing: list[str] = []
    for name in LINETYPES:
        if name not in doc.linetypes:
            missing.append(name)

    if missing:
        raise ValueError(
            f"Faltan tipos de línea en el documento: {', '.join(missing)}. "
            "Asegurate de crear el documento con ezdxf.new(setup=True)."
        )

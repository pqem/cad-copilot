"""Generador de tabla normativa DXF para Paper Space.

Genera una tabla DXF formateada con las verificaciones normativas del
Código de Edificación de Neuquén/Plottier, lista para insertar en el
Paper Space del plano y presentar al municipio.
"""

from __future__ import annotations

import ezdxf
from ezdxf.document import Drawing

from cad_copilot.standards.norms import ResultadoNormas


# ---------------------------------------------------------------------------
# Dimensiones de la tabla (en milímetros — Paper Space)
# ---------------------------------------------------------------------------

COL_W_DESCRIPCION = 70.0   # mm — columna "Ítem"
COL_W_VALOR = 30.0         # mm — columna "Calculado"
COL_W_MINIMO = 30.0        # mm — columna "Mínimo/Máximo"
COL_W_ESTADO = 22.0        # mm — columna "Estado"
ROW_H = 6.0                # mm — alto de fila
ROW_H_HEADER = 8.0         # mm — alto de fila encabezado
FONT_HEIGHT = 2.5          # mm — altura de texto
FONT_HEIGHT_TITLE = 3.5    # mm — altura de título
TOTAL_W = COL_W_DESCRIPCION + COL_W_VALOR + COL_W_MINIMO + COL_W_ESTADO


def _draw_cell(
    msp: ezdxf.layouts.BaseLayout,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    layer: str = "A-ANNO-TEXT",
    text_height: float = FONT_HEIGHT,
    bold: bool = False,
    align: str = "LEFT",
    margin: float = 2.0,
) -> None:
    """Dibuja una celda con borde y texto."""
    # Borde de la celda
    msp.add_lwpolyline(
        [(x, y), (x + w, y), (x + w, y - h), (x, y - h)],
        close=True,
        dxfattribs={"layer": "A-ANNO-TTLB"},
    )

    # Texto dentro de la celda
    if not text:
        return

    # Calcular posición del texto según alineación
    if align == "CENTER":
        tx = x + w / 2
        ty = y - h / 2
        attachment = 5  # Middle Center
    elif align == "RIGHT":
        tx = x + w - margin
        ty = y - h / 2
        attachment = 6  # Middle Right
    else:  # LEFT
        tx = x + margin
        ty = y - h / 2
        attachment = 4  # Middle Left

    style = "Titulo" if bold else "Standard"

    msp.add_mtext(
        text,
        dxfattribs={
            "layer": layer,
            "style": style,
            "char_height": text_height,
            "insert": (tx, ty),
            "attachment_point": attachment,
            "width": w - 2 * margin,
        },
    )


def generate_norm_table_dxf(
    resultado: ResultadoNormas,
    output_path: str,
    insert_x: float = 0.0,
    insert_y: float = 0.0,
) -> str:
    """Genera un DXF con la tabla normativa formateada para Paper Space.

    La tabla está diseñada para insertarse en el Paper Space del plano
    principal. Coordenadas en milímetros (Paper Space).

    Args:
        resultado: Resultado de calcular_normas().
        output_path: Ruta donde guardar el DXF de la tabla.
        insert_x: Coordenada X de inserción de la tabla (mm).
        insert_y: Coordenada Y de inserción de la tabla (mm).

    Returns:
        Ruta del archivo DXF generado.
    """
    import pathlib

    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4  # mm en Paper Space
    msp = doc.modelspace()

    # Configurar layers si no existen
    _ensure_layers(doc)

    x = insert_x
    y = insert_y

    # ─── Título principal ────────────────────────────────────────────────────
    titulo = "VERIFICACIÓN NORMATIVA — CÓD. EDIFICACIÓN NEUQUÉN/PLOTTIER"
    _draw_cell(
        msp, x, y, TOTAL_W, ROW_H_HEADER + 2,
        titulo,
        layer="A-ANNO-TTLB",
        text_height=FONT_HEIGHT_TITLE,
        bold=True,
        align="CENTER",
    )
    y -= ROW_H_HEADER + 2

    estado_general = "CUMPLE" if resultado.cumple_todo else "NO CUMPLE"
    sub_titulo = f"Proyecto: {resultado.proyecto or '(sin nombre)'}    Estado general: {estado_general}"
    _draw_cell(
        msp, x, y, TOTAL_W, ROW_H,
        sub_titulo,
        text_height=FONT_HEIGHT,
        align="LEFT",
    )
    y -= ROW_H

    # ─── Encabezados de columna ──────────────────────────────────────────────
    y -= 2  # espacio antes de tabla
    headers = ["ÍTEM", "CALCULADO", "MÍN/MÁX", "ESTADO"]
    col_widths = [COL_W_DESCRIPCION, COL_W_VALOR, COL_W_MINIMO, COL_W_ESTADO]

    cx = x
    for header, cw in zip(headers, col_widths):
        _draw_cell(msp, cx, y, cw, ROW_H_HEADER, header, bold=True, align="CENTER")
        cx += cw
    y -= ROW_H_HEADER

    # ─── Filas de ambientes ──────────────────────────────────────────────────
    for amb in resultado.ambientes:
        # Sub-encabezado de ambiente
        area_str = f"{amb.area_m2:.2f} m²"
        amb_header = f"{amb.space_name} ({amb.function}) — Área: {area_str}"
        _draw_cell(
            msp, x, y, TOTAL_W, ROW_H,
            amb_header,
            text_height=FONT_HEIGHT,
            bold=True,
            align="LEFT",
        )
        y -= ROW_H

        # Ítems del ambiente
        for item in amb.items:
            if item.valor_minimo == 0.0 and item.cumple:
                # Omitir ítems sin requisito
                continue

            cx = x
            estado_txt = "CUMPLE" if item.cumple else "NO CUMPLE"
            layer_estado = "A-ANNO-TEXT" if item.cumple else "A-ANNO-TEXT"

            _draw_cell(msp, cx, y, COL_W_DESCRIPCION, ROW_H, f"  {item.descripcion}")
            cx += COL_W_DESCRIPCION

            _draw_cell(msp, cx, y, COL_W_VALOR, ROW_H, f"{item.valor_calculado:.3f}", align="RIGHT")
            cx += COL_W_VALOR

            _draw_cell(msp, cx, y, COL_W_MINIMO, ROW_H, f"{item.valor_minimo:.3f}", align="RIGHT")
            cx += COL_W_MINIMO

            _draw_cell(msp, cx, y, COL_W_ESTADO, ROW_H, estado_txt, align="CENTER", layer=layer_estado)
            y -= ROW_H

    # ─── Sección FOS/FOT ─────────────────────────────────────────────────────
    if resultado.terreno:
        y -= 2
        _draw_cell(
            msp, x, y, TOTAL_W, ROW_H,
            "OCUPACIÓN DEL SUELO",
            bold=True,
            align="LEFT",
        )
        y -= ROW_H

        t = resultado.terreno
        fos_fot_data = [
            ("  FOS (Ocup. Suelo)", t.fos_calculado, t.fos_max, t.items[0].cumple if t.items else True),
            ("  FOT (Ocup. Total)", t.fot_calculado, t.fot_max, t.items[1].cumple if len(t.items) > 1 else True),
        ]

        for desc, calc, maximo, cumple in fos_fot_data:
            cx = x
            _draw_cell(msp, cx, y, COL_W_DESCRIPCION, ROW_H, desc)
            cx += COL_W_DESCRIPCION
            _draw_cell(msp, cx, y, COL_W_VALOR, ROW_H, f"{calc:.3f}", align="RIGHT")
            cx += COL_W_VALOR
            _draw_cell(msp, cx, y, COL_W_MINIMO, ROW_H, f"≤ {maximo:.3f}", align="RIGHT")
            cx += COL_W_MINIMO
            estado_txt = "CUMPLE" if cumple else "NO CUMPLE"
            _draw_cell(msp, cx, y, COL_W_ESTADO, ROW_H, estado_txt, align="CENTER")
            y -= ROW_H

    # ─── Nota al pie ─────────────────────────────────────────────────────────
    y -= 2
    nota = (
        "Verificación orientativa. Confirmar con municipio antes de presentar legajo. "
        "Valores según Cód. Edificación Neuquén/Plottier."
    )
    _draw_cell(
        msp, x, y, TOTAL_W, ROW_H,
        nota,
        text_height=FONT_HEIGHT - 0.5,
        align="LEFT",
    )

    doc.saveas(output_path)
    return output_path


def _ensure_layers(doc: Drawing) -> None:
    """Crea los layers necesarios si no existen."""
    layers_needed = {
        "A-ANNO-TEXT": {"color": 7},    # blanco/negro
        "A-ANNO-TTLB": {"color": 7},    # bordes tabla
    }
    for name, attrs in layers_needed.items():
        if name not in doc.layers:
            doc.layers.new(name=name, dxfattribs=attrs)

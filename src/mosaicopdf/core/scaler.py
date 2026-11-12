"""
Cálculo de escalado vectorial previo a la generación del mosaico.

Permite tanto reducir planos grandes como el efecto inverso: ampliar diseños
pequeños (Carta, Oficio, A4, etc.) a gran formato o a una cuadrícula mural
conservando el 100% de la geometría vectorial.
"""

from __future__ import annotations

import math

from mosaicopdf.models.mosaic_settings import MosaicSettings
from mosaicopdf.models.paper import Paper
from mosaicopdf.models.scale_spec import ScaleResult, ScaleSpec
from mosaicopdf.utils.units import format_dimensions_mm


class ScaleCalculator:
    """Calcula el factor de escala y las dimensiones virtuales de una página."""

    @staticmethod
    def calculate(
        source_width: float,
        source_height: float,
        spec: ScaleSpec,
        paper: Paper | None = None,
        settings: MosaicSettings | None = None,
    ) -> ScaleResult:
        """
        Resuelve ``ScaleSpec`` sobre ``(source_width, source_height)``.
        """
        if source_width <= 0 or source_height <= 0:
            raise ValueError("Las dimensiones de la página origen deben ser positivas.")

        if spec.mode == "original":
            return ScaleResult(
                source_width=source_width,
                source_height=source_height,
                virtual_width=source_width,
                virtual_height=source_height,
                scale_factor=1.0,
                description="Escala original 1:1 (100%)",
            )

        if spec.mode == "factor":
            if spec.factor <= 0:
                raise ValueError("El factor de escala debe ser mayor que cero.")
            return ScaleResult(
                source_width=source_width,
                source_height=source_height,
                virtual_width=source_width * spec.factor,
                virtual_height=source_height * spec.factor,
                scale_factor=spec.factor,
                description=f"Factor manual ({spec.factor * 100:.1f}%)",
            )

        if spec.mode == "target_width":
            if not spec.target_width or spec.target_width <= 0:
                raise ValueError("El ancho objetivo debe ser mayor que cero.")
            factor = spec.target_width / source_width
            return ScaleResult(
                source_width=source_width,
                source_height=source_height,
                virtual_width=source_width * factor,
                virtual_height=source_height * factor,
                scale_factor=factor,
                description=(
                    f"Ajuste por ancho objetivo "
                    f"({format_dimensions_mm(source_width * factor, source_height * factor)})"
                ),
            )

        if spec.mode == "target_height":
            if not spec.target_height or spec.target_height <= 0:
                raise ValueError("El alto objetivo debe ser mayor que cero.")
            factor = spec.target_height / source_height
            return ScaleResult(
                source_width=source_width,
                source_height=source_height,
                virtual_width=source_width * factor,
                virtual_height=source_height * factor,
                scale_factor=factor,
                description=(
                    f"Ajuste por alto objetivo "
                    f"({format_dimensions_mm(source_width * factor, source_height * factor)})"
                ),
            )

        if spec.mode == "target_size":
            if (
                not spec.target_width
                or not spec.target_height
                or spec.target_width <= 0
                or spec.target_height <= 0
            ):
                raise ValueError("Las dimensiones objetivo deben ser mayores que cero.")

            factor = _fit_into_box(
                src_w=source_width,
                src_h=source_height,
                box_w=spec.target_width,
                box_h=spec.target_height,
                fit_mode=spec.fit_mode,
                auto_rotate=spec.auto_rotate_target,
            )
            vw = source_width * factor
            vh = source_height * factor
            return ScaleResult(
                source_width=source_width,
                source_height=source_height,
                virtual_width=vw,
                virtual_height=vh,
                scale_factor=factor,
                description=(
                    f"Escalado a formato objetivo {format_dimensions_mm(vw, vh)} "
                    f"({factor * 100:.1f}%)"
                ),
            )

        if spec.mode == "grid":
            if paper is None or settings is None:
                raise ValueError(
                    "El escalado por cuadrícula requiere indicar papel y configuración."
                )
            if (
                not spec.grid_columns
                or not spec.grid_rows
                or spec.grid_columns < 1
                or spec.grid_rows < 1
            ):
                raise ValueError("Las filas y columnas de la cuadrícula deben ser >= 1.")

            factor = _fit_into_grid(
                src_w=source_width,
                src_h=source_height,
                paper=paper,
                settings=settings,
                columns=spec.grid_columns,
                rows=spec.grid_rows,
            )
            vw = source_width * factor
            vh = source_height * factor
            return ScaleResult(
                source_width=source_width,
                source_height=source_height,
                virtual_width=vw,
                virtual_height=vh,
                scale_factor=factor,
                description=(
                    f"Mural ajustado a cuadrícula {spec.grid_columns}x{spec.grid_rows} "
                    f"({factor * 100:.1f}%)"
                ),
            )

        raise ValueError(f"Modo de escala no soportado: '{spec.mode}'.")


def _fit_into_box(
    src_w: float,
    src_h: float,
    box_w: float,
    box_h: float,
    fit_mode: str,
    auto_rotate: bool,
) -> float:
    """Calcula el factor proporcional óptimo dentro de un rectángulo objetivo."""
    candidates = [(box_w, box_h)]
    if auto_rotate and not math.isclose(box_w, box_h):
        candidates.append((box_h, box_w))

    factors: list[float] = []
    for bw, bh in candidates:
        rx = bw / src_w
        ry = bh / src_h
        factors.append(min(rx, ry) if fit_mode == "contain" else max(rx, ry))

    return max(factors) if fit_mode == "contain" else min(factors)


def _fit_into_grid(
    src_w: float,
    src_h: float,
    paper: Paper,
    settings: MosaicSettings,
    columns: int,
    rows: int,
) -> float:
    """Calcula el factor proporcional máximo para llenar exactamente ``columns x rows``."""
    orientations = (
        ("portrait", "landscape")
        if settings.orientation == "auto"
        else (settings.orientation,)
    )
    best_factor = 0.0
    for orient in orientations:
        oriented_paper = paper.oriented(orient)
        pw = settings.printer_profile.printable_width(oriented_paper)
        ph = settings.printer_profile.printable_height(oriented_paper)
        step_x = pw - settings.overlap_x
        step_y = ph - settings.overlap_y
        if step_x <= 0 or step_y <= 0:
            continue
        grid_w = pw + (columns - 1) * step_x
        grid_h = ph + (rows - 1) * step_y
        factor = min(grid_w / src_w, grid_h / src_h)
        if factor > best_factor:
            best_factor = factor

    if best_factor <= 0:
        raise ValueError(
            "La solapa configurada es igual o mayor que el área imprimible del papel."
        )
    return best_factor

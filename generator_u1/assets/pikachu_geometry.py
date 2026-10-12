"""
Modulo geometrie 2D parametriche FDM per Coda a Fulmine Pikachu Ufficiale (Snapmaker U1).
Geometrie chiuse, manifold 100%, modellate fedelmente 1:1 dall'asset ufficiale:
- Icon_Pikachu_Tail_Body (Giallo Pikachu #FFCB05): corpo superiore a fulmine
- Icon_Pikachu_Tail_Base (Nero / Marrone #1A1A1A): base d'attacco con demarcazione a scalino
"""
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely import affinity
from typing import Tuple, Any

# Coordinate originali 1:1 dall'asset di riferimento
RAW_YELLOW_PTS = [
    (72, 45), (53, 118), (115, 136), (117, 172), (156, 181),
    (158, 208), (178, 218), (180, 200), (194, 205), (188, 191),
    (212, 195), (204, 182), (205, 151), (175, 141), (187, 94)
]
RAW_BROWN_PTS = [
    (178, 218), (182, 236), (200, 239), (244, 238), (247, 232),
    (218, 212), (220, 195), (212, 195), (188, 191), (194, 205), (180, 200)
]

_GEOM_BODY = None
_GEOM_BASE = None
_GEOM_FULL = None

def _init_geometries():
    global _GEOM_BODY, _GEOM_BASE, _GEOM_FULL
    if _GEOM_FULL is not None:
        return
    y_raw = sg.Polygon(RAW_YELLOW_PTS).buffer(0)
    b_raw = sg.Polygon(RAW_BROWN_PTS).buffer(0)
    full_raw = unary_union([y_raw, b_raw]).buffer(0)

    minx, miny, maxx, maxy = full_raw.bounds
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0

    # Invert Y per sistema cartesiano 3D (Y positivo in alto) e centra sull'origine (0, 0)
    _GEOM_BODY = affinity.scale(affinity.translate(y_raw, xoff=-cx, yoff=-cy), yfact=-1.0, origin=(0, 0))
    _GEOM_BASE = affinity.scale(affinity.translate(b_raw, xoff=-cx, yoff=-cy), yfact=-1.0, origin=(0, 0))
    _GEOM_FULL = unary_union([_GEOM_BODY, _GEOM_BASE]).buffer(0)

def get_pikachu_tail_components(target_h: float = 16.0) -> Tuple[Any, Any, Any]:
    """
    Restituisce (tail_body, tail_base, full_silhouette) scalati all'altezza target_h (mm).
    Tutte le geometrie sono centrate sull'origine (0, 0).
    """
    _init_geometries()
    minx, miny, maxx, maxy = _GEOM_FULL.bounds
    curr_h = maxy - miny
    s = target_h / curr_h if curr_h > 0 else 1.0

    body_s = affinity.scale(_GEOM_BODY, xfact=s, yfact=s, origin=(0, 0))
    base_s = affinity.scale(_GEOM_BASE, xfact=s, yfact=s, origin=(0, 0))
    full_s = affinity.scale(_GEOM_FULL, xfact=s, yfact=s, origin=(0, 0))

    return body_s, base_s, full_s

def get_pikachu_modular_components(target_h: float = 16.0) -> Tuple[Any, Any, Any]:
    """Alias di compatibilità per get_pikachu_tail_components."""
    return get_pikachu_tail_components(target_h=target_h)

def get_pikachu_geometry(target_h: float = 16.0) -> Any:
    """Restituisce la sagoma completa della coda a fulmine centrata all'origine."""
    _, _, full_s = get_pikachu_tail_components(target_h=target_h)
    return full_s

"""
Modulo geometrico per il portachiavi a forma di Cuore con scritta "HUNTRIX"
ottimizzato per la stampa 3D FDM su Snapmaker U1 (nozzle 0.4 mm).

Specifiche dimensionali e tolleranze:
- Base a cuore parametrico: larghezza ~52.0 mm, altezza ~51.8 mm, spessore Z = 3.00 mm.
- Occhiello anello sul lobo sinistro: diametro foro 3.8 mm, parete >= 2.2 mm (2.3 mm).
- Scritta "HUNTRIX" con font Huntrix: rilievo Z +1.20 mm, compenetrazione Z 0.40 mm (Z totale = 4.20 mm).
- Tratti minimi delle lettere >= 0.85 mm per estrusione solida a 2 perimetri continui.
"""
from typing import Dict, Any, Tuple
from pathlib import Path
import numpy as np
import trimesh
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
import matplotlib.textpath as tp
import matplotlib.font_manager as fm

from generator_u1.font_resolver import resolve_font_path


def get_heart_2d_geometry(target_width: float = 52.0) -> Polygon:
    """
    Genera la curva parametrica a cuore con asola portachiavi integrata
    sul lobo superiore sinistro.
    """
    t = np.linspace(0, 2 * np.pi, 250, endpoint=False)
    # Curva parametrica standard a cuore
    x_raw = 16.0 * np.sin(t) ** 3
    y_raw = 13.0 * np.cos(t) - 5.0 * np.cos(2 * t) - 2.0 * np.cos(3 * t) - np.cos(4 * t)

    raw_poly = Polygon(zip(x_raw, y_raw))
    raw_w = raw_poly.bounds[2] - raw_poly.bounds[0]

    scale = target_width / raw_w
    heart = affinity.scale(raw_poly, xfact=scale, yfact=scale, origin=(0, 0))

    # Parametri occhiello rinforzato FDM
    r_inner = 1.9  # Diametro foro netto 3.8 mm
    r_outer = 4.2  # Spessore parete 2.3 mm >= 2.2 mm

    # Posizionamento occhiello sul lobo superiore sinistro
    c_eyelet = Point(-13.5 * (target_width / 52.0), 20.0 * (target_width / 52.0))
    eyelet_outer = c_eyelet.buffer(r_outer, resolution=64)
    eyelet_inner = c_eyelet.buffer(r_inner, resolution=64)

    base_2d = unary_union([heart, eyelet_outer]).difference(eyelet_inner)
    return base_2d


def get_huntrix_text_2d_geometry(text: str = "HUNTRIX", target_width: float = 36.0) -> MultiPolygon:
    """
    Genera la geometria 2D della scritta HUNTRIX centrata e con buffer
    per garantire spessori minimi >= 0.85 mm per nozzle da 0.4 mm.
    """
    font_file = resolve_font_path("Huntrix")
    if not font_file:
        # Fallback percorso locale
        base_dir = Path(__file__).resolve().parent.parent
        font_file = str(base_dir / "assets" / "fonts" / "Huntrix.otf")

    fp = fm.FontProperties(fname=font_file)
    path = tp.TextPath((0, 0), text, size=10, prop=fp)
    
    # Estrazione poligoni con gestione fori
    raw_polys = [Polygon(p) for p in path.to_polygons() if len(p) >= 3]
    outers = []
    holes = []
    for p in raw_polys:
        if any(other.contains(p) for other in raw_polys if other != p):
            holes.append(p)
        else:
            outers.append(p)

    final_polys = []
    for outer in outers:
        my_holes = [h.exterior.coords for h in holes if outer.contains(h)]
        try:
            poly = Polygon(outer.exterior.coords, my_holes)
            if not poly.is_valid:
                poly = poly.buffer(0)
            final_polys.append(poly)
        except Exception:
            poly = Polygon(outer.exterior.coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            final_polys.append(poly)

    raw_text = unary_union(final_polys)
    current_w = raw_text.bounds[2] - raw_text.bounds[0]
    scale = target_width / current_w
    text_scaled = affinity.scale(raw_text, xfact=scale, yfact=scale, origin=raw_text.centroid)
    
    # Buffer di dilatazione 0.22 mm per raggiungere spessori >= 0.85 mm su tutte le lettere
    text_buffered = text_scaled.buffer(0.22, resolution=32)

    # Centratura ottica all'interno del corpo del cuore (y visuale attorno a +1.5 mm)
    tb = text_buffered.bounds
    tc_x = (tb[0] + tb[2]) / 2.0
    tc_y = (tb[1] + tb[3]) / 2.0
    text_centered = affinity.translate(text_buffered, xoff=-tc_x, yoff=1.5 - tc_y)

    return text_centered


def get_heart_huntrix_geometries(
    target_width: float = 52.0,
    text: str = "HUNTRIX"
) -> Dict[str, Any]:
    """
    Restituisce il dizionario con le geometrie 2D Shapely
    per la base a cuore e la scritta centrale.
    """
    base_2d = get_heart_2d_geometry(target_width=target_width)
    text_w = target_width * (36.0 / 52.0)
    text_2d = get_huntrix_text_2d_geometry(text=text, target_width=text_w)

    return {
        "base": base_2d,
        "text": text_2d
    }

"""
Modulo geometrico per il portachiavi a cuore con scritta centrale "HUNTRIX"
ottimizzato per la stampa 3D FDM su Snapmaker U1 (ugello 0.4 mm).

Specifiche di progetto:
1. Profilo a cuore raccordato:
   - Curve Bézier armoniose e lobi superiori pieni e simmetrici.
   - Cuspide inferiore smussata con arco di raccordo R = 2.5 mm (>= 2.0 mm).
   - Larghezza cuore principale ~48.0 mm, altezza ~42.0 mm.
2. Base di supporto (Base_Slab):
   - Offset perimetrale morbido di +2.0 mm attorno al cuore (larghezza totale 52.0 mm).
   - Asola portachiavi integrata al CENTRO (X=0), innestata nella gola tra i lobi.
   - Foro anello: diametro netto 3.8 mm (r=1.9 mm), parete esterna 2.3 mm (>= 2.2 mm).
3. Cuore intermedio (Heart_Body):
   - Corpo del cuore posizionato sopra la base.
4. Scritta centrale (Mesh_Text):
   - Glifi generati con font Huntrix e spaziatura (kerning) aumentata di +0.75 mm.
   - Luce minima garantita tra caratteri consecutivi >= 0.70 mm.
   - Spessore minimo dei tratti >= 0.85 mm.
5. Quote Z calibrate (Z totale = 4.60 mm):
   - Base_Slab: Z 0.0 - 2.40 mm (spessore 2.40 mm).
   - Heart_Body: Z 2.00 - 3.60 mm (compenetrazione Z 0.40 mm nella base).
   - Mesh_Text: Z 3.20 - 4.60 mm (compenetrazione Z 0.40 mm nel cuore).
"""
from typing import Dict, Any
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
import matplotlib.textpath as tp
import matplotlib.font_manager as fm

from generator_u1.font_resolver import resolve_font_path


def _cubic_bezier(p0, p1, p2, p3, n=60):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def get_heart_huntrix_geometries(
    target_width: float = 52.0,
    text: str = "HUNTRIX"
) -> Dict[str, Any]:
    """
    Restituisce le geometrie 2D Shapely per i 3 volumi:
    - base: Base_Slab (con asola X=0)
    - heart: Heart_Body
    - text: Mesh_Text
    """
    scale_factor = target_width / 52.0

    # 1. Ridisegno del profilo a cuore con curve Bézier e cuspide smussata R = 2.5 mm
    # Notch centrale: (0, 7.0)
    # Lobo superiore: (13.0, 20.0)
    # Fianco esterno: (24.0, 8.0)
    # Cuspide inferiore raccordata: arco tangente di raggio R = 2.5 mm centrato a (0, -19.5)
    c1 = _cubic_bezier(np.array([0.0, 7.0]), np.array([2.5, 14.5]), np.array([6.5, 20.0]), np.array([13.0, 20.0]))
    c2 = _cubic_bezier(np.array([13.0, 20.0]), np.array([20.0, 20.0]), np.array([24.0, 15.0]), np.array([24.0, 8.0]))
    c3 = _cubic_bezier(np.array([24.0, 8.0]), np.array([24.0, -1.0]), np.array([14.0, -13.0]), np.array([2.45, -20.0]))
    theta = np.linspace(np.arcsin(2.45 / 2.5), 0, 25)
    c4 = np.column_stack([2.5 * np.sin(theta), -19.5 - 2.5 * np.cos(theta)])

    right_half = np.vstack([c1, c2[1:], c3[1:], c4[1:]])
    left_half = np.column_stack([-right_half[::-1, 0], right_half[::-1, 1]])
    heart_poly_raw = Polygon(np.vstack([right_half, left_half[1:]]))

    if abs(scale_factor - 1.0) > 1e-4:
        heart_poly = affinity.scale(heart_poly_raw, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    else:
        heart_poly = heart_poly_raw

    # 2. Asola anello al CENTRO (X=0), innestata nella gola centrale tra i due lobi
    r_inner = 1.9 * scale_factor  # Foro diametro netto 3.8 mm
    r_outer = 4.2 * scale_factor  # Parete 2.3 mm >= 2.2 mm
    c_eyelet = Point(0.0, 18.5 * scale_factor)
    eyelet_outer = c_eyelet.buffer(r_outer, resolution=64)
    eyelet_inner = c_eyelet.buffer(r_inner, resolution=64)

    # Base_Slab: offset perimetrale morbido di 2.0 mm attorno al cuore con integrazione asola
    base_slab_offset = heart_poly.buffer(2.0 * scale_factor, resolution=64)
    base_slab_2d = unary_union([base_slab_offset, eyelet_outer]).difference(eyelet_inner)

    # Heart_Body: cuore sopra la base (assicura che il foro dell'anello rimanga libero)
    heart_body_2d = heart_poly.difference(eyelet_inner)

    # 3. Scritta HUNTRIX con kerning spaziato e buffer FDM >= 0.85 mm
    clean_txt = (text or "HUNTRIX").strip().upper()
    font_file = resolve_font_path("Huntrix")
    if not font_file:
        base_dir = Path(__file__).resolve().parent.parent
        font_file = str(base_dir / "assets" / "fonts" / "Huntrix.otf")

    fp = fm.FontProperties(fname=font_file)
    font_sz = 7.8 * scale_factor
    char_spacing = 0.75 * scale_factor  # Spaziatura orizzontale per luce >= 0.70 mm

    char_geoms = []
    cur_x = 0.0

    for ch in clean_txt:
        char_tp = tp.TextPath((0, 0), ch, size=font_sz, prop=fp)
        raw_polys = [Polygon(p) for p in char_tp.to_polygons() if len(p) >= 3]
        if not raw_polys:
            cur_x += (font_sz * 0.45) + char_spacing
            continue

        outers = [p for p in raw_polys if not any(o.contains(p) for o in raw_polys if o != p)]
        holes = [p for p in raw_polys if any(o.contains(p) for o in raw_polys if o != p)]
        poly_list = []
        for o in outers:
            h_coords = [h.exterior.coords for h in holes if o.contains(h)]
            try:
                poly = Polygon(o.exterior.coords, h_coords)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                poly_list.append(poly)
            except Exception:
                poly = Polygon(o.exterior.coords)
                if not poly.is_valid:
                    poly = poly.buffer(0)
                poly_list.append(poly)

        g_char = unary_union(poly_list)
        # Buffer protettivo 0.18 mm per spessore minimo >= 0.85 mm
        g_buf = g_char.buffer(0.18 * scale_factor, resolution=32)
        gb = g_buf.bounds
        g_placed = affinity.translate(g_buf, xoff=cur_x - gb[0])
        char_geoms.append(g_placed)
        cur_x = g_placed.bounds[2] + char_spacing

    if char_geoms:
        text_union = unary_union(char_geoms)
        tb = text_union.bounds
        tc_x = (tb[0] + tb[2]) / 2.0
        tc_y = (tb[1] + tb[3]) / 2.0
        # Centratura all'interno del corpo del cuore (y visuale attorno a +0.5 mm)
        text_2d = affinity.translate(text_union, xoff=-tc_x, yoff=(0.5 * scale_factor) - tc_y)
    else:
        text_2d = Polygon()

    return {
        "base": base_slab_2d,
        "heart": heart_body_2d,
        "text": text_2d
    }

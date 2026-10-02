import os
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely import affinity
import trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

from generator_u1.packager.snapmaker_3mf import PartItem

def _extract_shapely_polygons_from_textpath(tp: TextPath) -> sg.MultiPolygon:
    """
    Converte un TextPath matplotlib in poligoni Shapely con corretta
    gestione dei fori interni (es. A, O, B, P, R, D, 0, 4, 6, 8, 9).
    """
    raw_polys = [sg.Polygon(p) for p in tp.to_polygons() if len(p) >= 3]
    if not raw_polys:
        raise ValueError("Impossibile generare vettori per il testo fornito.")

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
        final_polys.append(sg.Polygon(outer.exterior.coords, my_holes))

    merged = unary_union(final_polys)
    return merged

def _generate_text_2d(
    text: str,
    font_family: str,
    font_path: Optional[str],
    font_size: float,
    letter_spacing: float
) -> sg.base.BaseGeometry:
    """Genera la geometria 2D vettoriale di una riga di testo."""
    if font_path and os.path.exists(font_path):
        fp = FontProperties(fname=font_path)
    else:
        weight = "bold" if font_family in ["Arial", "Segoe UI", "Georgia"] else "normal"
        fp = FontProperties(family=font_family, weight=weight)

    if letter_spacing == 0.0 or len(text) <= 1:
        tp = TextPath((0, 0), text, size=font_size, prop=fp)
        return _extract_shapely_polygons_from_textpath(tp)

    char_polys = []
    cur_x = 0.0
    for char in text:
        char_tp = TextPath((cur_x, 0), char, size=font_size, prop=fp)
        if len(char_tp.to_polygons()) > 0:
            cp = _extract_shapely_polygons_from_textpath(char_tp)
            char_polys.append(cp)
            cbounds = cp.bounds
            cur_x = cbounds[2] + letter_spacing
        else:
            cur_x += (font_size * 0.4) + letter_spacing

    if not char_polys:
        raise ValueError(f"Nessun carattere valido generato per '{text}'")
    return unary_union(char_polys)

def _extrude_geometry(geom: Any, height: float) -> trimesh.Trimesh:
    """Estrude un Polygon o MultiPolygon Shapely in una mesh trimesh 3D manifold."""
    polys = geom.geoms if hasattr(geom, "geoms") else [geom]
    sub_meshes = []
    for p in polys:
        if not p.is_empty and p.area > 1e-4:
            m = trimesh.creation.extrude_polygon(p, height=height)
            sub_meshes.append(m)

    if not sub_meshes:
        raise ValueError("Geometria vuota durante l'estrusione 3D.")

    if len(sub_meshes) == 1:
        return sub_meshes[0]
    return trimesh.util.concatenate(sub_meshes)

def generate_desk_sign_parts(params: Dict[str, Any]) -> List[PartItem]:
    """
    Genera le mesh 3D manifold per la Targhetta da Tavolo (Desk Sign).
    Supporta:
    - Base a Cuneo Inclinato (Wedge autoportante) o Piatta (Flat).
    - Faccia con estrusione lungo la normale matematica esatta.
    - Testo su 1 o 2 righe indipendenti con allineamento personalizzato.
    - Cornice / bordo decorativo in rilievo con raggio di raccordo.
    - Fino a 4 estrusori indipendenti Snapmaker U1 (T0..T3).
    """
    base_mode = params.get("base_mode", "wedge").lower()
    wedge_angle_deg = float(params.get("wedge_angle", 45.0))
    wedge_angle = np.radians(wedge_angle_deg)
    base_thickness = float(params.get("base_thickness", 2.4))
    corner_radius = float(params.get("corner_radius", 3.0))
    padding_x = float(params.get("padding_x", 6.0))
    padding_y = float(params.get("padding_y", 5.0))
    line_spacing = float(params.get("line_spacing", 3.5))
    text_align = params.get("text_align", "center").lower()

    # Riga 1 (Titolo)
    text_line1 = params.get("text_line1", "CHARIZARD").strip()
    if not text_line1:
        text_line1 = params.get("text", "DESK SIGN").strip() or "DESK SIGN"
    font_family_line1 = params.get("font_family_line1") or params.get("font_family", "Arial")
    font_path_line1 = params.get("font_path_line1") or params.get("font_path")
    font_size_line1 = float(params.get("font_size_line1", params.get("font_size", 14.0)))
    letter_spacing_line1 = float(params.get("letter_spacing_line1", params.get("letter_spacing", 0.0)))
    thickness_line1 = float(params.get("thickness_line1", 1.2))
    extruder_line1 = int(params.get("extruder_line1", params.get("extruder_text", 1)))

    # Riga 2 (Sottotitolo, opzionale)
    line2_enabled = bool(params.get("line2_enabled", True))
    text_line2 = params.get("text_line2", "").strip()
    if not text_line2:
        line2_enabled = False

    font_family_line2 = params.get("font_family_line2") or font_family_line1
    font_path_line2 = params.get("font_path_line2") or font_path_line1
    font_size_line2 = float(params.get("font_size_line2", 8.0))
    letter_spacing_line2 = float(params.get("letter_spacing_line2", 0.0))
    thickness_line2 = float(params.get("thickness_line2", 1.2))
    extruder_line2 = int(params.get("extruder_line2", 2))

    # Cornice / Bordo
    border_enabled = bool(params.get("border_enabled", True))
    border_width = float(params.get("border_width", 2.0))
    border_thickness = float(params.get("border_thickness", 1.0))
    extruder_border = int(params.get("extruder_border", 3))

    # Base
    extruder_base = int(params.get("extruder_base", 0))

    # 1. Generazione 2D Testo Riga 1
    t1_raw = _generate_text_2d(text_line1, font_family_line1, font_path_line1, font_size_line1, letter_spacing_line1)
    t1_minx, t1_miny, t1_maxx, t1_maxy = t1_raw.bounds
    w1 = t1_maxx - t1_minx
    h1 = t1_maxy - t1_miny
    t1_norm = affinity.translate(t1_raw, xoff=-t1_minx, yoff=-t1_miny)

    # 2. Generazione 2D Testo Riga 2 (se presente)
    t2_norm = None
    w2, h2 = 0.0, 0.0
    if line2_enabled:
        t2_raw = _generate_text_2d(text_line2, font_family_line2, font_path_line2, font_size_line2, letter_spacing_line2)
        t2_minx, t2_miny, t2_maxx, t2_maxy = t2_raw.bounds
        w2 = t2_maxx - t2_minx
        h2 = t2_maxy - t2_miny
        t2_norm = affinity.translate(t2_raw, xoff=-t2_minx, yoff=-t2_miny)

    # 3. Calcolo Ingombri Contenuto e Dimensionamento Faccia (W x H_face)
    w_content = max(w1, w2)
    if line2_enabled:
        h_content = h1 + line_spacing + h2
    else:
        h_content = h1

    border_clearance = (border_width + 1.5) if border_enabled else 0.0
    w_face = max(w_content + 2 * (padding_x + border_clearance), 60.0)
    h_face = max(h_content + 2 * (padding_y + border_clearance), 25.0)

    # 4. Posizionamento 2D dei Testi sulla Faccia (u in [-W/2, W/2], v in [0, H_face])
    v_start = (h_face - h_content) / 2.0

    if line2_enabled:
        # Riga 2 in basso (v inferiore), Riga 1 in alto (v superiore)
        v2_pos = v_start
        v1_pos = v_start + h2 + line_spacing
    else:
        v1_pos = v_start
        v2_pos = 0.0

    # Calcolo coordinate u in base all'allineamento
    if text_align == "center":
        u1_pos = -w1 / 2.0
        u2_pos = -w2 / 2.0
    elif text_align == "left":
        u1_pos = -w_face / 2.0 + padding_x + border_clearance
        u2_pos = -w_face / 2.0 + padding_x + border_clearance
    else:  # right
        u1_pos = w_face / 2.0 - padding_x - border_clearance - w1
        u2_pos = w_face / 2.0 - padding_x - border_clearance - w2

    t1_2d = affinity.translate(t1_norm, xoff=u1_pos, yoff=v1_pos)
    t2_2d = affinity.translate(t2_norm, xoff=u2_pos, yoff=v2_pos) if line2_enabled else None

    # 5. Generazione Cornice / Bordo 2D (se abilitata)
    border_2d = None
    if border_enabled:
        inset = 1.0
        u_min = -w_face / 2.0 + inset
        u_max = w_face / 2.0 - inset
        v_min = inset
        v_max = h_face - inset

        r = min(corner_radius, (u_max - u_min) / 4.0, (v_max - v_min) / 4.0)
        if r > 0.1:
            outer_box = sg.box(u_min + r, v_min + r, u_max - r, v_max - r).buffer(r, resolution=16)
        else:
            outer_box = sg.box(u_min, v_min, u_max, v_max)

        inner_box = outer_box.buffer(-border_width, resolution=16)
        border_2d = outer_box.difference(inner_box)

    # 6. Costruzione della Geometria 3D della Base e Trasformazione Normale
    parts: List[PartItem] = []

    if base_mode == "wedge":
        # BASE A CUNEO (WEDGE AUTOPORTANTE DA TAVOLO)
        # Profilo Y-Z:
        # Piatto PEI a Z=0. Faccia inclinata ad angolo alpha.
        h_lip = min(base_thickness, 2.0)
        t_land = 2.0  # Appiattimento superiore per solidità
        d_base = h_face * np.cos(wedge_angle) + t_land
        y0 = -d_base / 2.0

        # Poligono 2D YZ della sezione trasversale
        p_front_bot = (y0, 0.0)
        p_front_top = (y0, h_lip)
        p_face_top = (y0 + h_face * np.cos(wedge_angle), h_lip + h_face * np.sin(wedge_angle))
        p_rear_top = (y0 + h_face * np.cos(wedge_angle) + t_land, h_lip + h_face * np.sin(wedge_angle))
        p_rear_bot = (y0 + h_face * np.cos(wedge_angle) + t_land, 0.0)

        poly_yz = sg.Polygon([p_front_bot, p_front_top, p_face_top, p_rear_top, p_rear_bot])

        # Estrusione lungo X per larghezza w_face
        mesh_base_raw = trimesh.creation.extrude_polygon(poly_yz, height=w_face)
        # Matrice di rotazione per allineare l'asse di estrusione a X:
        # X = z_ext - w_face/2, Y = y, Z = z
        T_base = np.array([
            [0.0, 0.0, 1.0, -w_face / 2.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_base_raw.apply_transform(T_base)
        parts.append(PartItem(name="Base_Wedge", mesh=mesh_base_raw, extruder=extruder_base))

        # Matrice di trasformazione dal piano locale della faccia (u, v, w) allo spazio mondo (x, y, z):
        # x = u
        # y = y0 + v * cos(alpha) - w * sin(alpha)
        # z = h_lip + v * sin(alpha) + w * cos(alpha)
        # Normal w points strictly OUTWARD: (0, -sin(alpha), cos(alpha))
        M_face = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(wedge_angle), -np.sin(wedge_angle), y0],
            [0.0, np.sin(wedge_angle), np.cos(wedge_angle), h_lip],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)

    else:
        # BASE PIATTA (FLAT)
        # Rettangolo con angoli arrotondati estruso verticalmente
        r = min(corner_radius, w_face / 4.0, h_face / 4.0)
        u_min = -w_face / 2.0
        u_max = w_face / 2.0
        v_min = 0.0
        v_max = h_face

        if r > 0.1:
            base_poly = sg.box(u_min + r, v_min + r, u_max - r, v_max - r).buffer(r, resolution=16)
        else:
            base_poly = sg.box(u_min, v_min, u_max, v_max)

        # Centra in Y attorno a 0
        base_poly = affinity.translate(base_poly, yoff=-h_face / 2.0)
        mesh_base_raw = _extrude_geometry(base_poly, height=base_thickness)
        parts.append(PartItem(name="Base_Flat", mesh=mesh_base_raw, extruder=extruder_base))

        # Trasformazione per posizionare il rilievo sulla faccia superiore piatta a Z = base_thickness
        M_face = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, -h_face / 2.0],
            [0.0, 0.0, 1.0, base_thickness],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)

    # 7. Estrusione e Trasformazione Elementi in Rilievo sulla Faccia
    # Riga 1
    mesh_t1 = _extrude_geometry(t1_2d, height=thickness_line1)
    mesh_t1.apply_transform(M_face)
    clean_t1 = "".join(c for c in text_line1 if c.isalnum() or c in "_-") or "Line1"
    parts.append(PartItem(name=f"Text_Line1_{clean_t1}", mesh=mesh_t1, extruder=extruder_line1))

    # Riga 2 (se presente)
    if line2_enabled and t2_2d is not None:
        mesh_t2 = _extrude_geometry(t2_2d, height=thickness_line2)
        mesh_t2.apply_transform(M_face)
        clean_t2 = "".join(c for c in text_line2 if c.isalnum() or c in "_-") or "Line2"
        parts.append(PartItem(name=f"Text_Line2_{clean_t2}", mesh=mesh_t2, extruder=extruder_line2))

    # Cornice decorativa (se abilitata)
    if border_enabled and border_2d is not None and not border_2d.is_empty:
        mesh_border = _extrude_geometry(border_2d, height=border_thickness)
        mesh_border.apply_transform(M_face)
        parts.append(PartItem(name="Border_Frame", mesh=mesh_border, extruder=extruder_border))

    return parts

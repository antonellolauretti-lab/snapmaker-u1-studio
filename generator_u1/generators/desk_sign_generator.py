import os
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import numpy as np
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely import affinity
import trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

from generator_u1.packager.snapmaker_3mf import PartItem
from generator_u1.font_resolver import (
    get_font_properties,
    get_font_dilation_offset,
    apply_text_polygon_buffer,
    resolve_font_path
)
from generator_u1.generators.keychain_generator import _get_vector_icon

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
        try:
            poly = sg.Polygon(outer.exterior.coords, my_holes)
            if not poly.is_valid:
                poly = poly.buffer(0)
            final_polys.append(poly)
        except Exception:
            poly = sg.Polygon(outer.exterior.coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            final_polys.append(poly)

    try:
        merged = unary_union(final_polys)
    except Exception:
        sanitized = [p.buffer(0) for p in final_polys if not p.is_empty]
        merged = unary_union(sanitized)

    if not merged.is_valid:
        merged = merged.buffer(0)
    return merged

def _generate_text_2d(
    text: str,
    font_family: str,
    font_path: Optional[str],
    font_size: float,
    letter_spacing: float,
    dilation_offset: float = 0.0
) -> sg.base.BaseGeometry:
    """Genera la geometria 2D vettoriale di una riga di testo con buffer opzionale."""
    if not font_path:
        font_path = resolve_font_path(font_family)
    fp = get_font_properties(font_family, font_path)

    if letter_spacing == 0.0 or len(text) <= 1:
        tp = TextPath((0, 0), text, size=font_size, prop=fp)
        raw_geom = _extract_shapely_polygons_from_textpath(tp)
    else:
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
        raw_geom = unary_union(char_polys)

    if dilation_offset > 0.0:
        raw_geom = apply_text_polygon_buffer(raw_geom, dilation_offset)

    return raw_geom

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
    1. Base "Sagomata sul Testo" (contour): il profilo sagomato del testo poggia
       saldamente su un basamento/binario orizzontale spesso da appoggio con
       inclinazione ergonomica da tavolo (~76°) e nervature di rinforzo posteriori.
    2. Base "Rettangolare" (rectangle / wedge): targa rettangolare da tavolo
       con supporto cuneo solido autoportante (~68°), cornice perimetrale in rilievo
       e testo estruso sulla faccia inclinata.
    - Testo su 1 o 2 righe indipendenti con allineamento e spessore dedicati.
    - Simbolo/Icona vettoriale 3D a catalogo a sinistra o destra con estrusore dedicato.
    - Fino a 4 estrusori fisici Snapmaker U1 (T0..T3).
    """
    # Determinazione stile base: 'contour' (Sagomata sul Testo) vs 'rectangle' (Rettangolare)
    base_style = params.get("base_style")
    if not base_style:
        base_mode = params.get("base_mode", "").lower()
        if base_mode in ["flat", "wedge"]:
            base_style = "rectangle" if base_mode == "wedge" else "contour"
        else:
            base_style = "contour"
    base_style = base_style.lower()
    if base_style not in ["contour", "rectangle"]:
        base_style = "contour"

    base_thickness = float(params.get("base_thickness", 3.0))
    padding_x = float(params.get("padding_x", 8.0))
    padding_y = float(params.get("padding_y", 4.0))
    line_spacing = float(params.get("line_spacing", 3.5))

    # Riga 1 (Titolo Principale)
    text_line1 = params.get("text_line1") or params.get("text", "STUDIO U1")
    text_line1 = str(text_line1).strip()
    if not text_line1:
        text_line1 = "STUDIO U1"

    font_family_line1 = params.get("font_family_line1") or params.get("font_family", "Permanent Marker")
    font_path_line1 = params.get("font_path_line1") or params.get("font_path")
    if not font_path_line1:
        font_path_line1 = resolve_font_path(font_family_line1)

    font_size_line1 = float(params.get("font_size_line1", params.get("font_size", 16.0)))
    letter_spacing_line1 = float(params.get("letter_spacing_line1", params.get("letter_spacing", 0.0)))
    thickness_line1 = float(params.get("thickness_line1", 1.4))
    extruder_line1 = int(params.get("extruder_line1", params.get("extruder_text", 1)))

    # Riga 2 (Sottotitolo, opzionale)
    line2_enabled = bool(params.get("line2_enabled", False))
    text_line2 = (params.get("text_line2") or "").strip()
    if not text_line2:
        line2_enabled = False

    font_family_line2 = params.get("font_family_line2") or font_family_line1
    font_path_line2 = params.get("font_path_line2") or font_path_line1
    if not font_path_line2 and font_family_line2:
        font_path_line2 = resolve_font_path(font_family_line2)

    font_size_line2 = float(params.get("font_size_line2", font_size_line1 * 0.65))
    letter_spacing_line2 = float(params.get("letter_spacing_line2", 0.0))
    thickness_line2 = float(params.get("thickness_line2", 1.2))
    extruder_line2 = int(params.get("extruder_line2", -1))
    if extruder_line2 == -1:
        extruder_line2 = extruder_line1

    # Simbolo / Icona 3D
    icon_name = params.get("icon_name") or params.get("icon_id") or "none"
    icon_position = str(params.get("icon_position", "right")).lower()
    has_custom_icon_color = bool(
        params.get("has_custom_icon_color") or 
        params.get("hasCustomIconColor") or 
        params.get("custom_icon_color") or 
        (int(params.get("extruder_icon", 1)) == 2)
    )
    if has_custom_icon_color:
        extruder_icon = 2
    else:
        extruder_icon = extruder_line1

    # Cornice / Bordo (utilizzato per stile 'rectangle')
    border_enabled = bool(params.get("border_enabled", True))
    border_width = float(params.get("border_width", 2.0))
    border_thickness = float(params.get("border_thickness", 1.0))
    extruder_border = int(params.get("extruder_border", 3))

    # Assegnazione estrusore base
    extruder_base = int(params.get("extruder_base", 0))

    offset1 = get_font_dilation_offset(font_family_line1)
    offset2 = get_font_dilation_offset(font_family_line2)

    # 1. Generazione 2D Testo Riga 1
    t1_raw = _generate_text_2d(
        text_line1, font_family_line1, font_path_line1,
        font_size_line1, letter_spacing_line1, dilation_offset=offset1
    )
    t1_minx, t1_miny, t1_maxx, t1_maxy = t1_raw.bounds
    w1 = t1_maxx - t1_minx
    h1 = t1_maxy - t1_miny
    t1_norm = affinity.translate(t1_raw, xoff=-t1_minx, yoff=-t1_miny)

    # 2. Generazione 2D Testo Riga 2 (se presente)
    t2_norm = None
    w2, h2 = 0.0, 0.0
    if line2_enabled:
        try:
            t2_raw = _generate_text_2d(
                text_line2, font_family_line2, font_path_line2,
                font_size_line2, letter_spacing_line2, dilation_offset=offset2
            )
            t2_minx, t2_miny, t2_maxx, t2_maxy = t2_raw.bounds
            w2 = t2_maxx - t2_minx
            h2 = t2_maxy - t2_miny
            t2_norm = affinity.translate(t2_raw, xoff=-t2_minx, yoff=-t2_miny)
        except Exception:
            line2_enabled = False

    w_text_content = max(w1, w2)
    if line2_enabled:
        h_text_content = h1 + line_spacing + h2
    else:
        h_text_content = h1

    # 3. Generazione e Scalatura Simbolo Vettoriale (se selezionato)
    icon_raw = _get_vector_icon(icon_name)
    icon_norm = None
    iw, ih = 0.0, 0.0
    spacing_icon = 4.0 if (icon_raw is not None) else 0.0

    if icon_raw is not None:
        icon_h = min(font_size_line1 * 1.05, max(h_text_content * 0.90, 14.0))
        icon_scaled = affinity.scale(icon_raw, xfact=icon_h, yfact=icon_h, origin=(0, 0))
        iminx, iminy, imaxx, imaxy = icon_scaled.bounds
        iw = imaxx - iminx
        ih = imaxy - iminy
        icon_norm = affinity.translate(icon_scaled, xoff=-iminx, yoff=-iminy)

    # Calcolo ingombro orizzontale combinato (Testo + Icona)
    w_content_total = (w_text_content + spacing_icon + iw) if (icon_norm is not None) else w_text_content
    h_content_total = max(h_text_content, ih) if (icon_norm is not None) else h_text_content

    # Disposizione orizzontale centrata attorno a u = 0
    if icon_norm is not None:
        if icon_position == "left":
            x_icon = -w_content_total / 2.0
            x_text_start = -w_content_total / 2.0 + iw + spacing_icon
        else:
            x_text_start = -w_content_total / 2.0
            x_icon = -w_content_total / 2.0 + w_text_content + spacing_icon

        x1 = x_text_start + (w_text_content - w1) / 2.0
        x2 = x_text_start + (w_text_content - w2) / 2.0
    else:
        x_icon = 0.0
        x1 = -w1 / 2.0
        x2 = -w2 / 2.0

    # Disposizione verticale
    if line2_enabled and t2_norm is not None:
        y1 = h2 + line_spacing
        y2 = 0.0
        mid_y = h_text_content / 2.0
        y_icon = max(0.0, mid_y - (ih / 2.0))
    else:
        y1 = 0.0
        y2 = 0.0
        y_icon = max(0.0, (h1 - ih) / 2.0)

    t1_local = affinity.translate(t1_norm, xoff=x1, yoff=y1)
    t2_local = affinity.translate(t2_norm, xoff=x2, yoff=y2) if (line2_enabled and t2_norm is not None) else None
    icon_local = affinity.translate(icon_norm, xoff=x_icon, yoff=y_icon) if (icon_norm is not None) else None

    # Fissaggio robusto del testo sul binario:
    # Rimuovi i singoli 'dentini' isolati: crea un raccordo continuo lungo tutta la quota orizzontale
    # inferiore delle lettere dell'ultima riga, saldando la scritta direttamente al basamento
    if line2_enabled and t2_local is not None:
        b_minx, b_miny, b_maxx, b_maxy = t2_local.bounds
        text_weld_runner = sg.box(b_minx - 0.5, -2.5, b_maxx + 0.5, 1.8)
        t2_local = unary_union([t2_local, text_weld_runner]).buffer(0)
    else:
        b_minx, b_miny, b_maxx, b_maxy = t1_local.bounds
        text_weld_runner = sg.box(b_minx - 0.5, -2.5, b_maxx + 0.5, 1.8)
        t1_local = unary_union([t1_local, text_weld_runner]).buffer(0)

    # Unione elementi in rilievo frontale
    fg_items = [t1_local]
    if t2_local is not None:
        fg_items.append(t2_local)
    if icon_local is not None:
        fg_items.append(icon_local)
    fg_union = unary_union(fg_items)

    parts: List[PartItem] = []

    if base_style == "contour":
        # ==============================================================================
        # 1. TARGHETTA DA TAVOLO SAGOMATA SUL TESTO CON BASAMENTO/BINARIO D'APPOGGIO
        # ==============================================================================
        contour_pad = max(3.5, padding_y)
        all_fg_bounds = fg_union.bounds
        overall_minx, overall_miny, overall_maxx, overall_maxy = all_fg_bounds

        # Profilo sagomato attorno a testo e simbolo
        close_r = max(4.0, font_size_line1 * 0.3)
        closed_fg = fg_union.buffer(close_r, resolution=16).buffer(-close_r, resolution=16)
        contour_raw = closed_fg.buffer(contour_pad, resolution=16).buffer(0)

        # Elementi di supporto e fusione monolitica:
        fuse_elements = [contour_raw]

        # A) Se è presente un'icona laterale (a destra o sinistra):
        if icon_local is not None:
            ix_min, iy_min, ix_max, iy_max = icon_local.bounds
            # 1. Pilastro/pedistallo solido verticale sotto l'icona fino al basamento inferiore (elimina fluttuazioni)
            icon_column = sg.box(ix_min - contour_pad, -contour_pad - 4.0, ix_max + contour_pad, iy_min + 1.5)
            fuse_elements.append(icon_column)

            # 2. Ponte orizzontale solido di raccordo tra il corpo del testo e l'icona
            if icon_position == "left":
                bridge_conn = sg.box(ix_min, min(0.0, iy_min), x_text_start + 2.0, iy_max + contour_pad)
            else:
                bridge_conn = sg.box(x_text_start + w_text_content - 2.0, min(0.0, iy_min), ix_max, iy_max + contour_pad)
            fuse_elements.append(bridge_conn)

        # B) Basamento/Fondazione orizzontale continua lungo tutta la larghezza dell'assieme
        # Garantisce appoggio continuo e chiusura completa di qualsiasi fessura tra lettere e binario
        bot_foundation_h = max(6.0, contour_pad * 2.2)
        bottom_foundation = sg.box(overall_minx - contour_pad, -contour_pad - 4.0, overall_maxx + contour_pad, bot_foundation_h)
        fuse_elements.append(bottom_foundation)

        contour_fused = unary_union(fuse_elements).buffer(0)
        # Rimuovi eventuali fori/fessure interne residue per garantire una placca d'appoggio monolitica
        if hasattr(contour_fused, 'exterior') and contour_fused.exterior is not None:
            contour_2d = sg.Polygon(contour_fused.exterior.coords)
        elif contour_fused.geom_type == 'MultiPolygon':
            outers = [sg.Polygon(p.exterior.coords) for p in contour_fused.geoms if not p.is_empty]
            contour_2d = unary_union(outers).buffer(0)
        else:
            contour_2d = contour_fused

        c_minx, c_miny, c_maxx, c_maxy = contour_2d.bounds
        w_contour = c_maxx - c_minx
        h_contour = c_maxy - c_miny
        x_contour_center = (c_minx + c_maxx) / 2.0

        # Allinea in modo che la base della sagoma inizi a v = 0
        v_offset = -c_miny
        contour_2d_aligned = affinity.translate(contour_2d, yoff=v_offset)
        t1_2d_aligned = affinity.translate(t1_local, yoff=v_offset)
        t2_2d_aligned = affinity.translate(t2_local, yoff=v_offset) if t2_local else None
        icon_2d_aligned = affinity.translate(icon_local, yoff=v_offset) if icon_local else None

        # Parametri Geometrici Inclinazione e Binario d'Appoggio (Standing Footing)
        tilt_angle_deg = float(params.get("tilt_angle", 76.0)) # Angolo ergonomico da scrivania
        tilt_angle = np.radians(tilt_angle_deg)
        rail_h = 6.0               # Spessore/altezza del basamento (mm)
        y_front = -8.0             # Sporgenza frontale del basamento sul tavolo (mm)
        y_back = 18.0              # Sporgenza posteriore del basamento sul tavolo (mm)
        w_rail = max(w_contour + 16.0, 72.0) # Larghezza basamento (supera la sagoma del testo)
        plate_thickness = max(base_thickness, 3.2)
        y_anchor = 0.0
        z_anchor = rail_h - 2.0    # Incastro solido nel basamento

        # 1. Mesh Basamento/Binario Orizzontale Solido da Appoggio con Gusset Posteriore Continuo
        # Profilo trasversale YZ con appoggio piatto su Z = 0 e sostegno continuo lungo la schiena della targa
        h_gusset = min(h_contour * 0.45, 14.0)
        back_y = y_anchor - plate_thickness * np.sin(tilt_angle) + h_gusset * np.cos(tilt_angle)
        back_z = z_anchor + plate_thickness * np.cos(tilt_angle) + h_gusset * np.sin(tilt_angle)

        p_front_bot = (y_front, 0.0)
        p_front_top = (y_front, 3.5)
        p_front_lip = (-2.0, rail_h)
        p_back_gusset = (back_y, back_z)
        p_rear_top = (y_back - 3.5, rail_h + 1.0)
        p_rear_chamf = (y_back, 2.5)
        p_rear_bot = (y_back, 0.0)
        rail_poly_yz = sg.Polygon([p_front_bot, p_front_top, p_front_lip, p_back_gusset, p_rear_top, p_rear_chamf, p_rear_bot])

        mesh_rail = trimesh.creation.extrude_polygon(rail_poly_yz, height=w_rail)
        T_rail = np.array([
            [0.0, 0.0, 1.0, x_contour_center - w_rail / 2.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_rail.apply_transform(T_rail)

        # 2. Mesh Placca Sagomata Inclinata (Backplate)
        mesh_plate = _extrude_geometry(contour_2d_aligned, height=plate_thickness)
        M_plate = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(tilt_angle), -np.sin(tilt_angle), y_anchor],
            [0.0, np.sin(tilt_angle), np.cos(tilt_angle), z_anchor],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_plate.apply_transform(M_plate)

        mesh_base_total = trimesh.util.concatenate([mesh_rail, mesh_plate])
        parts.append(PartItem(name="Base_Contour_Rail", mesh=mesh_base_total, extruder=extruder_base))

        # Matrice comune per gli elementi in rilievo sulla faccia inclinata
        M_face_elements = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(tilt_angle), -np.sin(tilt_angle), y_anchor - plate_thickness * np.sin(tilt_angle)],
            [0.0, np.sin(tilt_angle), np.cos(tilt_angle), z_anchor + plate_thickness * np.cos(tilt_angle)],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)

        # 4. Estrusione Testo Riga 1
        mesh_t1 = _extrude_geometry(t1_2d_aligned, height=thickness_line1)
        mesh_t1.apply_transform(M_face_elements)
        clean_t1 = "".join(c for c in text_line1 if c.isalnum() or c in "_-")[:20] or "Line1"
        parts.append(PartItem(name=f"Text_Line1_{clean_t1}", mesh=mesh_t1, extruder=extruder_line1))

        # 5. Estrusione Testo Riga 2 (se presente)
        if line2_enabled and t2_2d_aligned is not None:
            mesh_t2 = _extrude_geometry(t2_2d_aligned, height=thickness_line2)
            mesh_t2.apply_transform(M_face_elements)
            clean_t2 = "".join(c for c in text_line2 if c.isalnum() or c in "_-")[:20] or "Line2"
            parts.append(PartItem(name=f"Text_Line2_{clean_t2}", mesh=mesh_t2, extruder=extruder_line2))

        # 6. Estrusione Simbolo 3D (se presente)
        if icon_2d_aligned is not None:
            mesh_icon = _extrude_geometry(icon_2d_aligned, height=thickness_line1)
            mesh_icon.apply_transform(M_face_elements)
            clean_icon = "".join(c for c in icon_name if c.isalnum() or c in "_-")[:20] or "Icon"
            parts.append(PartItem(name=f"Icon_{clean_icon}", mesh=mesh_icon, extruder=extruder_icon))

    else:
        # ==============================================================================
        # 2. TARGHETTA DA TAVOLO RETTANGOLARE CON SUPPORTO CUNEO AUTOPORTANTE
        # ==============================================================================
        border_clearance = (border_width + 1.5) if border_enabled else 0.0
        w_face = max(w_content_total + 2 * (padding_x + border_clearance), 68.0)
        h_face = max(h_content_total + 2 * (padding_y + border_clearance), 28.0)

        # Centra il contenuto sulla faccia rettangolare
        v_start = (h_face - h_content_total) / 2.0
        t1_face = affinity.translate(t1_local, yoff=v_start)
        t2_face = affinity.translate(t2_local, yoff=v_start) if t2_local else None
        icon_face = affinity.translate(icon_local, yoff=v_start) if icon_local else None

        # Cornice / Bordo perimetrale
        border_2d = None
        if border_enabled:
            inset = 1.0
            u_min = -w_face / 2.0 + inset
            u_max = w_face / 2.0 - inset
            v_min = inset
            v_max = h_face - inset
            r = min(3.0, (u_max - u_min) / 4.0, (v_max - v_min) / 4.0)
            if r > 0.1:
                outer_box = sg.box(u_min + r, v_min + r, u_max - r, v_max - r).buffer(r, resolution=16)
            else:
                outer_box = sg.box(u_min, v_min, u_max, v_max)
            inner_box = outer_box.buffer(-border_width, resolution=16)
            border_2d = outer_box.difference(inner_box)

        # Angolo di inclinazione ergonomico da scrivania
        wedge_angle_deg = float(params.get("wedge_angle", 70.0))
        wedge_angle = np.radians(wedge_angle_deg)
        h_lip = min(base_thickness, 2.5)
        t_land = 3.0  # Spessore/appiattimento superiore placca
        y0 = -6.0

        p_front_bot = (y0 - 3.0, 0.0)
        p_front_top = (y0 - 3.0, h_lip)
        p_face_top = (y0 + h_face * np.cos(wedge_angle), h_lip + h_face * np.sin(wedge_angle))
        p_rear_top = (p_face_top[0] + t_land, p_face_top[1])
        p_rear_plate_bot = (y0 + 3.0 + 3.5 * np.sin(wedge_angle), 0.0)

        poly_plate_yz = sg.Polygon([p_front_bot, p_front_top, p_face_top, p_rear_top, p_rear_plate_bot])
        mesh_base_raw = trimesh.creation.extrude_polygon(poly_plate_yz, height=w_face)
        T_base = np.array([
            [0.0, 0.0, 1.0, -w_face / 2.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_base_raw.apply_transform(T_base)

        # Supporto posteriore a staffe triangolari a sbalzo (profondità a terra 28 mm, anti-ribaltamento)
        total_depth_target = 28.0  # Richiesto: almeno 25-30 mm per stabilità ottimale
        y_rear_foot = p_front_bot[0] + total_depth_target
        v_attach = h_face * 0.65
        attach_y = y0 + v_attach * np.cos(wedge_angle) + 2.5
        attach_z = h_lip + v_attach * np.sin(wedge_angle) - 1.0
        p_bracket_bot_front = (p_rear_plate_bot[0] - 2.0, 0.0)
        p_bracket_bot_rear = (y_rear_foot, 0.0)
        p_bracket_top = (attach_y, attach_z)
        poly_bracket = sg.Polygon([p_bracket_bot_front, p_bracket_bot_rear, p_bracket_top])

        sub_stand_meshes = [mesh_base_raw]
        bracket_w = 8.0
        bracket_positions = [-w_face * 0.32, w_face * 0.32]
        if w_face > 110.0:
            bracket_positions.append(0.0)

        for bx in bracket_positions:
            mb = trimesh.creation.extrude_polygon(poly_bracket, height=bracket_w)
            Tb = np.array([
                [0.0, 0.0, 1.0, bx - bracket_w / 2.0],
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0]
            ], dtype=float)
            mb.apply_transform(Tb)
            sub_stand_meshes.append(mb)

        # Piede stabilizzatore posteriore a terra (profilo basso 2.5 mm a basso consumo che unisce i piedi a Z=0)
        p_tie_bot_front = (y_rear_foot - 5.0, 0.0)
        p_tie_bot_rear = (y_rear_foot, 0.0)
        p_tie_top_rear = (y_rear_foot, 2.5)
        p_tie_top_front = (y_rear_foot - 5.0, 2.5)
        poly_tie = sg.Polygon([p_tie_bot_front, p_tie_bot_rear, p_tie_top_rear, p_tie_top_front])
        w_tie = w_face * 0.75
        m_tie = trimesh.creation.extrude_polygon(poly_tie, height=w_tie)
        T_tie = np.array([
            [0.0, 0.0, 1.0, -w_tie / 2.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        m_tie.apply_transform(T_tie)
        sub_stand_meshes.append(m_tie)

        mesh_stand_total = trimesh.util.concatenate(sub_stand_meshes)
        parts.append(PartItem(name="Base_Rectangle_Stand", mesh=mesh_stand_total, extruder=extruder_base))

        M_face = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(wedge_angle), -np.sin(wedge_angle), y0],
            [0.0, np.sin(wedge_angle), np.cos(wedge_angle), h_lip],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)

        mesh_t1 = _extrude_geometry(t1_face, height=thickness_line1)
        mesh_t1.apply_transform(M_face)
        clean_t1 = "".join(c for c in text_line1 if c.isalnum() or c in "_-")[:20] or "Line1"
        parts.append(PartItem(name=f"Text_Line1_{clean_t1}", mesh=mesh_t1, extruder=extruder_line1))

        if line2_enabled and t2_face is not None:
            mesh_t2 = _extrude_geometry(t2_face, height=thickness_line2)
            mesh_t2.apply_transform(M_face)
            clean_t2 = "".join(c for c in text_line2 if c.isalnum() or c in "_-")[:20] or "Line2"
            parts.append(PartItem(name=f"Text_Line2_{clean_t2}", mesh=mesh_t2, extruder=extruder_line2))

        if icon_face is not None:
            mesh_icon = _extrude_geometry(icon_face, height=thickness_line1)
            mesh_icon.apply_transform(M_face)
            clean_icon = "".join(c for c in icon_name if c.isalnum() or c in "_-")[:20] or "Icon"
            parts.append(PartItem(name=f"Icon_{clean_icon}", mesh=mesh_icon, extruder=extruder_icon))

        if border_enabled and border_2d is not None and not border_2d.is_empty:
            mesh_border = _extrude_geometry(border_2d, height=border_thickness)
            mesh_border.apply_transform(M_face)
            parts.append(PartItem(name="Border_Frame", mesh=mesh_border, extruder=extruder_border))

    return parts

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
        raise ValueError("Impossibile generare vettori per la stringa di testo fornita.")

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

def _normalize_to_unit(geom: Any) -> Any:
    """Trasla e scala una forma in un rettangolo normalizzato di altezza unitaria."""
    minx, miny, maxx, maxy = geom.bounds
    w = maxx - minx
    h = maxy - miny
    scale = max(w, h)
    if scale <= 1e-6:
        return geom
    g = affinity.translate(geom, xoff=-minx, yoff=-miny)
    g = affinity.scale(g, xfact=1.0 / scale, yfact=1.0 / scale, origin=(0, 0))
    return g

def _get_vector_icon(name: str) -> Optional[Any]:
    """Libreria di sagome e simboli vettoriali 2D normalizzati."""
    if not name or name.lower() == "none":
        return None

    name = name.lower()
    if name == "heart":
        t = np.linspace(0, 2 * np.pi, 64)
        x = 16 * np.sin(t) ** 3
        y = 13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t)
        poly = sg.Polygon(list(zip(x, y)))
        return _normalize_to_unit(poly)

    elif name == "star":
        angles = np.linspace(0, 2 * np.pi, 11)[:-1]
        r_list = [1.0, 0.45] * 5
        star_pts = [(r * np.cos(a + np.pi / 2), r * np.sin(a + np.pi / 2)) for a, r in zip(angles, r_list)]
        poly = sg.Polygon(star_pts)
        return _normalize_to_unit(poly)

    elif name == "lightning":
        bolt_pts = [
            (0.45, 1.0),
            (0.05, 0.45),
            (0.40, 0.45),
            (0.15, 0.0),
            (0.75, 0.55),
            (0.45, 0.55),
            (0.70, 1.0),
        ]
        poly = sg.Polygon(bolt_pts)
        return _normalize_to_unit(poly)

    elif name == "paw":
        palm = sg.Point(0, 0).buffer(0.5)
        t1 = sg.Point(-0.4, 0.65).buffer(0.16)
        t2 = sg.Point(-0.15, 0.85).buffer(0.16)
        t3 = sg.Point(0.15, 0.85).buffer(0.16)
        t4 = sg.Point(0.4, 0.65).buffer(0.16)
        poly = unary_union([palm, t1, t2, t3, t4])
        return _normalize_to_unit(poly)

    elif name == "crown":
        crown_pts = [
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 0.75),
            (0.75, 0.35),
            (0.5, 0.95),
            (0.25, 0.35),
            (0.0, 0.75),
        ]
        poly = sg.Polygon(crown_pts)
        return _normalize_to_unit(poly)

    return None

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

def generate_keychain_parts(params: Dict[str, Any]) -> List[PartItem]:
    """
    Genera le mesh 3D della Base, del Testo e dell'eventuale Icona
    rispettando la configurazione degli utensili Snapmaker U1 (T0..T3).
    """
    text = params.get("text", "ANTONELLO").strip()
    font_family = params.get("font_family", "Arial")
    font_path = params.get("font_path")
    font_size = float(params.get("font_size", 14.0))
    letter_spacing = float(params.get("letter_spacing", 0.0))
    base_style = params.get("base_style", "rectangle")
    base_thickness = float(params.get("base_thickness", 2.4))
    text_thickness = float(params.get("text_thickness", 1.2))
    text_mode = params.get("text_mode", "embossed")
    corner_radius = float(params.get("corner_radius", 4.0))
    padding_x = float(params.get("padding_x", 5.0))
    padding_y = float(params.get("padding_y", 4.5))
    hole_enabled = bool(params.get("hole_enabled", True))
    hole_position = params.get("hole_position", "left")
    hole_diameter = float(params.get("hole_diameter", 5.0))
    icon_name = params.get("icon_name", "none")
    icon_position = params.get("icon_position", "left")
    extruder_base = int(params.get("extruder_base", 0))
    extruder_text = int(params.get("extruder_text", 1))
    extruder_icon = int(params.get("extruder_icon", extruder_text))

    # 1. Configurazione del Font (Supporta sia font di sistema che file .ttf/.otf caricato)
    if font_path and os.path.exists(font_path):
        fp = FontProperties(fname=font_path)
    else:
        weight = "bold" if font_family in ["Arial", "Segoe UI", "Georgia"] else "normal"
        fp = FontProperties(family=font_family, weight=weight)

    # 2. Generazione vettoriale del Testo
    if letter_spacing == 0.0 or len(text) <= 1:
        tp = TextPath((0, 0), text, size=font_size, prop=fp)
        text_2d = _extract_shapely_polygons_from_textpath(tp)
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
        text_2d = unary_union(char_polys)

    minx, miny, maxx, maxy = text_2d.bounds
    mid_y = (miny + maxy) / 2.0

    # 3. Generazione e posizionamento dell'Icona Vettoriale
    icon_raw = _get_vector_icon(icon_name)
    icon_2d = None
    if icon_raw is not None:
        icon_h = font_size * 0.90
        icon_scaled = affinity.scale(icon_raw, xfact=icon_h, yfact=icon_h, origin=(0, 0))
        iminx, iminy, imaxx, imaxy = icon_scaled.bounds
        iw = imaxx - iminx
        ih = imaxy - iminy

        spacing_icon = 2.5
        if icon_position == "left":
            # A sinistra del testo
            ix = minx - iw - spacing_icon
            iy = mid_y - (ih / 2.0)
            icon_2d = affinity.translate(icon_scaled, xoff=ix, yoff=iy)
        else:
            # A destra del testo
            ix = maxx + spacing_icon
            iy = mid_y - (ih / 2.0)
            icon_2d = affinity.translate(icon_scaled, xoff=ix, yoff=iy)

    # Unione elementi in rilievo per il calcolo della base
    foreground_items = [text_2d]
    if icon_2d is not None:
        foreground_items.append(icon_2d)
    foreground_union = unary_union(foreground_items)

    fg_minx, fg_miny, fg_maxx, fg_maxy = foreground_union.bounds
    fg_mid_y = (fg_miny + fg_maxy) / 2.0

    # 4. Creazione del Contorno della Base
    hole_radius = hole_diameter / 2.0
    hole_wall = max(3.0, hole_radius * 1.2)

    if base_style == "contour":
        base_contour = foreground_union.buffer(padding_y, resolution=16)
        if hole_enabled:
            if hole_position == "left":
                hx = fg_minx - (hole_radius + hole_wall)
                hy = fg_mid_y
            elif hole_position == "right":
                hx = fg_maxx + (hole_radius + hole_wall)
                hy = fg_mid_y
            else:  # top
                hx = (fg_minx + fg_maxx) / 2.0
                hy = fg_maxy + (hole_radius + hole_wall)

            hole_ear = sg.Point(hx, hy).buffer(hole_radius + hole_wall, resolution=16)
            base_contour = unary_union([base_contour, hole_ear])
    else:
        x_left_extra = (hole_radius * 2 + hole_wall * 2) if (hole_enabled and hole_position == "left") else padding_x
        x_right_extra = (hole_radius * 2 + hole_wall * 2) if (hole_enabled and hole_position == "right") else padding_x
        y_top_extra = (hole_radius * 2 + hole_wall * 2) if (hole_enabled and hole_position == "top") else padding_y

        x0 = fg_minx - x_left_extra
        x1 = fg_maxx + x_right_extra
        y0 = fg_miny - padding_y
        y1 = fg_maxy + y_top_extra

        r = min(corner_radius, (x1 - x0) / 4.0, (y1 - y0) / 4.0)
        inner_box = sg.box(x0 + r, y0 + r, x1 - r, y1 - r)
        base_contour = inner_box.buffer(r, resolution=16)

        if hole_enabled:
            if hole_position == "left":
                hx = x0 + hole_radius + hole_wall
                hy = fg_mid_y
            elif hole_position == "right":
                hx = x1 - (hole_radius + hole_wall)
                hy = fg_mid_y
            else:
                hx = (fg_minx + fg_maxx) / 2.0
                hy = y1 - (hole_radius + hole_wall)

    # 5. Applicazione del Foro
    if hole_enabled:
        hole_geom = sg.Point(hx, hy).buffer(hole_radius, resolution=32)
        base_2d = base_contour.difference(hole_geom)
    else:
        base_2d = base_contour

    # 6. Centratura delle geometrie in (0, 0)
    bx0, by0, bx1, by1 = base_2d.bounds
    cx = (bx0 + bx1) / 2.0
    cy = (by0 + by1) / 2.0

    base_2d = affinity.translate(base_2d, xoff=-cx, yoff=-cy)
    text_2d = affinity.translate(text_2d, xoff=-cx, yoff=-cy)
    if icon_2d is not None:
        icon_2d = affinity.translate(icon_2d, xoff=-cx, yoff=-cy)

    # 7. Estrusione 3D e Definizione Parti
    parts: List[PartItem] = []

    if text_mode == "embossed":
        mesh_base = _extrude_geometry(base_2d, height=base_thickness)
        parts.append(PartItem(name="Base", mesh=mesh_base, extruder=extruder_base))

        mesh_text = _extrude_geometry(text_2d, height=text_thickness)
        mesh_text.apply_translation([0, 0, base_thickness])
        parts.append(PartItem(name=f"Text_{text}", mesh=mesh_text, extruder=extruder_text))

        if icon_2d is not None:
            mesh_icon = _extrude_geometry(icon_2d, height=text_thickness)
            mesh_icon.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name=f"Icon_{icon_name}", mesh=mesh_icon, extruder=extruder_icon))

    elif text_mode == "flush":
        inlay_depth = min(text_thickness, base_thickness * 0.5)
        relief_union = text_2d if icon_2d is None else unary_union([text_2d, icon_2d])

        base_bottom_2d = base_2d.difference(relief_union)
        mesh_base_bottom = _extrude_geometry(base_bottom_2d, height=inlay_depth)
        mesh_base_top = _extrude_geometry(base_2d, height=base_thickness - inlay_depth)
        mesh_base_top.apply_translation([0, 0, inlay_depth])
        mesh_base = trimesh.util.concatenate([mesh_base_bottom, mesh_base_top])
        parts.append(PartItem(name="Base", mesh=mesh_base, extruder=extruder_base))

        mesh_text = _extrude_geometry(text_2d, height=inlay_depth)
        parts.append(PartItem(name=f"Text_{text}_Inlay", mesh=mesh_text, extruder=extruder_text))

        if icon_2d is not None:
            mesh_icon = _extrude_geometry(icon_2d, height=inlay_depth)
            parts.append(PartItem(name=f"Icon_{icon_name}_Inlay", mesh=mesh_icon, extruder=extruder_icon))

    elif text_mode == "debossed":
        deboss_depth = min(text_thickness, base_thickness - 0.8)
        relief_union = text_2d if icon_2d is None else unary_union([text_2d, icon_2d])

        mesh_base_bottom = _extrude_geometry(base_2d, height=base_thickness - deboss_depth)
        base_top_2d = base_2d.difference(relief_union)
        mesh_base_top = _extrude_geometry(base_top_2d, height=deboss_depth)
        mesh_base_top.apply_translation([0, 0, base_thickness - deboss_depth])
        mesh_base = trimesh.util.concatenate([mesh_base_bottom, mesh_base_top])
        parts.append(PartItem(name="Base_Engraved", mesh=mesh_base, extruder=extruder_base))

    return parts

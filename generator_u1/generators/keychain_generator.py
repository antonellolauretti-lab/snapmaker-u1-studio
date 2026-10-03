import os
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import shapely.geometry as sg
from shapely.ops import unary_union, nearest_points
from shapely import affinity
import trimesh
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

from generator_u1.packager.snapmaker_3mf import PartItem

def _ensure_single_connected_polygon(geom: Any, bridge_width: float = 4.0) -> sg.Polygon:
    """
    Garantisce che la geometria della base sia un singolo poligono compatto e continuo (Polygon).
    Se l'unione booleana genera un MultiPolygon (isole staccate come l'asola o lettere separate),
    collega automaticamente le isole al corpo principale tramite un ponte solido di raccordo.
    """
    if geom is None or geom.is_empty:
        raise ValueError("Geometria base vuota.")

    if geom.geom_type == "Polygon":
        return geom

    # Se è un MultiPolygon o GeometryCollection:
    polys = [p for p in geom.geoms if p.geom_type == "Polygon" and not p.is_empty and p.area > 1e-2]
    if not polys:
        raise ValueError("Nessun poligono valido nella base.")
    if len(polys) == 1:
        return polys[0]

    # Ordina per area decrescente: il poligono principale con l'area maggiore è il corpo centrale
    polys.sort(key=lambda p: p.area, reverse=True)
    unified = polys[0]

    for p in polys[1:]:
        p_main, p_other = nearest_points(unified, p)
        dist = p_main.distance(p_other)
        if dist > 0:
            line = sg.LineString([p_main, p_other])
            connector = line.buffer(bridge_width / 2.0, cap_style=1, join_style=1)
            unified = unary_union([unified, p, connector])
        else:
            unified = unary_union([unified, p])

    unified = unified.buffer(0)
    if unified.geom_type == "MultiPolygon":
        unified = max(unified.geoms, key=lambda p: p.area)

    return unified

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

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"

ICON_ALIASES = {
    # Forme
    "heart": "cuore", "cuore": "cuore",
    "star": "stella", "stella": "stella",
    "lightning": "fulmine", "bolt": "fulmine", "fulmine": "fulmine",
    "clover": "quadrifoglio", "quadrifoglio": "quadrifoglio",
    "shamrock": "trifoglio", "trifoglio": "trifoglio",
    "crown": "corona", "corona": "corona",
    "moon": "luna", "luna": "luna",
    "sun": "sole", "sole": "sole",
    "cloud": "nuvola", "nuvola": "nuvola",
    "leaf": "foglia", "flower": "foglia", "foglia": "foglia", "fiore": "foglia",
    "gem": "diamante", "diamond": "diamante", "diamante": "diamante",
    "ribbon": "fiocco", "fiocco": "fiocco",
    "infinity": "infinito", "infinito": "infinito",
    "skull": "teschio", "teschio": "teschio",
    "cross": "croce", "croce": "croce",
    "trophy": "trofeo", "trofeo": "trofeo",
    "medal": "medaglia", "medaglia": "medaglia",
    # Animali
    "paw": "zampa", "zampa": "zampa",
    "dog": "cane", "cane": "cane",
    "cat": "gatto", "gatto": "gatto",
    "horse": "cavallo", "cavallo": "cavallo",
    "fish": "pesce", "pesce": "pesce",
    "bird": "uccello", "dove": "uccello", "uccello": "uccello", "uccellino": "uccello",
    "dragon": "dinosauro", "dinosaur": "dinosauro", "dinosauro": "dinosauro",
    "otter": "lontra", "dolphin": "lontra", "lontra": "lontra",
    "frog": "rana", "rana": "rana",
    "crow": "corvo", "corvo": "corvo",
    # Gaming
    "gamepad": "gamepad",
    "ghost": "fantasma", "fantasma": "fantasma",
    "shield": "scudo", "scudo": "scudo",
    "dice-d20": "dado_d20", "dice_d20": "dado_d20", "dado_d20": "dado_d20",
    "rocket": "astronave", "spaceship": "astronave", "astronave": "astronave",
    "dice": "dado", "dado": "dado",
    # Musica
    "music": "nota", "note": "nota", "nota": "nota", "doppia_nota": "nota",
    "guitar": "chitarra", "chitarra": "chitarra",
    "headphones": "cuffie", "cuffie": "cuffie",
    "palette": "tavolozza", "tavolozza": "tavolozza",
    # Sport
    "football": "calcio", "futbol": "calcio", "soccer": "calcio", "calcio": "calcio",
    "basketball": "basket", "basket": "basket",
    "fist": "boxe", "boxing": "boxe", "boxe": "boxe",
    "dumbbell": "manubrio", "manubrio": "manubrio",
    "bicycle": "bici", "bike": "bici", "bici": "bici",
    "mountain": "montagna", "montagna": "montagna",
    "campground": "tenda", "tent": "tenda", "tenda": "tenda",
    # Motori
    "car": "auto", "auto": "auto",
    "motorcycle": "moto", "motorbike": "moto", "moto": "moto",
    "truck": "camion", "camion": "camion",
    "plane": "aereo", "airplane": "aereo", "aereo": "aereo",
    "sailboat": "barca", "boat": "barca", "ship": "barca", "barca": "barca",
    # Simboli
    "anchor": "ancora", "ancora": "ancora",
    "fire": "fuoco", "flame": "fuoco", "fuoco": "fuoco",
    "tree": "albero", "albero": "albero",
    "camera": "fotocamera", "fotocamera": "fotocamera",
    "glasses": "occhiali", "sunglasses": "occhiali", "occhiali": "occhiali",
    "peace": "pace", "pace": "pace",
    "gift": "regalo", "regalo": "regalo",
    "coffee": "caffe", "mug": "caffe", "caffe": "caffe",
}

_PARSED_SVG_CACHE: Dict[str, Any] = {}

try:
    from generator_u1.assets.icons_data import ICONS_LIBRARY
    ICONS_DICT = {icon["id"].lower(): icon["d"] for icon in ICONS_LIBRARY if icon.get("d")}
except Exception:
    ICONS_DICT = {}

def _parse_svg_file_to_shapely(svg_path: Path) -> Optional[Any]:
    """Converte un file SVG in una geometria Shapely manifold e normalizzata."""
    try:
        content = svg_path.read_text(encoding="utf-8")
        d_matches = re.findall(r'd="([^"]+)"', content)
        if not d_matches:
            return None

        from svgpath2mpl import parse_path
        raw_polys = []
        for d in d_matches:
            p = parse_path(d)
            for pts in p.to_polygons():
                if len(pts) >= 3:
                    poly = sg.Polygon(pts).buffer(0)
                    if poly.is_valid and not poly.is_empty and poly.area > 1e-4:
                        raw_polys.append(poly)

        if not raw_polys:
            return None

        raw_polys.sort(key=lambda x: x.area, reverse=True)
        combined = raw_polys[0]
        for other in raw_polys[1:]:
            combined = combined.symmetric_difference(other)

        if not combined.is_valid:
            combined = combined.buffer(0)

        # Inverti asse Y (SVG ha origine top-left, 3D cartesiano bottom-left)
        combined = affinity.scale(combined, yfact=-1.0, origin=(0, 0))
        return _normalize_to_unit(combined)
    except Exception as e:
        print(f"Errore parsing SVG {svg_path}: {e}")
        return None

def _get_vector_icon(name: str) -> Optional[Any]:
    """
    Libreria di sagome e simboli vettoriali 2D caricata dinamicamente
    dai file SVG in generator_u1/assets/icons/.
    Supporta l'aggiunta di nuovi SVG senza modificare il codice Python.
    """
    if not name or name.lower() in ("none", "", "nessuna"):
        return None

    name_clean = name.lower().strip()
    target_stem = ICON_ALIASES.get(name_clean, name_clean)

    if target_stem in _PARSED_SVG_CACHE:
        return _PARSED_SVG_CACHE[target_stem]

    # 1. Cerca file .svg corrispondente in assets/icons/
    if ICONS_DIR.is_dir():
        svg_candidate = ICONS_DIR / f"{target_stem}.svg"
        if svg_candidate.is_file():
            geom = _parse_svg_file_to_shapely(svg_candidate)
            if geom is not None:
                _PARSED_SVG_CACHE[target_stem] = geom
                return geom

        # Cerca tra tutti i file .svg senza distinzione maiuscole/minuscole
        for f in ICONS_DIR.glob("*.svg"):
            if f.stem.lower() in (target_stem, name_clean):
                geom = _parse_svg_file_to_shapely(f)
                if geom is not None:
                    _PARSED_SVG_CACHE[target_stem] = geom
                    return geom

    # 2. Fallback su ICONS_DICT se presente (per retrocompatibilità)
    svg_d = ICONS_DICT.get(name_clean) or ICONS_DICT.get(target_stem)
    if svg_d:
        try:
            from svgpath2mpl import parse_path
            p = parse_path(svg_d)
            raw_polys = [sg.Polygon(pts).buffer(0) for pts in p.to_polygons() if len(pts) >= 3]
            if raw_polys:
                raw_polys.sort(key=lambda x: x.area, reverse=True)
                poly = raw_polys[0]
                for other in raw_polys[1:]:
                    poly = poly.symmetric_difference(other)
                poly = affinity.scale(poly, yfact=-1.0, origin=(0, 0))
                normalized = _normalize_to_unit(poly)
                _PARSED_SVG_CACHE[target_stem] = normalized
                return normalized
        except Exception as e:
            print(f"Errore fallback icona SVG {name}: {e}")

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

    # 4. Creazione del Contorno della Base e dell'Asola Anello
    hole_radius = hole_diameter / 2.0
    hole_wall = max(3.0, hole_radius * 1.0)
    outer_radius = hole_radius + hole_wall

    if base_style == "contour":
        # Rinforzo strutturale anti-rottura: garantisce almeno 8-10 mm di spessore continuo tra parole e simboli
        font_h = fg_maxy - fg_miny
        min_structural_h = max(8.5, min(10.5, font_h * 0.70))

        # 1. Morphological closing per colmare gole profonde e insenature tra lettere/parole
        close_r = max(4.0, font_size * 0.30)
        closed_fg = foreground_union.buffer(close_r, resolution=16).buffer(-close_r, resolution=16)

        # 2. Ponte strutturale centrale lungo l'asse X che collega l'intero corpo del portachiavi
        spine_y0 = fg_mid_y - (min_structural_h / 2.0)
        spine_y1 = fg_mid_y + (min_structural_h / 2.0)
        spine_box = sg.box(fg_minx + padding_y, spine_y0, fg_maxx - padding_y, spine_y1)

        # Unione base con ponte strutturale e arrotondamento smussato
        base_contour = unary_union([
            closed_fg.buffer(padding_y, resolution=16),
            spine_box
        ]).buffer(0)
        base_contour = base_contour.buffer(0.8, resolution=16).buffer(-0.8, resolution=16)
        if hole_enabled:
            if hole_position == "left":
                hx = fg_minx - hole_radius - (hole_wall * 0.2)
                hy = fg_mid_y
                hole_ear = sg.Point(hx, hy).buffer(outer_radius, resolution=32)
                bridge = sg.box(hx, hy - outer_radius * 0.75, fg_minx + padding_x, hy + outer_radius * 0.75)
                base_contour = unary_union([base_contour, hole_ear, bridge])
            elif hole_position == "right":
                hx = fg_maxx + hole_radius + (hole_wall * 0.2)
                hy = fg_mid_y
                hole_ear = sg.Point(hx, hy).buffer(outer_radius, resolution=32)
                bridge = sg.box(fg_maxx - padding_x, hy - outer_radius * 0.75, hx, hy + outer_radius * 0.75)
                base_contour = unary_union([base_contour, hole_ear, bridge])
            else:  # top
                hx = (fg_minx + fg_maxx) / 2.0
                hy = fg_maxy + hole_radius + (hole_wall * 0.2)
                hole_ear = sg.Point(hx, hy).buffer(outer_radius, resolution=32)
                bridge = sg.box(hx - outer_radius * 0.75, fg_mid_y, hx + outer_radius * 0.75, hy)
                base_contour = unary_union([base_contour, hole_ear, bridge])
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

    # Assicura tassativamente che la base sia un poligono unico e compatto prima del foro
    base_contour = _ensure_single_connected_polygon(base_contour, bridge_width=outer_radius * 1.2)

    # 5. Applicazione del Foro
    if hole_enabled:
        hole_geom = sg.Point(hx, hy).buffer(hole_radius, resolution=32)
        base_2d = base_contour.difference(hole_geom)
        base_2d = _ensure_single_connected_polygon(base_2d, bridge_width=outer_radius * 1.2)
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

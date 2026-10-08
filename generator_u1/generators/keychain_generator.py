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
from generator_u1.font_resolver import (
    get_font_properties,
    get_font_dilation_offset,
    apply_text_polygon_buffer
)

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

def _normalize_to_unit(geom: Any, by_height: bool = False) -> Any:
    """Trasla e scala una forma in un rettangolo normalizzato di altezza unitaria."""
    minx, miny, maxx, maxy = geom.bounds
    w = maxx - minx
    h = maxy - miny
    if by_height:
        scale = h if h > 1e-6 else 1.0
    else:
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
    "pokeball": "pokeball", "pokéball": "pokeball", "poke_ball": "pokeball", "sfera_pokemon": "pokeball",
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
    # Easter Egg Aziendale
    "txt": "txt_ennova_logo",
    "ennova": "txt_ennova_logo",
    "txt ennova": "txt_ennova_logo",
    "txt_ennova": "txt_ennova_logo",
    "txt_ennova_logo": "txt_ennova_logo",
}

_PARSED_SVG_CACHE: Dict[str, Any] = {}

try:
    from generator_u1.assets.icons_data import ICONS_LIBRARY
    ICONS_DICT = {icon["id"].lower(): icon["d"] for icon in ICONS_LIBRARY if icon.get("d")}
except Exception:
    ICONS_DICT = {}

def _parse_svg_file_to_shapely(svg_path: Path, by_height: bool = False) -> Optional[Any]:
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
        return _normalize_to_unit(combined, by_height=by_height)
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
    is_txt_logo = target_stem in ("txt_ennova_logo", "txt", "ennova", "txt ennova", "txt_ennova")

    if target_stem in _PARSED_SVG_CACHE:
        return _PARSED_SVG_CACHE[target_stem]

    # 1. Cerca file .svg corrispondente in assets/icons/
    if ICONS_DIR.is_dir():
        svg_candidate = ICONS_DIR / f"{target_stem}.svg"
        if svg_candidate.is_file():
            geom = _parse_svg_file_to_shapely(svg_candidate, by_height=is_txt_logo)
            if geom is not None:
                _PARSED_SVG_CACHE[target_stem] = geom
                return geom

        # Cerca tra tutti i file .svg senza distinzione maiuscole/minuscole
        for f in ICONS_DIR.glob("*.svg"):
            if f.stem.lower() in (target_stem, name_clean):
                geom = _parse_svg_file_to_shapely(f, by_height=is_txt_logo)
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

def _generate_text_line_2d(
    text: str,
    fp: FontProperties,
    font_size: float,
    letter_spacing: float = 0.0,
    dilation_offset: float = 0.0
) -> sg.base.BaseGeometry:
    """Genera la geometria 2D vettoriale di una singola riga di testo con corretta gestione dei fori e buffer opzionale."""
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

def generate_keychain_parts(params: Dict[str, Any]) -> List[PartItem]:
    """
    Genera le mesh 3D della Base, del Testo (1 o 2 righe sovrapposte) e dell'eventuale Icona
    rispettando la configurazione degli utensili Snapmaker U1 (T0..T3).
    """
    text = (params.get("text_line1") or params.get("text") or "TUO NOME").strip()
    font_family = params.get("font_family", "Anton")
    font_path = params.get("font_path")
    font_size = float(params.get("font_size", 14.0))
    letter_spacing = float(params.get("letter_spacing", 0.0))
    base_style = params.get("base_style", "rectangle")
    base_thickness = float(params.get("base_thickness", 3.2))
    if base_thickness < 3.0:
        base_thickness = 3.2
    text_thickness = float(params.get("text_thickness", 1.4))
    text_mode = params.get("text_mode", "embossed")
    corner_radius = float(params.get("corner_radius", 4.0))
    padding_x = float(params.get("padding_x", 5.0))
    padding_y = float(params.get("padding_y", 2.0))
    hole_enabled = bool(params.get("hole_enabled", True))
    hole_position = params.get("hole_position", "left")
    hole_diameter = float(params.get("hole_diameter", 5.0))
    icon_name = params.get("icon_name") or params.get("icon_id") or "none"
    icon_position = params.get("icon_position", "left")
    extruder_base = int(params.get("extruder_base", 0))
    extruder_text = int(params.get("extruder_text", 1))

    # Parametri Seconda Riga (Sottotitolo / Cognome)
    line2_enabled = bool(params.get("line2_enabled", False))
    text_line2 = (params.get("text_line2") or "").strip()
    font_size_line2 = float(params.get("font_size_line2", font_size * 0.75))
    letter_spacing_line2 = float(params.get("letter_spacing_line2", 0.0))
    line_spacing = float(params.get("line_spacing", 3.5))
    font_family_line2 = params.get("font_family_line2") or font_family
    font_path_line2 = params.get("font_path_line2") or font_path

    extruder_line2 = int(params.get("extruder_line2", -1))
    if extruder_line2 == -1:
        extruder_line2 = extruder_text

    extruder_icon = int(params.get("extruder_icon", -1))
    if extruder_icon == -1:
        extruder_icon = extruder_text

    # Controllo speciale TXT ENNOVA: sincronizzazione 100% con TXT_ENNOVA_Keyring.3mf
    clean_txt = text.strip().upper()
    is_txt_model = (
        clean_txt == "TXT ENNOVA"
        and not line2_enabled
        and base_style == "contour"
    )
    if is_txt_model:
        try:
            from generator_u1.assets.txt_logo_geometry import get_exact_txt_keyring_geometries
            b2d, t2d, s2d = get_exact_txt_keyring_geometries()

            m_base = _extrude_geometry(b2d, height=base_thickness)
            m_text = _extrude_geometry(t2d, height=text_thickness)
            m_text.apply_translation([0, 0, base_thickness])
            m_sym = _extrude_geometry(s2d, height=text_thickness)
            m_sym.apply_translation([0, 0, base_thickness])

            return [
                PartItem(name="Base_Portachiavi", mesh=m_base, extruder=extruder_base),
                PartItem(name="Simbolo_Fluido_Logo", mesh=m_sym, extruder=2),
                PartItem(name="Testo_TXT_ENNOVA", mesh=m_text, extruder=extruder_text)
            ]
        except Exception as e:
            print(f"Avviso generatore TXT ENNOVA dedicato: {e}")

    # 1. Risoluzione Font tramite font_resolver (supporta cloud e font incorporati)
    fp1 = get_font_properties(font_family, font_path)
    fp2 = get_font_properties(font_family_line2, font_path_line2)
    offset1 = get_font_dilation_offset(font_family)
    offset2 = get_font_dilation_offset(font_family_line2)

    # 2. Generazione vettoriale Riga 1 (con eventuale offset di dilatazione per tratti sottili)
    # 2. Generazione vettoriale Riga 1 (con eventuale offset di dilatazione per tratti sottili)
    t1_norm_letters = None
    t1_norm_outline = None
    if clean_txt == "TXT ENNOVA":
        try:
            from generator_u1.assets.txt_logo_geometry import get_txt_letters_geometry
            t1_raw = get_txt_letters_geometry(target_height=font_size)
        except Exception:
            t1_raw = _generate_text_line_2d(text, fp1, font_size, letter_spacing, dilation_offset=offset1)
    elif clean_txt in ("POKEMON", "POKÉMON"):
        try:
            from generator_u1.assets.pokemon_geometry import (
                get_pokemon_letters_geometry,
                get_pokemon_outline_border_geometry,
                get_pokemon_contour_geometry,
            )
            g_letters = get_pokemon_letters_geometry(target_height=font_size)
            g_outline = get_pokemon_outline_border_geometry(target_height=font_size)
            g_contour = get_pokemon_contour_geometry(target_height=font_size)
            c_minx, c_miny, c_maxx, c_maxy = g_contour.bounds
            t1_norm_letters = affinity.translate(g_letters, xoff=-c_minx, yoff=-c_miny)
            t1_norm_outline = affinity.translate(g_outline, xoff=-c_minx, yoff=-c_miny)
            t1_raw = affinity.translate(g_contour, xoff=-c_minx, yoff=-c_miny)
        except Exception:
            t1_raw = _generate_text_line_2d(text, fp1, font_size, letter_spacing, dilation_offset=offset1)
    else:
        t1_raw = _generate_text_line_2d(text, fp1, font_size, letter_spacing, dilation_offset=offset1)
    t1_minx, t1_miny, t1_maxx, t1_maxy = t1_raw.bounds
    w1 = t1_maxx - t1_minx
    h1 = t1_maxy - t1_miny
    t1_norm = affinity.translate(t1_raw, xoff=-t1_minx, yoff=-t1_miny)

    # 3. Generazione vettoriale Riga 2 (se presente e abilitata)
    t2_norm = None
    w2, h2 = 0.0, 0.0
    if line2_enabled and text_line2:
        clean_txt2 = text_line2.strip().upper()
        try:
            if clean_txt2 == "TXT ENNOVA":
                from generator_u1.assets.txt_logo_geometry import get_txt_letters_geometry
                t2_raw = get_txt_letters_geometry(target_height=font_size_line2)
            elif clean_txt2 in ("POKEMON", "POKÉMON"):
                from generator_u1.assets.pokemon_geometry import get_pokemon_letters_geometry
                t2_raw = get_pokemon_letters_geometry(target_height=font_size_line2)
            else:
                t2_raw = _generate_text_line_2d(text_line2, fp2, font_size_line2, letter_spacing_line2, dilation_offset=offset2)
            t2_minx, t2_miny, t2_maxx, t2_maxy = t2_raw.bounds
            w2 = t2_maxx - t2_minx
            h2 = t2_maxy - t2_miny
            t2_norm = affinity.translate(t2_raw, xoff=-t2_minx, yoff=-t2_miny)
        except Exception as e:
            print(f"Avviso: impossibile generare riga 2 '{text_line2}': {e}")
            t2_norm = None

    # 4. Impilamento e Centratura Orizzontale delle 2 righe
    if t2_norm is not None:
        w_text = max(w1, w2)
        x1 = (w_text - w1) / 2.0
        x2 = (w_text - w2) / 2.0
        y1 = h2 + line_spacing  # Riga 1 in alto
        y2 = 0.0                # Riga 2 in basso

        text1_2d = affinity.translate(t1_norm, xoff=x1, yoff=y1)
        text2_2d = affinity.translate(t2_norm, xoff=x2, yoff=y2)
        text_2d = unary_union([text1_2d, text2_2d])
    else:
        x1 = 0.0
        y1 = 0.0
        text1_2d = t1_norm
        text2_2d = None
        text_2d = t1_norm

    text1_letters_2d = affinity.translate(t1_norm_letters, xoff=x1, yoff=y1) if t1_norm_letters else None
    text1_outline_2d = affinity.translate(t1_norm_outline, xoff=x1, yoff=y1) if t1_norm_outline else None

    minx, miny, maxx, maxy = text_2d.bounds
    mid_y = (miny + maxy) / 2.0

    # 5. Generazione e posizionamento dell'Icona Vettoriale
    is_txt_logo = str(icon_name).lower().strip() in ("txt_ennova_logo", "txt", "ennova", "txt ennova", "txt_ennova")
    is_pokeball = str(icon_name).lower().strip() in ("pokeball", "poke_ball", "pokéball", "poke ball", "sfera_pokemon")
    pokeball_top_2d = None
    pokeball_bottom_2d = None
    pokeball_band_2d = None
    pokeball_button_2d = None
    icon_raw = _get_vector_icon(icon_name) if (not is_txt_logo and not is_pokeball) else None
    icon_2d = None

    if is_txt_logo:
        try:
            from generator_u1.assets.txt_logo_geometry import get_txt_modular_components
            s_mod, _, _ = get_txt_modular_components()
            h_ref = maxy - miny
            s_scale = h1 / 5.451072445428663
            protrusion = (7.4555 - 5.45107) / 2.0 * s_scale

            # Barretta Verticale Divisoria: estesa a tutta altezza se sono presenti 2 righe
            d_sw = 0.950 * s_scale
            if text2_2d is not None:
                d_sh = h_ref + 2.0 * protrusion
            else:
                d_sh = 7.4555 * s_scale
            d_scaled = sg.box(0, 0, d_sw, d_sh)
            gap_bar_text = 1.727 * s_scale
            spacing_icon = 1.867 * s_scale

            if str(icon_position).lower() == "left":
                x_bar_offset = minx - d_sw - gap_bar_text
            else:
                x_bar_offset = maxx + gap_bar_text
            y_bar_offset = mid_y - (d_sh / 2.0)
            d_placed = affinity.translate(d_scaled, xoff=x_bar_offset, yoff=y_bar_offset)
            text1_2d = unary_union([text1_2d, d_placed])
            text_2d = unary_union([text1_2d] + ([text2_2d] if text2_2d else []))
            minx, miny, maxx, maxy = text_2d.bounds

            # Simbolo Fluido (solo nuvoletta quadrata, colore simbolo)
            s_minx, s_miny, s_maxx, s_maxy = s_mod.bounds
            s_norm = affinity.translate(s_mod, xoff=-s_minx, yoff=-s_miny)
            icon_scaled = affinity.scale(s_norm, xfact=s_scale, yfact=s_scale, origin=(0, 0))
            iw = (s_maxx - s_minx) * s_scale
            ih = (s_maxy - s_miny) * s_scale
            if str(icon_position).lower() == "left":
                ix = minx - iw - spacing_icon
            else:
                ix = maxx + spacing_icon
            iy = mid_y - (ih / 2.0)
            icon_2d = affinity.translate(icon_scaled, xoff=ix, yoff=iy)
        except Exception as e:
            print(f"Errore gestione logo TXT portachiavi: {e}")
    elif is_pokeball:
        try:
            from generator_u1.assets.pokeball_geometry import (
                get_pokeball_modular_components,
                get_pokeball_geometry,
            )
            if clean_txt in ("POKEMON", "POKÉMON"):
                h_P = 10.9400897 * (font_size / 14.0)
                pokeball_diam = 0.78 * h_P
            else:
                pokeball_diam = min(font_size * 0.75, (maxy - miny) * 0.75)
                if pokeball_diam < 6.0:
                    pokeball_diam = 8.5

            p_top, p_bot, p_band, p_btn = get_pokeball_modular_components(target_diameter=pokeball_diam)
            p_full = get_pokeball_geometry(target_diameter=pokeball_diam)
            iw = pokeball_diam
            ih = pokeball_diam
            spacing_icon = 2.5
            if clean_txt in ("POKEMON", "POKÉMON"):
                y_center_P = y1 + (10.9400897 * (font_size / 14.0)) / 2.0
                iy = y_center_P - (ih / 2.0)
            else:
                iy = mid_y - (ih / 2.0)

            if str(icon_position).lower() == "left":
                ix = minx - iw - spacing_icon
            else:
                ix = maxx + spacing_icon

            pokeball_top_2d = affinity.translate(p_top, xoff=ix, yoff=iy)
            pokeball_bottom_2d = affinity.translate(p_bot, xoff=ix, yoff=iy)
            pokeball_band_2d = affinity.translate(p_band, xoff=ix, yoff=iy)
            pokeball_button_2d = affinity.translate(p_btn, xoff=ix, yoff=iy)
            icon_2d = affinity.translate(p_full, xoff=ix, yoff=iy)
        except Exception as e:
            print(f"Errore gestione Pokeball portachiavi: {e}")
    elif icon_raw is not None:
        icon_h = min(font_size * 0.95, (maxy - miny) * 0.85)
        spacing_icon = 2.5
        icon_scaled = affinity.scale(icon_raw, xfact=icon_h, yfact=icon_h, origin=(0, 0))
        iminx, iminy, imaxx, imaxy = icon_scaled.bounds
        iw = imaxx - iminx
        ih = imaxy - iminy
        icon_norm = affinity.translate(icon_scaled, xoff=-iminx, yoff=-iminy)

        if str(icon_position).lower() == "left":
            ix = minx - iw - spacing_icon
            iy = mid_y - (ih / 2.0)
            icon_2d = affinity.translate(icon_norm, xoff=ix, yoff=iy)
        else:
            ix = maxx + spacing_icon
            iy = mid_y - (ih / 2.0)
            icon_2d = affinity.translate(icon_norm, xoff=ix, yoff=iy)

    # 6. Unione elementi in rilievo per il calcolo della base
    foreground_items = [text1_2d]
    if text2_2d is not None:
        foreground_items.append(text2_2d)
    if icon_2d is not None:
        foreground_items.append(icon_2d)
    foreground_union = unary_union(foreground_items)

    fg_minx, fg_miny, fg_maxx, fg_maxy = foreground_union.bounds
    fg_mid_y = (fg_miny + fg_maxy) / 2.0

    # 7. Helper per creazione Contorno Base e Asola Anello
    hole_radius = hole_diameter / 2.0
    hole_wall = max(3.0, hole_radius * 1.0)
    outer_radius = hole_radius + hole_wall

    def _generate_base_contour_and_hole(fg_u: Any, current_fs: float):
        fg_u_minx, fg_u_miny, fg_u_maxx, fg_u_maxy = fg_u.bounds
        fg_u_mid_y = (fg_u_miny + fg_u_maxy) / 2.0

        if base_style == "contour":
            font_h = fg_u_maxy - fg_u_miny
            min_structural_h = max(8.5, min(14.0, font_h * 0.50))

            # Morphological closing per colmare gole profonde tra lettere e righe sovrapposte
            close_r = max(4.0, current_fs * 0.30)
            closed_fg = fg_u.buffer(close_r, resolution=16).buffer(-close_r, resolution=16)

            # Ponte strutturale centrale lungo l'asse X che collega l'intero corpo del portachiavi
            spine_y0 = fg_u_mid_y - (min_structural_h / 2.0)
            spine_y1 = fg_u_mid_y + (min_structural_h / 2.0)
            spine_box = sg.box(fg_u_minx + padding_y, spine_y0, fg_u_maxx - padding_y, spine_y1)

            b_contour = unary_union([
                closed_fg.buffer(padding_y, resolution=16),
                spine_box
            ]).buffer(0)
            b_contour = b_contour.buffer(0.8, resolution=16).buffer(-0.8, resolution=16)

            if hole_enabled:
                if hole_position == "left":
                    hx = fg_u_minx - hole_radius - (hole_wall * 0.2)
                    hy = fg_u_mid_y
                    hole_ear = sg.Point(hx, hy).buffer(outer_radius, resolution=32)
                    bridge = sg.box(hx, hy - outer_radius * 0.75, fg_u_minx + padding_x, hy + outer_radius * 0.75)
                    b_contour = unary_union([b_contour, hole_ear, bridge])
                elif hole_position == "right":
                    hx = fg_u_maxx + hole_radius + (hole_wall * 0.2)
                    hy = fg_u_mid_y
                    hole_ear = sg.Point(hx, hy).buffer(outer_radius, resolution=32)
                    bridge = sg.box(fg_u_maxx - padding_x, hy - outer_radius * 0.75, hx, hy + outer_radius * 0.75)
                    b_contour = unary_union([b_contour, hole_ear, bridge])
                else:  # top
                    hx = (fg_u_minx + fg_u_maxx) / 2.0
                    hy = fg_u_maxy + hole_radius + (hole_wall * 0.2)
                    hole_ear = sg.Point(hx, hy).buffer(outer_radius, resolution=32)
                    bridge = sg.box(hx - outer_radius * 0.75, fg_u_mid_y, hx + outer_radius * 0.75, hy)
                    b_contour = unary_union([b_contour, hole_ear, bridge])
        else:
            x_left_extra = (hole_radius * 2 + hole_wall * 2) if (hole_enabled and hole_position == "left") else padding_x
            x_right_extra = (hole_radius * 2 + hole_wall * 2) if (hole_enabled and hole_position == "right") else padding_x
            y_top_extra = (hole_radius * 2 + hole_wall * 2) if (hole_enabled and hole_position == "top") else padding_y

            x0 = fg_u_minx - x_left_extra
            x1 = fg_u_maxx + x_right_extra
            y0 = fg_u_miny - padding_y
            y1 = fg_u_maxy + y_top_extra

            r = min(corner_radius, (x1 - x0) / 4.0, (y1 - y0) / 4.0)
            inner_box = sg.box(x0 + r, y0 + r, x1 - r, y1 - r)
            b_contour = inner_box.buffer(r, resolution=16)

            if hole_enabled:
                if hole_position == "left":
                    hx = x0 + hole_radius + hole_wall
                    hy = fg_u_mid_y
                elif hole_position == "right":
                    hx = x1 - (hole_radius + hole_wall)
                    hy = fg_u_mid_y
                else:
                    hx = (fg_u_minx + fg_u_maxx) / 2.0
                    hy = y1 - (hole_radius + hole_wall)

        b_contour = _ensure_single_connected_polygon(b_contour, bridge_width=outer_radius * 1.2)

        if hole_enabled:
            h_geom = sg.Point(hx, hy).buffer(hole_radius, resolution=32)
            b_2d = b_contour.difference(h_geom)
            b_2d = _ensure_single_connected_polygon(b_2d, bridge_width=outer_radius * 1.2)
        else:
            b_2d = b_contour

        return b_2d

    base_2d = _generate_base_contour_and_hole(foreground_union, font_size)

    # 8. Auto-scaling su lunghezza X (lunghezza massima 80.0 mm / 8,0 cm)
    MAX_KEYCHAIN_LENGTH = 80.0
    bx0, _, bx1, _ = base_2d.bounds
    initial_total_width = bx1 - bx0

    if initial_total_width > MAX_KEYCHAIN_LENGTH:
        fg_w0 = fg_maxx - fg_minx
        w_fixed = initial_total_width - fg_w0
        # Calcolo scala analitica proporzionale lungo X e Y per non eccedere 80.0 mm
        scale_factor = (MAX_KEYCHAIN_LENGTH - w_fixed) / fg_w0 if fg_w0 > 0 else (MAX_KEYCHAIN_LENGTH / initial_total_width)
        scale_factor = max(0.25, min(scale_factor, 1.0))

        text1_2d = affinity.scale(text1_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if text1_letters_2d is not None:
            text1_letters_2d = affinity.scale(text1_letters_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if text1_outline_2d is not None:
            text1_outline_2d = affinity.scale(text1_outline_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if text2_2d is not None:
            text2_2d = affinity.scale(text2_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if icon_2d is not None:
            icon_2d = affinity.scale(icon_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if is_pokeball and pokeball_top_2d is not None:
            pokeball_top_2d = affinity.scale(pokeball_top_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            pokeball_bottom_2d = affinity.scale(pokeball_bottom_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            pokeball_band_2d = affinity.scale(pokeball_band_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            pokeball_button_2d = affinity.scale(pokeball_button_2d, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))

        foreground_items = [text1_2d]
        if text2_2d is not None:
            foreground_items.append(text2_2d)
        if icon_2d is not None:
            foreground_items.append(icon_2d)
        foreground_union = unary_union(foreground_items)

        base_2d = _generate_base_contour_and_hole(foreground_union, font_size * scale_factor)

        # Controllo di clamp di sicurezza per micro-tolleranze
        bw0, _, bw1, _ = base_2d.bounds
        current_w = bw1 - bw0
        if current_w > MAX_KEYCHAIN_LENGTH:
            clamp_scale = MAX_KEYCHAIN_LENGTH / current_w
            text1_2d = affinity.scale(text1_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
            if text1_letters_2d is not None:
                text1_letters_2d = affinity.scale(text1_letters_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
            if text1_outline_2d is not None:
                text1_outline_2d = affinity.scale(text1_outline_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
            if text2_2d is not None:
                text2_2d = affinity.scale(text2_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
            if icon_2d is not None:
                icon_2d = affinity.scale(icon_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
            if is_pokeball and pokeball_top_2d is not None:
                pokeball_top_2d = affinity.scale(pokeball_top_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
                pokeball_bottom_2d = affinity.scale(pokeball_bottom_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
                pokeball_band_2d = affinity.scale(pokeball_band_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
                pokeball_button_2d = affinity.scale(pokeball_button_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(0, 0))
            foreground_items = [text1_2d]
            if text2_2d is not None:
                foreground_items.append(text2_2d)
            if icon_2d is not None:
                foreground_items.append(icon_2d)
            foreground_union = unary_union(foreground_items)
            base_2d = _generate_base_contour_and_hole(foreground_union, font_size * scale_factor * clamp_scale)

    # 9. Centratura delle geometrie in (0, 0)
    bx0, by0, bx1, by1 = base_2d.bounds
    cx = (bx0 + bx1) / 2.0
    cy = (by0 + by1) / 2.0

    base_2d = affinity.translate(base_2d, xoff=-cx, yoff=-cy)
    text1_2d = affinity.translate(text1_2d, xoff=-cx, yoff=-cy)
    if text1_letters_2d is not None:
        text1_letters_2d = affinity.translate(text1_letters_2d, xoff=-cx, yoff=-cy)
    if text1_outline_2d is not None:
        text1_outline_2d = affinity.translate(text1_outline_2d, xoff=-cx, yoff=-cy)
    if text2_2d is not None:
        text2_2d = affinity.translate(text2_2d, xoff=-cx, yoff=-cy)
    if icon_2d is not None:
        icon_2d = affinity.translate(icon_2d, xoff=-cx, yoff=-cy)
    if is_pokeball and pokeball_top_2d is not None:
        pokeball_top_2d = affinity.translate(pokeball_top_2d, xoff=-cx, yoff=-cy)
        pokeball_bottom_2d = affinity.translate(pokeball_bottom_2d, xoff=-cx, yoff=-cy)
        pokeball_band_2d = affinity.translate(pokeball_band_2d, xoff=-cx, yoff=-cy)
        pokeball_button_2d = affinity.translate(pokeball_button_2d, xoff=-cx, yoff=-cy)

    # 10. Estrusione 3D e Definizione Parti
    parts: List[PartItem] = []

    if text_mode == "embossed":
        mesh_base = _extrude_geometry(base_2d, height=base_thickness)
        parts.append(PartItem(name="Base", mesh=mesh_base, extruder=extruder_base))

        if text1_letters_2d is not None and text1_outline_2d is not None:
            # Doppio strato ufficiale Pokémon: Bordo Blu spesso Z=1.0mm + Lettere Gialle Z=1.4mm
            mesh_outline = _extrude_geometry(text1_outline_2d, height=1.0)
            mesh_outline.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name="Text_Pokemon_Outline", mesh=mesh_outline, extruder=1, color="#2a75bb"))

            mesh_letters = _extrude_geometry(text1_letters_2d, height=text_thickness)
            mesh_letters.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name="Text_Pokemon_Letters", mesh=mesh_letters, extruder=2, color="#ffcb05"))
        else:
            clean_t1 = re.sub(r"[^a-zA-Z0-9_-]", "", text) or "Riga1"
            mesh_text1 = _extrude_geometry(text1_2d, height=text_thickness)
            mesh_text1.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name=f"Text_{clean_t1}", mesh=mesh_text1, extruder=extruder_text))

        if text2_2d is not None:
            clean_t2 = re.sub(r"[^a-zA-Z0-9_-]", "", text_line2) or "Riga2"
            mesh_text2 = _extrude_geometry(text2_2d, height=text_thickness)
            mesh_text2.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name=f"Text_{clean_t2}", mesh=mesh_text2, extruder=extruder_line2))

        if is_pokeball and pokeball_top_2d is not None:
            m_top = _extrude_geometry(pokeball_top_2d, height=text_thickness)
            m_top.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name="Icon_Pokeball_Top", mesh=m_top, extruder=3, color="#ee1515"))

            m_bot = _extrude_geometry(pokeball_bottom_2d, height=text_thickness)
            m_bot.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name="Icon_Pokeball_Bottom", mesh=m_bot, extruder=1, color="#ffffff"))

            m_band = _extrude_geometry(pokeball_band_2d, height=text_thickness)
            m_band.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name="Icon_Pokeball_Band", mesh=m_band, extruder=0, color="#1a1a1a"))

            m_btn = _extrude_geometry(pokeball_button_2d, height=text_thickness)
            m_btn.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name="Icon_Pokeball_Button", mesh=m_btn, extruder=1, color="#ffffff"))
        elif icon_2d is not None:
            mesh_icon = _extrude_geometry(icon_2d, height=text_thickness)
            mesh_icon.apply_translation([0, 0, base_thickness])
            parts.append(PartItem(name=f"Icon_{icon_name}", mesh=mesh_icon, extruder=extruder_icon))

    elif text_mode == "flush":
        inlay_depth = min(text_thickness, base_thickness * 0.5)
        relief_items = [text1_2d]
        if text2_2d is not None:
            relief_items.append(text2_2d)
        if icon_2d is not None:
            relief_items.append(icon_2d)
        relief_union = unary_union(relief_items)

        base_bottom_2d = base_2d.difference(relief_union)
        mesh_base_bottom = _extrude_geometry(base_bottom_2d, height=inlay_depth)
        mesh_base_top = _extrude_geometry(base_2d, height=base_thickness - inlay_depth)
        mesh_base_top.apply_translation([0, 0, inlay_depth])
        mesh_base = trimesh.util.concatenate([mesh_base_bottom, mesh_base_top])
        parts.append(PartItem(name="Base", mesh=mesh_base, extruder=extruder_base))

        if text1_letters_2d is not None and text1_outline_2d is not None:
            mesh_outline = _extrude_geometry(text1_outline_2d, height=1.0)
            parts.append(PartItem(name="Text_Pokemon_Outline_Inlay", mesh=mesh_outline, extruder=1, color="#2a75bb"))
            mesh_letters = _extrude_geometry(text1_letters_2d, height=inlay_depth)
            parts.append(PartItem(name="Text_Pokemon_Letters_Inlay", mesh=mesh_letters, extruder=2, color="#ffcb05"))
        else:
            clean_t1 = re.sub(r"[^a-zA-Z0-9_-]", "", text) or "Riga1"
            mesh_text1 = _extrude_geometry(text1_2d, height=inlay_depth)
            parts.append(PartItem(name=f"Text_{clean_t1}_Inlay", mesh=mesh_text1, extruder=extruder_text))

        if text2_2d is not None:
            clean_t2 = re.sub(r"[^a-zA-Z0-9_-]", "", text_line2) or "Riga2"
            mesh_text2 = _extrude_geometry(text2_2d, height=inlay_depth)
            parts.append(PartItem(name=f"Text_{clean_t2}_Inlay", mesh=mesh_text2, extruder=extruder_line2))

        if is_pokeball and pokeball_top_2d is not None:
            m_top = _extrude_geometry(pokeball_top_2d, height=inlay_depth)
            parts.append(PartItem(name="Icon_Pokeball_Top_Inlay", mesh=m_top, extruder=3, color="#ee1515"))
            m_bot = _extrude_geometry(pokeball_bottom_2d, height=inlay_depth)
            parts.append(PartItem(name="Icon_Pokeball_Bottom_Inlay", mesh=m_bot, extruder=1, color="#ffffff"))
            m_band = _extrude_geometry(pokeball_band_2d, height=inlay_depth)
            parts.append(PartItem(name="Icon_Pokeball_Band_Inlay", mesh=m_band, extruder=0, color="#1a1a1a"))
            m_btn = _extrude_geometry(pokeball_button_2d, height=inlay_depth)
            parts.append(PartItem(name="Icon_Pokeball_Button_Inlay", mesh=m_btn, extruder=1, color="#ffffff"))
        elif icon_2d is not None:
            mesh_icon = _extrude_geometry(icon_2d, height=inlay_depth)
            parts.append(PartItem(name=f"Icon_{icon_name}_Inlay", mesh=mesh_icon, extruder=extruder_icon))

    elif text_mode == "debossed":
        deboss_depth = min(text_thickness, base_thickness - 0.8)
        relief_items = [text1_2d]
        if text2_2d is not None:
            relief_items.append(text2_2d)
        if icon_2d is not None:
            relief_items.append(icon_2d)
        relief_union = unary_union(relief_items)

        mesh_base_bottom = _extrude_geometry(base_2d, height=base_thickness - deboss_depth)
        base_top_2d = base_2d.difference(relief_union)
        mesh_base_top = _extrude_geometry(base_top_2d, height=deboss_depth)
        mesh_base_top.apply_translation([0, 0, base_thickness - deboss_depth])
        mesh_base = trimesh.util.concatenate([mesh_base_bottom, mesh_base_top])
        parts.append(PartItem(name="Base_Engraved", mesh=mesh_base, extruder=extruder_base))

    return parts


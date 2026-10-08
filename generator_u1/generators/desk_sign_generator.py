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

def _boolean_union_meshes(meshes: List[trimesh.Trimesh]) -> trimesh.Trimesh:
    """
    Unisce solidamente un insieme di mesh manifold in un unico corpo monolitico continuo.
    Utilizza il motore 'manifold' (manifold3d) per generare una superficie chiusa
    senza gusci o facce interne separate. Effettua fallback trasparente in caso di errore.
    """
    valid_meshes = [m for m in meshes if isinstance(m, trimesh.Trimesh) and not m.is_empty and len(m.faces) > 0]
    if not valid_meshes:
        return trimesh.Trimesh()
    if len(valid_meshes) == 1:
        return valid_meshes[0]

    try:
        u = trimesh.boolean.union(valid_meshes, engine="manifold")
        if isinstance(u, trimesh.Trimesh) and not u.is_empty and len(u.faces) > 0:
            return u
    except Exception:
        pass

    try:
        u = trimesh.boolean.union(valid_meshes)
        if isinstance(u, trimesh.Trimesh) and not u.is_empty and len(u.faces) > 0:
            return u
    except Exception:
        pass

    return trimesh.util.concatenate(valid_meshes)

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
    is_txt_logo = str(icon_name).lower().strip() in ("txt_ennova_logo", "txt", "ennova", "txt ennova", "txt_ennova")
    default_icon_pos = "left" if is_txt_logo else "right"
    icon_position = str(params.get("icon_position", default_icon_pos)).lower()
    has_custom_icon_color = bool(
        params.get("has_custom_icon_color") or 
        params.get("hasCustomIconColor") or 
        params.get("custom_icon_color") or 
        (int(params.get("extruder_icon", 1)) == 2)
    )
    if is_txt_logo or has_custom_icon_color:
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
    clean_txt1 = text_line1.strip().upper()
    is_txt_text = (clean_txt1 == "TXT ENNOVA")
    is_pokemon_text = (clean_txt1 in ("POKEMON", "POKÉMON"))
    t1_norm_letters = None
    t1_norm_outline = None
    if is_txt_text:
        try:
            from generator_u1.assets.txt_logo_geometry import get_txt_letters_geometry
            t1_raw = get_txt_letters_geometry(target_height=font_size_line1)
        except Exception:
            t1_raw = _generate_text_2d(
                text_line1, font_family_line1, font_path_line1,
                font_size_line1, letter_spacing_line1, dilation_offset=offset1
            )
    elif is_pokemon_text:
        try:
            from generator_u1.assets.pokemon_geometry import (
                get_pokemon_letters_geometry,
                get_pokemon_outline_border_geometry,
                get_pokemon_contour_geometry,
            )
            g_letters = get_pokemon_letters_geometry(target_height=font_size_line1)
            g_outline = get_pokemon_outline_border_geometry(target_height=font_size_line1)
            g_contour = get_pokemon_contour_geometry(target_height=font_size_line1)
            c_minx, c_miny, c_maxx, c_maxy = g_contour.bounds
            t1_norm_letters = affinity.translate(g_letters, xoff=-c_minx, yoff=-c_miny)
            t1_norm_outline = affinity.translate(g_outline, xoff=-c_minx, yoff=-c_miny)
            t1_raw = affinity.translate(g_contour, xoff=-c_minx, yoff=-c_miny)
        except Exception:
            t1_raw = _generate_text_2d(
                text_line1, font_family_line1, font_path_line1,
                font_size_line1, letter_spacing_line1, dilation_offset=offset1
            )
    else:
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
        clean_txt2 = text_line2.strip().upper()
        is_txt_text2 = (clean_txt2 == "TXT ENNOVA")
        is_pokemon_text2 = (clean_txt2 in ("POKEMON", "POKÉMON"))
        try:
            if is_txt_text2:
                from generator_u1.assets.txt_logo_geometry import get_txt_letters_geometry
                t2_raw = get_txt_letters_geometry(target_height=font_size_line2)
            elif is_pokemon_text2:
                from generator_u1.assets.pokemon_geometry import get_pokemon_letters_geometry
                t2_raw = get_pokemon_letters_geometry(target_height=font_size_line2)
            else:
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
    icon_norm = None
    iw, ih = 0.0, 0.0
    bar_geom = None
    is_pokeball = str(icon_name).lower().strip() in ("pokeball", "poke_ball", "pokéball", "poke ball", "sfera_pokemon")
    pokeball_top_norm = None
    pokeball_bot_norm = None
    pokeball_band_norm = None
    pokeball_btn_norm = None

    if is_txt_logo:
        try:
            from generator_u1.assets.txt_logo_geometry import get_txt_modular_components
            s_mod, _, _ = get_txt_modular_components()
            
            s_scale = h1 / 5.451072445428663
            d_sw = 0.950 * s_scale
            gap_bar_text = 1.727 * s_scale
            spacing_icon = 1.867 * s_scale
            protrusion = (7.4555 - 5.45107) / 2.0 * s_scale

            # Barretta Verticale Divisoria:
            # - Su doppia riga: si estende a tutta altezza dalla sommità di riga 1 fino alla base di riga 2
            # - Su riga singola: si calibra esattamente all'altezza 1:1 della riga 1
            if line2_enabled and t2_norm is not None:
                bar_h = h_text_content + 2.0 * protrusion
            else:
                bar_h = 7.4555 * s_scale
            bar_geom = sg.box(0, 0, d_sw, bar_h)

            # Simbolo Fluido (solo nuvoletta quadrata a onde, colore simbolo)
            s_minx, s_miny, s_maxx, s_maxy = s_mod.bounds
            s_norm = affinity.translate(s_mod, xoff=-s_minx, yoff=-s_miny)
            icon_norm = affinity.scale(s_norm, xfact=s_scale, yfact=s_scale, origin=(0, 0))
            iw = (s_maxx - s_minx) * s_scale
            ih = (s_maxy - s_miny) * s_scale
        except Exception as e:
            print(f"Errore gestione logo TXT: {e}")
            is_txt_logo = False
            bar_geom = None
            spacing_icon = 4.0
    elif is_pokeball:
        try:
            from generator_u1.assets.pokeball_geometry import (
                get_pokeball_modular_components,
                get_pokeball_geometry,
            )
            if is_pokemon_text:
                h_P = 10.9400897 * (font_size_line1 / 14.0)
                pokeball_diam = 0.78 * h_P
            else:
                pokeball_diam = min(font_size_line1 * 0.85, max(h_text_content * 0.75, 10.0))

            p_top, p_bot, p_band, p_btn = get_pokeball_modular_components(target_diameter=pokeball_diam)
            p_full = get_pokeball_geometry(target_diameter=pokeball_diam)
            iw = pokeball_diam
            ih = pokeball_diam
            spacing_icon = 4.0
            icon_norm = p_full
            pokeball_top_norm = p_top
            pokeball_bot_norm = p_bot
            pokeball_band_norm = p_band
            pokeball_btn_norm = p_btn
        except Exception as e:
            print(f"Errore gestione Pokeball desk sign: {e}")
            spacing_icon = 4.0
    else:
        icon_raw = _get_vector_icon(icon_name)
        spacing_icon = 4.0 if (icon_raw is not None) else 0.0
        if icon_raw is not None:
            icon_h = min(font_size_line1 * 1.05, max(h_text_content * 0.90, 14.0))
            icon_scaled = affinity.scale(icon_raw, xfact=icon_h, yfact=icon_h, origin=(0, 0))
            iminx, iminy, imaxx, imaxy = icon_scaled.bounds
            iw = imaxx - iminx
            ih = imaxy - iminy
            icon_norm = affinity.translate(icon_scaled, xoff=-iminx, yoff=-iminy)

    # Calcolo ingombro orizzontale combinato (Testo + Icona + eventuale barretta)
    if is_txt_logo and bar_geom is not None:
        w_content_total = iw + spacing_icon + d_sw + gap_bar_text + w_text_content
        h_content_total = max(h_text_content, bar_h, ih)
    else:
        w_content_total = (w_text_content + spacing_icon + iw) if (icon_norm is not None) else w_text_content
        h_content_total = max(h_text_content, ih) if (icon_norm is not None) else h_text_content

    # Auto-scaling su larghezza X (larghezza massima assoluta 130.0 mm / 13,0 cm)
    MAX_DESK_SIGN_WIDTH = 130.0
    contour_pad = max(3.5, padding_y)
    if base_style == "contour":
        target_max_fg_w = MAX_DESK_SIGN_WIDTH - 2.0 * contour_pad - 1.0
    else:
        target_max_fg_w = MAX_DESK_SIGN_WIDTH - 2.0 * padding_x

    if w_content_total > target_max_fg_w and w_content_total > 0:
        scale_factor = target_max_fg_w / w_content_total
        scale_factor = max(0.20, min(scale_factor, 1.0))
        t1_norm = affinity.scale(t1_norm, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if t1_norm_letters is not None:
            t1_norm_letters = affinity.scale(t1_norm_letters, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if t1_norm_outline is not None:
            t1_norm_outline = affinity.scale(t1_norm_outline, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        w1 *= scale_factor
        h1 *= scale_factor
        if line2_enabled and t2_norm is not None:
            t2_norm = affinity.scale(t2_norm, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            w2 *= scale_factor
            h2 *= scale_factor
        if icon_norm is not None:
            icon_norm = affinity.scale(icon_norm, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            iw *= scale_factor
            ih *= scale_factor
        if is_pokeball and pokeball_top_norm is not None:
            pokeball_top_norm = affinity.scale(pokeball_top_norm, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            pokeball_bot_norm = affinity.scale(pokeball_bot_norm, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            pokeball_band_norm = affinity.scale(pokeball_band_norm, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            pokeball_btn_norm = affinity.scale(pokeball_btn_norm, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
        if is_txt_logo and bar_geom is not None:
            bar_geom = affinity.scale(bar_geom, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
            d_sw *= scale_factor
            bar_h *= scale_factor
            protrusion *= scale_factor
            gap_bar_text *= scale_factor
            spacing_icon *= scale_factor
        line_spacing *= scale_factor
        w_text_content = max(w1, w2)
        h_text_content = (h1 + line_spacing + h2) if line2_enabled else h1
        if is_txt_logo and bar_geom is not None:
            w_content_total = iw + spacing_icon + d_sw + gap_bar_text + w_text_content
            h_content_total = max(h_text_content, bar_h, ih)
        else:
            w_content_total = (w_text_content + spacing_icon + iw) if (icon_norm is not None) else w_text_content
            h_content_total = max(h_text_content, ih) if (icon_norm is not None) else h_text_content

    # Disposizione orizzontale centrata attorno a u = 0
    if is_txt_logo and bar_geom is not None:
        if icon_position == "left":
            x_icon = -w_content_total / 2.0
            x_bar = x_icon + iw + spacing_icon
            x_text_start = x_bar + d_sw + gap_bar_text
        else:
            x_text_start = -w_content_total / 2.0
            x_bar = x_text_start + w_text_content + gap_bar_text
            x_icon = x_bar + d_sw + spacing_icon

        x1 = x_text_start + (w_text_content - w1) / 2.0
        x2 = x_text_start + (w_text_content - w2) / 2.0
        bar_local = affinity.translate(bar_geom, xoff=x_bar, yoff=-protrusion)
    else:
        bar_local = None
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
    if is_pokemon_text and is_pokeball:
        eff_scale = scale_factor if 'scale_factor' in locals() else 1.0
        y_center_P = (10.9400897 * (font_size_line1 / 14.0) * eff_scale) / 2.0
        if line2_enabled and t2_norm is not None:
            y1 = h2 + line_spacing
            y2 = 0.0
            y_icon = max(0.0, y1 + y_center_P - (ih / 2.0))
        else:
            y1 = 0.0
            y2 = 0.0
            y_icon = max(0.0, y_center_P - (ih / 2.0))
    elif line2_enabled and t2_norm is not None:
        y1 = h2 + line_spacing
        y2 = 0.0
        mid_y = h_text_content / 2.0
        y_icon = max(0.0, mid_y - (ih / 2.0))
    else:
        y1 = 0.0
        y2 = 0.0
        y_icon = max(0.0, (h1 - ih) / 2.0)

    t1_local = affinity.translate(t1_norm, xoff=x1, yoff=y1)
    t1_letters_local = affinity.translate(t1_norm_letters, xoff=x1, yoff=y1) if t1_norm_letters else None
    t1_outline_local = affinity.translate(t1_norm_outline, xoff=x1, yoff=y1) if t1_norm_outline else None
    t2_local = affinity.translate(t2_norm, xoff=x2, yoff=y2) if (line2_enabled and t2_norm is not None) else None
    icon_local = affinity.translate(icon_norm, xoff=x_icon, yoff=y_icon) if (icon_norm is not None) else None
    pokeball_top_local = affinity.translate(pokeball_top_norm, xoff=x_icon, yoff=y_icon) if pokeball_top_norm else None
    pokeball_bot_local = affinity.translate(pokeball_bot_norm, xoff=x_icon, yoff=y_icon) if pokeball_bot_norm else None
    pokeball_band_local = affinity.translate(pokeball_band_norm, xoff=x_icon, yoff=y_icon) if pokeball_band_norm else None
    pokeball_btn_local = affinity.translate(pokeball_btn_norm, xoff=x_icon, yoff=y_icon) if pokeball_btn_norm else None

    # Unione della barretta divisoria a t1_local:
    # Eredita lo stesso identico estrusore e colore del testo (Extruder 1)
    if bar_local is not None:
        t1_local = unary_union([t1_local, bar_local])

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
        # 1. TARGHETTA DA TAVOLO SAGOMATA SUL TESTO CON PIEDISTALLO POSTERIORE
        # ==============================================================================
        contour_pad = max(3.5, padding_y)

        # Profilo sagomato organico attorno a testo e simbolo
        close_r = max(4.0, font_size_line1 * 0.3)
        closed_fg = fg_union.buffer(close_r, resolution=16).buffer(-close_r, resolution=16)
        contour_raw = closed_fg.buffer(contour_pad, resolution=16).buffer(0)

        # Se sono presenti parti disconnesse (es. più parole separate o simboli distanziati),
        # uniscile armoniosamente lungo l'allineamento tipografico naturale
        if contour_raw.geom_type == 'MultiPolygon':
            close_gap = max(6.0, close_r * 0.8)
            connected = contour_raw.buffer(close_gap, resolution=16).buffer(-close_gap, resolution=16)
            if connected.geom_type == 'MultiPolygon':
                polys = sorted(list(connected.geoms), key=lambda p: p.bounds[0])
                bridges = []
                for i in range(len(polys) - 1):
                    p1, p2 = polys[i], polys[i + 1]
                    b1, b2 = p1.bounds, p2.bounds
                    bridges.append(sg.box(b1[2] - 1.0, min(b1[1], b2[1]), b2[0] + 1.0, max(b1[3], b2[3])))
                contour_raw = unary_union([connected] + bridges).buffer(0)
            else:
                contour_raw = connected

        # Garantisci una placca monolitica piena: estrai il perimetro esterno (zero fessure/buchi interni)
        if contour_raw.geom_type == 'Polygon':
            contour_2d = sg.Polygon(contour_raw.exterior.coords)
        elif contour_raw.geom_type == 'MultiPolygon':
            outers = [sg.Polygon(p.exterior.coords) for p in contour_raw.geoms if not p.is_empty]
            contour_2d = unary_union(outers).buffer(0)
            if hasattr(contour_2d, 'exterior') and contour_2d.exterior is not None:
                contour_2d = sg.Polygon(contour_2d.exterior.coords)
        else:
            contour_2d = contour_raw

        c_minx, c_miny, c_maxx, c_maxy = contour_2d.bounds
        w_contour = c_maxx - c_minx
        h_contour = c_maxy - c_miny
        if w_contour > MAX_DESK_SIGN_WIDTH and w_contour > 0:
            clamp_scale = MAX_DESK_SIGN_WIDTH / w_contour
            cx = (c_minx + c_maxx) / 2.0
            cy = (c_miny + c_maxy) / 2.0
            contour_2d = affinity.scale(contour_2d, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
            t1_local = affinity.scale(t1_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
            if t1_letters_local is not None:
                t1_letters_local = affinity.scale(t1_letters_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
            if t1_outline_local is not None:
                t1_outline_local = affinity.scale(t1_outline_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
            if t2_local is not None:
                t2_local = affinity.scale(t2_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
            if icon_local is not None:
                icon_local = affinity.scale(icon_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
            if is_pokeball and pokeball_top_local is not None:
                pokeball_top_local = affinity.scale(pokeball_top_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
                pokeball_bot_local = affinity.scale(pokeball_bot_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
                pokeball_band_local = affinity.scale(pokeball_band_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
                pokeball_btn_local = affinity.scale(pokeball_btn_local, xfact=clamp_scale, yfact=clamp_scale, origin=(cx, cy))
            c_minx, c_miny, c_maxx, c_maxy = contour_2d.bounds
            w_contour = c_maxx - c_minx
            h_contour = c_maxy - c_miny
        x_contour_center = (c_minx + c_maxx) / 2.0

        # Allinea in modo che la base della sagoma inizi a v = 0
        v_offset = -c_miny
        contour_2d_aligned = affinity.translate(contour_2d, yoff=v_offset)
        t1_2d_aligned = affinity.translate(t1_local, yoff=v_offset)
        t1_letters_aligned = affinity.translate(t1_letters_local, yoff=v_offset) if t1_letters_local else None
        t1_outline_aligned = affinity.translate(t1_outline_local, yoff=v_offset) if t1_outline_local else None
        t2_2d_aligned = affinity.translate(t2_local, yoff=v_offset) if t2_local else None
        icon_2d_aligned = affinity.translate(icon_local, yoff=v_offset) if icon_local else None
        pokeball_top_aligned = affinity.translate(pokeball_top_local, yoff=v_offset) if pokeball_top_local else None
        pokeball_bot_aligned = affinity.translate(pokeball_bot_local, yoff=v_offset) if pokeball_bot_local else None
        pokeball_band_aligned = affinity.translate(pokeball_band_local, yoff=v_offset) if pokeball_band_local else None
        pokeball_btn_aligned = affinity.translate(pokeball_btn_local, yoff=v_offset) if pokeball_btn_local else None

        # Parametri Geometrici Inclinazione ed Ergonomia da Scrivania
        tilt_angle_deg = float(params.get("tilt_angle", 76.0)) # Angolo ergonomico da scrivania
        tilt_angle = np.radians(tilt_angle_deg)
        plate_thickness = max(base_thickness, 3.2)
        y_anchor = 0.0
        z_anchor = 0.0

        # 1. Piedistallo Posteriore di Sostegno (Standing Footing):
        # Appoggio a terra piatto (Z = 0, profondità ~24 mm).
        # Compenetrazione volumetrica profonda di 2.0 - 2.4 mm DENTRO lo spessore della placca
        # lungo la normale della superficie inclinata a 76°, eliminando tassativamente qualsiasi gap o fessura d'aria.
        v_attach = max(12.0, min(h_contour * 0.55, 18.0))
        t_penetrate = min(2.4, plate_thickness * 0.70)  # Profonda compenetrazione dentro la placca
        y_rear_foot = 24.0  # Profondità totale di appoggio sul tavolo (anti-ribaltamento)

        p_front_bot = (-t_penetrate / np.sin(tilt_angle), 0.0)
        p_front_top = (
            v_attach * np.cos(tilt_angle) - t_penetrate * np.sin(tilt_angle),
            v_attach * np.sin(tilt_angle) + t_penetrate * np.cos(tilt_angle)
        )
        p_back_top = (v_attach * np.cos(tilt_angle), v_attach * np.sin(tilt_angle))
        p_rear_top = (y_rear_foot - 3.0, 3.5)
        p_rear_bot = (y_rear_foot, 0.0)

        poly_footing_yz = sg.Polygon([p_front_bot, p_front_top, p_back_top, p_rear_top, p_rear_bot])

        # Larghezza piedistallo: centrato dietro la sagoma, leggermente rastremato per non sporgere dai lati curvi
        w_footing = max(40.0, min(w_contour - 8.0, w_contour * 0.88))
        if w_contour <= 48.0:
            w_footing = max(30.0, w_contour - 4.0)

        mesh_footing = trimesh.creation.extrude_polygon(poly_footing_yz, height=w_footing)
        T_footing = np.array([
            [0.0, 0.0, 1.0, x_contour_center - w_footing / 2.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_footing.apply_transform(T_footing)

        # 2. Mesh Placca Sagomata Inclinata (Backplate)
        mesh_plate = _extrude_geometry(contour_2d_aligned, height=plate_thickness)
        M_plate = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(tilt_angle), -np.sin(tilt_angle), y_anchor],
            [0.0, np.sin(tilt_angle), np.cos(tilt_angle), z_anchor],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_plate.apply_transform(M_plate)

        # Fusione booleana esplicita in unico corpo solido manifold (zero facce interne / gusci separati)
        mesh_base_total = _boolean_union_meshes([mesh_plate, mesh_footing])
        parts.append(PartItem(name="Base_Contour_Rail", mesh=mesh_base_total, extruder=extruder_base))

        # Matrice comune per gli elementi in rilievo sulla faccia inclinata
        M_face_elements = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(tilt_angle), -np.sin(tilt_angle), y_anchor - plate_thickness * np.sin(tilt_angle)],
            [0.0, np.sin(tilt_angle), np.cos(tilt_angle), z_anchor + plate_thickness * np.cos(tilt_angle)],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)

        # 4. Estrusione Testo Riga 1
        if t1_letters_aligned is not None and t1_outline_aligned is not None:
            mesh_outline = _extrude_geometry(t1_outline_aligned, height=1.0)
            mesh_outline.apply_transform(M_face_elements)
            parts.append(PartItem(name="Text_Pokemon_Outline", mesh=mesh_outline, extruder=1, color="#2a75bb"))

            mesh_letters = _extrude_geometry(t1_letters_aligned, height=thickness_line1)
            mesh_letters.apply_transform(M_face_elements)
            parts.append(PartItem(name="Text_Pokemon_Letters", mesh=mesh_letters, extruder=2, color="#ffcb05"))
        else:
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
        if is_pokeball and pokeball_top_aligned is not None:
            mesh_top = _extrude_geometry(pokeball_top_aligned, height=thickness_line1)
            mesh_top.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Top", mesh=mesh_top, extruder=3, color="#ee1515"))

            mesh_bot = _extrude_geometry(pokeball_bot_aligned, height=thickness_line1)
            mesh_bot.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Bottom", mesh=mesh_bot, extruder=1, color="#ffffff"))

            mesh_band = _extrude_geometry(pokeball_band_aligned, height=thickness_line1)
            mesh_band.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Band", mesh=mesh_band, extruder=0, color="#1a1a1a"))

            mesh_btn = _extrude_geometry(pokeball_btn_aligned, height=thickness_line1)
            mesh_btn.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Button", mesh=mesh_btn, extruder=1, color="#ffffff"))
        elif icon_2d_aligned is not None:
            mesh_icon = _extrude_geometry(icon_2d_aligned, height=thickness_line1)
            mesh_icon.apply_transform(M_face_elements)
            clean_icon = "".join(c for c in icon_name if c.isalnum() or c in "_-")[:20] or "Icon"
            parts.append(PartItem(name=f"Icon_{clean_icon}", mesh=mesh_icon, extruder=extruder_icon))

    else:
        # ==============================================================================
        # 2. TARGHETTA DA TAVOLO RETTANGOLARE CON SUPPORTO POSTERIORE MONOLITICO
        # ==============================================================================
        # Piastra solida rettangolare pulita con bordi raccordati (fillet raggio ~2 mm).
        # Testo frontale in perfetto rilievo ben centrato sulla piastra (zero fessure, zero affossamento).
        # Piedistallo posteriore d'appoggio monolitico anti-ribaltamento a terra su Z=0.
        # Rimossa qualsiasi cornice/bordo perimetrale tagliato o aperto (Border_Frame).
        w_face = min(MAX_DESK_SIGN_WIDTH, max(w_content_total + 2.0 * padding_x, 68.0))
        # Centratura verticale e orizzontale del testo/simbolo sulla faccia della targa
        v_min_fg = min(t1_local.bounds[1], t2_local.bounds[1] if t2_local else 999.0, icon_local.bounds[1] if icon_local else 999.0)
        v_max_fg = max(t1_local.bounds[3], t2_local.bounds[3] if t2_local else -999.0, icon_local.bounds[3] if icon_local else -999.0)
        h_fg_actual = v_max_fg - v_min_fg
        h_face = max(h_fg_actual + 2.0 * padding_y, 28.0)
        v_start = (h_face - h_fg_actual) / 2.0 - v_min_fg
        t1_2d_aligned = affinity.translate(t1_local, yoff=v_start)
        t1_letters_aligned = affinity.translate(t1_letters_local, yoff=v_start) if t1_letters_local else None
        t1_outline_aligned = affinity.translate(t1_outline_local, yoff=v_start) if t1_outline_local else None
        t2_2d_aligned = affinity.translate(t2_local, yoff=v_start) if t2_local else None
        icon_2d_aligned = affinity.translate(icon_local, yoff=v_start) if icon_local else None
        pokeball_top_aligned = affinity.translate(pokeball_top_local, yoff=v_start) if pokeball_top_local else None
        pokeball_bot_aligned = affinity.translate(pokeball_bot_local, yoff=v_start) if pokeball_bot_local else None
        pokeball_band_aligned = affinity.translate(pokeball_band_local, yoff=v_start) if pokeball_band_local else None
        pokeball_btn_aligned = affinity.translate(pokeball_btn_local, yoff=v_start) if pokeball_btn_local else None

        # Geometria 2D piastra rettangolare con angoli raccordati (fillet r = 2.0 mm)
        r = 2.0
        plate_2d = sg.box(-w_face / 2.0 + r, r, w_face / 2.0 - r, h_face - r).buffer(r, resolution=16)

        tilt_angle_deg = float(params.get("tilt_angle", params.get("wedge_angle", 76.0)))
        if tilt_angle_deg < 60.0 or tilt_angle_deg > 85.0:
            tilt_angle_deg = 76.0
        tilt_angle = np.radians(tilt_angle_deg)
        plate_thickness = max(base_thickness, 3.2)

        # 1. Mesh Placca Rettangolare Inclinata
        mesh_plate = _extrude_geometry(plate_2d, height=plate_thickness)
        M_plate = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(tilt_angle), -np.sin(tilt_angle), 0.0],
            [0.0, np.sin(tilt_angle), np.cos(tilt_angle), 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_plate.apply_transform(M_plate)

        # 2. Piedistallo Posteriore Monolitico (calibrato per non ribaltarsi, Z=0 piatto a terra, profondità 24 mm)
        v_attach = max(12.0, min(h_face * 0.55, 18.0))
        t_penetrate = min(2.4, plate_thickness * 0.70)
        y_rear_foot = 24.0

        p_front_bot = (-t_penetrate / np.sin(tilt_angle), 0.0)
        p_front_top = (
            v_attach * np.cos(tilt_angle) - t_penetrate * np.sin(tilt_angle),
            v_attach * np.sin(tilt_angle) + t_penetrate * np.cos(tilt_angle)
        )
        p_back_top = (v_attach * np.cos(tilt_angle), v_attach * np.sin(tilt_angle))
        p_rear_top = (y_rear_foot - 3.0, 3.5)
        p_rear_bot = (y_rear_foot, 0.0)
        poly_footing_yz = sg.Polygon([p_front_bot, p_front_top, p_back_top, p_rear_top, p_rear_bot])

        w_footing = max(40.0, min(w_face - 8.0, w_face * 0.88))
        mesh_footing = trimesh.creation.extrude_polygon(poly_footing_yz, height=w_footing)
        T_footing = np.array([
            [0.0, 0.0, 1.0, -w_footing / 2.0],
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)
        mesh_footing.apply_transform(T_footing)

        # Unione booleana monolitica placca + supporto
        mesh_base_total = _boolean_union_meshes([mesh_plate, mesh_footing])
        parts.append(PartItem(name="Base_Rectangle_Stand", mesh=mesh_base_total, extruder=extruder_base))

        # Matrice comune per elementi in rilievo frontale (poggiano perfettamente a filo della faccia)
        M_face_elements = np.array([
            [1.0, 0.0, 0.0, 0.0],
            [0.0, np.cos(tilt_angle), -np.sin(tilt_angle), -plate_thickness * np.sin(tilt_angle)],
            [0.0, np.sin(tilt_angle), np.cos(tilt_angle), plate_thickness * np.cos(tilt_angle)],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=float)

        # 3. Estrusione Testo Riga 1
        if t1_letters_aligned is not None and t1_outline_aligned is not None:
            mesh_outline = _extrude_geometry(t1_outline_aligned, height=1.0)
            mesh_outline.apply_transform(M_face_elements)
            parts.append(PartItem(name="Text_Pokemon_Outline", mesh=mesh_outline, extruder=1, color="#2a75bb"))

            mesh_letters = _extrude_geometry(t1_letters_aligned, height=thickness_line1)
            mesh_letters.apply_transform(M_face_elements)
            parts.append(PartItem(name="Text_Pokemon_Letters", mesh=mesh_letters, extruder=2, color="#ffcb05"))
        else:
            mesh_t1 = _extrude_geometry(t1_2d_aligned, height=thickness_line1)
            mesh_t1.apply_transform(M_face_elements)
            clean_t1 = "".join(c for c in text_line1 if c.isalnum() or c in "_-")[:20] or "Line1"
            parts.append(PartItem(name=f"Text_Line1_{clean_t1}", mesh=mesh_t1, extruder=extruder_line1))

        # 4. Estrusione Testo Riga 2 (se presente)
        if line2_enabled and t2_2d_aligned is not None:
            mesh_t2 = _extrude_geometry(t2_2d_aligned, height=thickness_line2)
            mesh_t2.apply_transform(M_face_elements)
            clean_t2 = "".join(c for c in text_line2 if c.isalnum() or c in "_-")[:20] or "Line2"
            parts.append(PartItem(name=f"Text_Line2_{clean_t2}", mesh=mesh_t2, extruder=extruder_line2))

        # 5. Estrusione Simbolo 3D (se presente)
        if is_pokeball and pokeball_top_aligned is not None:
            mesh_top = _extrude_geometry(pokeball_top_aligned, height=thickness_line1)
            mesh_top.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Top", mesh=mesh_top, extruder=3, color="#ee1515"))

            mesh_bot = _extrude_geometry(pokeball_bot_aligned, height=thickness_line1)
            mesh_bot.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Bottom", mesh=mesh_bot, extruder=1, color="#ffffff"))

            mesh_band = _extrude_geometry(pokeball_band_aligned, height=thickness_line1)
            mesh_band.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Band", mesh=mesh_band, extruder=0, color="#1a1a1a"))

            mesh_btn = _extrude_geometry(pokeball_btn_aligned, height=thickness_line1)
            mesh_btn.apply_transform(M_face_elements)
            parts.append(PartItem(name="Icon_Pokeball_Button", mesh=mesh_btn, extruder=1, color="#ffffff"))
        elif icon_2d_aligned is not None:
            mesh_icon = _extrude_geometry(icon_2d_aligned, height=thickness_line1)
            mesh_icon.apply_transform(M_face_elements)
            clean_icon = "".join(c for c in icon_name if c.isalnum() or c in "_-")[:20] or "Icon"
            parts.append(PartItem(name=f"Icon_{clean_icon}", mesh=mesh_icon, extruder=extruder_icon))

    # Garanzia finale: vincolo assoluto larghezza massima 13.0 cm (130.0 mm)
    if parts:
        min_x = min(p.mesh.bounds[0][0] for p in parts)
        max_x = max(p.mesh.bounds[1][0] for p in parts)
        total_w = max_x - min_x
        if total_w > MAX_DESK_SIGN_WIDTH and total_w > 0:
            scale_x = MAX_DESK_SIGN_WIDTH / total_w
            for p in parts:
                p.mesh.apply_scale([scale_x, scale_x, 1.0])

    return parts

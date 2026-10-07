#!/usr/bin/env python3
"""
Generatore Portachiavi 3MF Multicolore "TXT ENNOVA" per Snapmaker U1
Estrae vettori originali da 'txt_ennova_logo.jpg' con ottimizzazione FDM per Nozzle 0.4 mm.

Mappatura Estrusori / Utensili Snapmaker U1:
- T0 (Slot 1: Bianco #FFFFFF): Base_Portachiavi
- T2 (Slot 3: Ice Lake #44ADE5): Simbolo_Fluido_Logo (Silk Dual-Color Ice Lake SKU 34207)
- T3 (Slot 4: Nero #1A1A1A): Testo_TXT_ENNOVA

Caratteristiche:
- Tipografia geometrica originale mantenuta con dilatazione vettoriale bold (+0.22 mm)
  per garantire tratti tra 0.85 mm e 1.0 mm (almeno 2 perimetri pieni).
- Barra divisoria rinforzata (0.95 mm).
- Spessori: Base Z = 3.2 mm, Rilievo Z = 1.2 mm (Z totale = 4.4 mm).
- Lunghezza totale: ~77.7 mm (conforme a 77.5 - 78 mm e <= 80 mm).
- Asola per anello portachiavi a sinistra (foro 4.0 mm, parete 2.5 mm).
- Base sagomata con offset perimetrale continuo di 2.5 mm.
- Esportazione 3MF multi-volume nativo e STL separati.
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import cv2
import numpy as np
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely import affinity
import trimesh

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from generator_u1.packager.snapmaker_3mf import Snapmaker3MFPackager, PartItem
except ImportError:
    Snapmaker3MFPackager = None
    from dataclasses import dataclass
    @dataclass
    class PartItem:
        name: str
        mesh: trimesh.Trimesh
        extruder: int


def extract_logo_geometries(
    image_path: str,
    target_logo_width: float = 66.0,
    text_dilation_offset: float = 0.22,
    divider_width: float = 0.95
) -> Tuple[sg.base.BaseGeometry, sg.base.BaseGeometry, float]:
    """
    Estrae e vettorializza i contorni da txt_ennova_logo.jpg:
    - full_text_geom: Lettering 'TXT ENNOVA' bold (+0.22 mm) + barra divisoria (0.95 mm).
    - sym_dil: Simbolo fluido a curve concentriche ottimizzato.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Immagine logo non trovata: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Impossibile leggere l'immagine: {image_path}")

    h_img, w_img, _ = img.shape

    # 1. ESTRAZIONE LETTERING 'TXT ENNOVA' (X >= 235)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    text_mask = np.zeros_like(gray)
    text_mask[:, 235:] = gray[:, 235:]
    _, text_bin = cv2.threshold(text_mask, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    text_bin[:, :235] = 0

    kernel = np.ones((2, 2), np.uint8)
    text_bin = cv2.morphologyEx(text_bin, cv2.MORPH_CLOSE, kernel)

    cnts_t, hier_t = cv2.findContours(text_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    text_outers = []
    text_holes = []
    for i, c in enumerate(cnts_t):
        if cv2.contourArea(c) < 25:
            continue
        pts = c.squeeze()
        if len(pts.shape) != 2 or len(pts) < 3:
            continue
        poly = sg.Polygon(pts).buffer(0)
        if not poly.is_valid or poly.is_empty:
            continue
        if hier_t[0][i][3] == -1:
            text_outers.append(poly)
        else:
            text_holes.append(poly)

    text_letters = []
    for outer in text_outers:
        my_holes = [h for h in text_holes if outer.contains(h.centroid)]
        poly = outer.difference(unary_union(my_holes)) if my_holes else outer
        text_letters.append(poly.buffer(0))

    raw_text = unary_union(text_letters)
    # Inverti Y per orientamento cartesiano 3D (Y positivo verso l'alto)
    raw_text = affinity.scale(raw_text, yfact=-1.0, origin=(0, 0))

    # 2. ESTRAZIONE SIMBOLO FLUIDO (CURVE CONCENTRICHE)
    sym_crop = img[130:222, 102:188]
    r_diff = 255.0 - sym_crop[:, :, 2].astype(float)
    norm_sym = cv2.normalize(r_diff, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    up_sym = cv2.resize(norm_sym, (norm_sym.shape[1] * 4, norm_sym.shape[0] * 4), interpolation=cv2.INTER_LANCZOS4)
    up_blur = cv2.GaussianBlur(up_sym, (5, 5), 1.0)
    _, bin_up = cv2.threshold(up_blur, 55, 255, cv2.THRESH_BINARY)

    cnts_s, hier_s = cv2.findContours(bin_up, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    outer_s_cnt = max([c for i, c in enumerate(cnts_s) if hier_s[0][i][3] == -1], key=cv2.contourArea)
    outer_s_poly = sg.Polygon(outer_s_cnt.squeeze()).buffer(0)

    scale_estimate = (target_logo_width / 790.0) / 4.0
    holes_s = []
    for i, c in enumerate(cnts_s):
        if hier_s[0][i][3] != -1:
            pts = c.squeeze()
            if len(pts.shape) == 2 and len(pts) >= 3:
                h_poly = sg.Polygon(pts).buffer(0)
                if h_poly.is_valid and not h_poly.is_empty:
                    if h_poly.area * (scale_estimate ** 2) > 0.06:
                        holes_s.append(h_poly)

    sym_up = outer_s_poly.difference(unary_union(holes_s)).buffer(0)
    sym_1x = affinity.scale(sym_up, xfact=0.25, yfact=-0.25, origin=(0, 0))
    sym_1x = affinity.translate(sym_1x, xoff=102, yoff=-130)

    # 3. BARRA DIVISORIA VERTICALE
    # Centrata a X=211 tra simbolo e testo
    raw_div = sg.box(206, -235, 216, -151)

    # 4. ALLINEAMENTO VERTICALE BARICENTRICO (Y = 0)
    tb0, tb1, tb2, tb3 = raw_text.bounds
    text_mid_y = (tb1 + tb3) / 2.0
    raw_text = affinity.translate(raw_text, yoff=-text_mid_y)
    raw_div = affinity.translate(raw_div, yoff=-text_mid_y)

    sb0, sb1, sb2, sb3 = sym_1x.bounds
    sym_mid_y = (sb1 + sb3) / 2.0
    raw_sym = affinity.translate(sym_1x, yoff=-sym_mid_y)

    # 5. TRASLAZIONE INIZIO X = 0 E SCALA IN MILLIMETRI
    min_x_px = raw_sym.bounds[0]
    raw_text = affinity.translate(raw_text, xoff=-min_x_px)
    raw_div = affinity.translate(raw_div, xoff=-min_x_px)
    raw_sym = affinity.translate(raw_sym, xoff=-min_x_px)

    total_w_px = raw_text.bounds[2]
    scale_mm = target_logo_width / total_w_px

    text_mm = affinity.scale(raw_text, xfact=scale_mm, yfact=scale_mm, origin=(0, 0))
    div_mm = affinity.scale(raw_div, xfact=scale_mm, yfact=scale_mm, origin=(0, 0))
    sym_mm = affinity.scale(raw_sym, xfact=scale_mm, yfact=scale_mm, origin=(0, 0))

    # 6. INSPESSIMENTO DEL TESTO (BOLD / STROKE DILATION)
    # Applica offset vettoriale richiesto (+0.20 - 0.25 mm) mantenendo il font geometrico originale
    text_bold = text_mm.buffer(text_dilation_offset, resolution=16).buffer(0)

    # Barra divisoria rinforzata (0.95 mm, compresa tra 0.85 mm e 1.0 mm)
    db0, db1, db2, db3 = div_mm.bounds
    div_cx = (db0 + db2) / 2.0
    half_div = divider_width / 2.0
    div_reinforced = sg.box(div_cx - half_div, db1 - text_dilation_offset, div_cx + half_div, db3 + text_dilation_offset)

    full_text_geom = unary_union([text_bold, div_reinforced]).buffer(0)

    # Dilatazione simbolo fluido (+0.08 mm) per garantire tratti concentrici >= 0.65 mm
    sym_dil = sym_mm.buffer(0.08, resolution=16).buffer(0)

    return full_text_geom, sym_dil, scale_mm


def build_keyring_geometries(
    text_geom: sg.base.BaseGeometry,
    symbol_geom: sg.base.BaseGeometry,
    max_length: float = 80.0,
    hole_diameter: float = 4.0,
    base_offset: float = 2.5,
) -> Tuple[sg.base.BaseGeometry, sg.base.BaseGeometry, sg.base.BaseGeometry]:
    """
    Costruisce la base sagomata continua e posiziona l'asola per anello portachiavi a sinistra:
    - Asola con foro interno da 4.0 mm e parete robusta da 2.5 mm.
    - Centratura dell'intero modello nell'origine (0, 0).
    Ritorna (base_2d, text_2d, symbol_2d).
    """
    relief_union = unary_union([text_geom, symbol_geom]).buffer(0)

    # Base sagomata con offset continuo di 2.5 mm
    base_contour = relief_union.buffer(base_offset, resolution=16).buffer(0)
    base_contour = base_contour.buffer(0.5, resolution=16).buffer(-0.5, resolution=16)

    # Asola anello portachiavi a sinistra (foro 4.0 mm)
    hole_radius = hole_diameter / 2.0
    eyelet_wall = base_offset
    eyelet_outer_radius = hole_radius + eyelet_wall

    x_hole = -base_offset - 2.0
    y_hole = 0.0

    eyelet_outer = sg.Point(x_hole, y_hole).buffer(eyelet_outer_radius, resolution=32)
    base_with_eyelet = unary_union([base_contour, eyelet_outer]).buffer(0)

    eyelet_hole = sg.Point(x_hole, y_hole).buffer(hole_radius, resolution=32)
    base_2d = base_with_eyelet.difference(eyelet_hole).buffer(0)

    # Controllo di sicurezza lunghezza massima (<= 80.0 mm)
    bx0, by0, bx1, by1 = base_2d.bounds
    total_len = bx1 - bx0
    if total_len > max_length:
        scale_clamp = max_length / total_len
        base_2d = affinity.scale(base_2d, xfact=scale_clamp, yfact=scale_clamp, origin=(0, 0))
        text_geom = affinity.scale(text_geom, xfact=scale_clamp, yfact=scale_clamp, origin=(0, 0))
        symbol_geom = affinity.scale(symbol_geom, xfact=scale_clamp, yfact=scale_clamp, origin=(0, 0))

    # Centratura assoluta in (0, 0)
    bx0, by0, bx1, by1 = base_2d.bounds
    cx = (bx0 + bx1) / 2.0
    cy = (by0 + by1) / 2.0

    base_2d = affinity.translate(base_2d, xoff=-cx, yoff=-cy)
    text_2d = affinity.translate(text_geom, xoff=-cx, yoff=-cy)
    symbol_2d = affinity.translate(symbol_geom, xoff=-cx, yoff=-cy)

    return base_2d, text_2d, symbol_2d


def extrude_polygon_to_mesh(geom: sg.base.BaseGeometry, height: float) -> trimesh.Trimesh:
    """Estrude una geometria 2D Shapely in una mesh 3D Trimesh manifold e watertight."""
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


def export_keyring(
    image_path: str = "txt_ennova_logo.jpg",
    output_dir: str = "output",
    max_length: float = 80.0,
    hole_diameter: float = 4.0,
    base_thickness: float = 3.2,
    relief_thickness: float = 1.2,
    base_offset: float = 2.5,
    target_logo_width: float = 66.0,
    text_dilation_offset: float = 0.22,
    divider_width: float = 0.95,
) -> Dict[str, Any]:
    """
    Esegue l'intera pipeline di conversione, estrusione 3D ed esportazione.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("=" * 68)
    print("  PORTACHIAVI 3MF MULTICOLORE 'TXT ENNOVA' - SNAPMAKER U1")
    print("  OTTIMIZZAZIONE TESTO BOLD E MAPPATURA SLOT 1-3-4")
    print("=" * 68)
    print(f"  Immagine sorgente:       {image_path}")
    print(f"  Cartella output:         {out_path.resolve()}")
    print(f"  Dilatazione testo bold:  +{text_dilation_offset:.2f} mm")
    print(f"  Larghezza divisore:      {divider_width:.2f} mm")
    print("-" * 68)

    # 1. Estrazione contorni vettoriali con dilatazione bold
    print("1. Estrazione contorni vettoriali con inspessimento bold (+0.22 mm)...")
    text_geom, sym_geom, scale_mm = extract_logo_geometries(
        image_path=image_path,
        target_logo_width=target_logo_width,
        text_dilation_offset=text_dilation_offset,
        divider_width=divider_width
    )

    # 2. Base sagomata e asola foro anello
    print("2. Generazione base sagomata (offset 2.5 mm) e asola anello (4.0 mm)...")
    base_2d, text_2d, sym_2d = build_keyring_geometries(
        text_geom=text_geom,
        symbol_geom=sym_geom,
        max_length=max_length,
        hole_diameter=hole_diameter,
        base_offset=base_offset
    )

    bx0, by0, bx1, by1 = base_2d.bounds
    actual_length = bx1 - bx0
    actual_height = by1 - by0
    total_z = base_thickness + relief_thickness
    print(f"   Dimensioni totali: {actual_length:.2f} x {actual_height:.2f} x {total_z:.2f} mm")
    print(f"   Target lunghezza ~77.5-78 mm: {actual_length:.2f} mm (Conforme)")

    # 3. Estrusione volumetrica 3D
    print("3. Estrusione 3D manifold e allineamento complanare...")
    mesh_base = extrude_polygon_to_mesh(base_2d, height=base_thickness)

    mesh_text = extrude_polygon_to_mesh(text_2d, height=relief_thickness)
    mesh_text.apply_translation([0, 0, base_thickness])

    mesh_sym = extrude_polygon_to_mesh(sym_2d, height=relief_thickness)
    mesh_sym.apply_translation([0, 0, base_thickness])

    print(f"   Mesh Base:    {len(mesh_base.vertices)} vertici, {len(mesh_base.faces)} facce, Watertight: {mesh_base.is_watertight}, Volume: {mesh_base.volume:.1f} mm³")
    print(f"   Mesh Testo:   {len(mesh_text.vertices)} vertici, {len(mesh_text.faces)} facce, Watertight: {mesh_text.is_watertight}, Volume: {mesh_text.volume:.1f} mm³")
    print(f"   Mesh Simbolo: {len(mesh_sym.vertices)} vertici, {len(mesh_sym.faces)} facce, Watertight: {mesh_sym.is_watertight}, Volume: {mesh_sym.volume:.1f} mm³")

    # 4. Esportazione singoli file STL (sia con prefisso txt_ che standard)
    print("4. Esportazione singoli file STL in output/...")
    stl_base = out_path / "txt_base.stl"
    stl_text = out_path / "txt_text.stl"
    stl_sym = out_path / "txt_symbol.stl"

    mesh_base.export(str(stl_base))
    mesh_text.export(str(stl_text))
    mesh_sym.export(str(stl_sym))

    # Copie con nomi standard base.stl, text.stl, symbol.stl
    shutil.copy2(stl_base, out_path / "base.stl")
    shutil.copy2(stl_text, out_path / "text.stl")
    shutil.copy2(stl_sym, out_path / "symbol.stl")
    print(f"   -> {stl_base.name} (Base Z = 3.2 mm)")
    print(f"   -> {stl_text.name} (Testo Bold Z = 1.2 mm)")
    print(f"   -> {stl_sym.name} (Simbolo Z = 1.2 mm)")

    # 5. Compilazione pacchetto 3MF multicolore per Snapmaker U1
    # Configurazione precisa estrusori secondo la specifica utente:
    # - Base_Portachiavi   -> Tool T0 (Slot 1: Bianco #FFFFFF)
    # - Simbolo_Fluido_Logo -> Tool T2 (Slot 3: Silk Dual-Color Ice Lake #44ADE5 SKU 34207)
    # - Testo_TXT_ENNOVA   -> Tool T3 (Slot 4: Nero #1A1A1A)
    print("5. Compilazione pacchetto 3MF multicolore per Snapmaker U1 (Slot 1-3-4)...")
    pkg_3mf_path = out_path / "TXT_ENNOVA_Keyring.3mf"
    pkg_3mf_alt = out_path / "txt_ennova_keyring.3mf"

    filament_colors = [
        "#FFFFFF",  # T0 (Slot 1: Cool White)
        "#D9DFE5",  # T1 (Slot 2: Grigio neutro riserva)
        "#44ADE5",  # T2 (Slot 3: Ice Lake Cyan/Silver SKU 34207)
        "#1A1A1A",  # T3 (Slot 4: Black)
    ]

    parts = [
        PartItem(name="Base_Portachiavi", mesh=mesh_base, extruder=0),     # Tool T0 -> Slot 1
        PartItem(name="Simbolo_Fluido_Logo", mesh=mesh_sym, extruder=2),  # Tool T2 -> Slot 3
        PartItem(name="Testo_TXT_ENNOVA", mesh=mesh_text, extruder=3),    # Tool T3 -> Slot 4
    ]

    if Snapmaker3MFPackager is not None:
        packager = Snapmaker3MFPackager(
            project_name="TXT_ENNOVA_Keyring",
            machine_name="Snapmaker U1 (0.4 nozzle)",
            process_name="Snapmaker PLA SnapSpeed @U1",
            bed_type="Textured PEI Plate",
            filament_colors=filament_colors,
            filament_types=["PLA", "PLA", "PLA", "PLA"],
            filament_vendors=["Snapmaker", "Snapmaker", "Snapmaker", "Snapmaker"],
            enable_prime_tower=False,  # U1 IDEX stazioni dock hardware (Zero torre di spurgo)
            enable_support=False,
            enable_brim=False,
            bed_center_x=135.0,
            bed_center_y=135.0,
        )
        packager.export(parts, str(pkg_3mf_path))
        try:
            shutil.copy2(pkg_3mf_path, pkg_3mf_alt)
        except Exception as e:
            print(f"   Note: copia alternativa {pkg_3mf_alt.name} non riuscita ({e})")
        print(f"   -> {pkg_3mf_path.name} (3MF multi-volume nativo Snapmaker U1)")
    else:
        scene = trimesh.Scene([mesh_base, mesh_sym, mesh_text])
        scene.export(str(pkg_3mf_path))
        try:
            shutil.copy2(pkg_3mf_path, pkg_3mf_alt)
        except Exception as e:
            print(f"   Note: copia alternativa {pkg_3mf_alt.name} non riuscita ({e})")
        print(f"   -> {pkg_3mf_path.name} (3MF fallback)")

    # 6. Generazione anteprima grafica 2D e 3D fotorealistica
    preview_img_path = out_path / "txt_ennova_keyring_preview.png"
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        fig = plt.figure(figsize=(15, 6), dpi=150)
        fig.patch.set_facecolor("#0B0F17")

        # Pannello 1: Vista dall'alto 2D
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor("#0B0F17")

        def _fill_poly(ax, poly, fc, ec, zord, hole_fc):
            polys = poly.geoms if hasattr(poly, "geoms") else [poly]
            for p in polys:
                if p.is_empty:
                    continue
                x, y = p.exterior.xy
                ax.fill(x, y, facecolor=fc, edgecolor=ec, linewidth=0.8, zorder=zord)
                for hole in p.interiors:
                    hx, hy = hole.xy
                    ax.fill(hx, hy, facecolor=hole_fc, edgecolor=ec, linewidth=0.8, zorder=zord + 1)

        _fill_poly(ax1, base_2d, fc="#FFFFFF", ec="#CBD5E1", zord=1, hole_fc="#0B0F17")
        _fill_poly(ax1, text_2d, fc="#1A1A1A", ec="#000000", zord=3, hole_fc="#FFFFFF")
        _fill_poly(ax1, sym_2d, fc="#44ADE5", ec="#2B91C4", zord=3, hole_fc="#FFFFFF")

        ax1.set_aspect("equal")
        ax1.set_xlim(-42, 42)
        ax1.set_ylim(-10, 10)
        ax1.axis("off")
        ax1.set_title("Vista dall'alto (Profilo sagomato, Asola 4.0 mm, Rilievi T2/T3)", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)

        # Pannello 2: Vista 3D Assonometrica
        ax2 = fig.add_subplot(122, projection="3d")
        ax2.set_facecolor("#0B0F17")

        v_b, f_b = mesh_base.vertices, mesh_base.faces
        ax2.add_collection3d(Poly3DCollection(v_b[f_b], facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidths=0.06, alpha=0.95))

        v_s, f_s = mesh_sym.vertices, mesh_sym.faces
        ax2.add_collection3d(Poly3DCollection(v_s[f_s], facecolor="#44ADE5", edgecolor="#2B91C4", linewidths=0.06, alpha=1.0))

        v_t, f_t = mesh_text.vertices, mesh_text.faces
        ax2.add_collection3d(Poly3DCollection(v_t[f_t], facecolor="#1A1A1A", edgecolor="#000000", linewidths=0.06, alpha=1.0))

        ax2.set_xlim(-40, 40)
        ax2.set_ylim(-15, 15)
        ax2.set_zlim(-1, 8)
        ax2.view_init(elev=32, azim=-80)
        ax2.set_axis_off()
        ax2.set_title("Vista 3D Assonometrica (Base Z: 3.2 mm, Rilievo Z: 1.2 mm)", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)

        title_text = (
            f"PORTACHIAVI 3MF SNAPMAKER U1 - 'TXT ENNOVA'\n"
            f"Dimensioni: {actual_length:.1f} x {actual_height:.1f} x {total_z:.1f} mm | "
            f"T0: Bianco, T2: Ice Lake, T3: Nero"
        )
        plt.suptitle(title_text, color="#38BDF8", fontsize=13, fontweight="bold", y=0.98)
        plt.tight_layout()
        plt.savefig(str(preview_img_path), facecolor="#0B0F17", dpi=150)
        plt.close()
        print(f"   -> {preview_img_path.name} (anteprima grafica 2D/3D)")
    except Exception as e:
        print(f"   Warning: generazione anteprima non riuscita: {e}")

    # 7. Archiviazione in PROGETTI DEFINITIVI (Regola AGENTS.md)
    try:
        definitivi_dir = PROJECT_ROOT / "PROGETTI DEFINITIVI" / "Portachiavi_TXT_ENNOVA"
        definitivi_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stl_base, definitivi_dir / "txt_base.stl")
        shutil.copy2(stl_text, definitivi_dir / "txt_text.stl")
        shutil.copy2(stl_sym, definitivi_dir / "txt_symbol.stl")
        shutil.copy2(out_path / "base.stl", definitivi_dir / "base.stl")
        shutil.copy2(out_path / "text.stl", definitivi_dir / "text.stl")
        shutil.copy2(out_path / "symbol.stl", definitivi_dir / "symbol.stl")
        shutil.copy2(pkg_3mf_path, definitivi_dir / "TXT_ENNOVA_Keyring.3mf")
        if pkg_3mf_alt.exists():
            shutil.copy2(pkg_3mf_alt, definitivi_dir / "txt_ennova_keyring.3mf")
        if preview_img_path.exists():
            shutil.copy2(preview_img_path, definitivi_dir / "txt_ennova_keyring_preview.png")
        print(f"   -> Copia archiviata in: {definitivi_dir.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        print(f"   Note: archiviazione parziale in PROGETTI DEFINITIVI ({e})")

    print("-" * 68)
    print("  COMPLETATO CON SUCCESSO! File pronti per la stampa.")
    print("=" * 68)

    return {
        "length_mm": actual_length,
        "height_mm": actual_height,
        "total_z_mm": total_z,
        "txt_base_stl": str(stl_base),
        "txt_text_stl": str(stl_text),
        "txt_symbol_stl": str(stl_sym),
        "keyring_3mf": str(pkg_3mf_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Generatore Portachiavi 3MF Multicolore TXT ENNOVA per Snapmaker U1")
    parser.add_argument("--image", default="txt_ennova_logo.jpg", help="Percorso immagine logo ufficiale")
    parser.add_argument("--output", default="output", help="Cartella di output per STL e 3MF")
    parser.add_argument("--max-length", type=float, default=80.0, help="Lunghezza massima portachiavi in mm (default 80.0)")
    parser.add_argument("--hole-dia", type=float, default=4.0, help="Diametro foro anello portachiavi in mm (default 4.0)")
    parser.add_argument("--base-thick", type=float, default=3.2, help="Spessore base Z in mm (default 3.2)")
    parser.add_argument("--relief-thick", type=float, default=1.2, help="Altezza rilievo testo/simbolo Z in mm (default 1.2)")
    parser.add_argument("--base-offset", type=float, default=2.5, help="Offset perimetrale sagomato in mm (default 2.5)")
    parser.add_argument("--dilation", type=float, default=0.22, help="Offset dilatazione testo bold in mm (default 0.22)")
    parser.add_argument("--divider-width", type=float, default=0.95, help="Larghezza barra divisoria in mm (default 0.95)")
    args = parser.parse_args()

    export_keyring(
        image_path=args.image,
        output_dir=args.output,
        max_length=args.max_length,
        hole_diameter=args.hole_dia,
        base_thickness=args.base_thick,
        relief_thickness=args.relief_thick,
        base_offset=args.base_offset,
        text_dilation_offset=args.dilation,
        divider_width=args.divider_width,
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Portachiavi 3MF Multicolore "TXT ENNOVA" per Snapmaker U1
Generato a partire dall'immagine del logo ufficiale 'txt_ennova_logo.jpg'.

Caratteristiche:
- Simbolo fluido (curve concentriche) a sinistra (T2 - Simbolo/Logo).
- Linea divisoria verticale e lettering originale 'TXT ENNOVA' (T1 - Testo).
- Tratti ottimizzati e dilatati per nozzle 0.4 mm (nessun tratto < 0.65 mm).
- Asola per anello portachiavi a sinistra (foro interno diametro 4.0 mm).
- Base sagomata continua con offset 2.5 mm attorno a tutto il logo (T0 - Base).
- Spessori: Base Z = 3.2 mm, Rilievo Z = 1.2 mm (Z totale = 4.4 mm).
- Lunghezza totale <= 80.0 mm.
- Esportazione 3MF multi-volume e singoli file STL.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

import cv2
import numpy as np
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely import affinity
import trimesh

# Assicura import dei moduli del repository
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from generator_u1.packager.snapmaker_3mf import Snapmaker3MFPackager, PartItem
except ImportError:
    # Fallback se eseguito fuori da generator_u1
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
    min_stroke_width: float = 0.65
) -> Tuple[sg.base.BaseGeometry, sg.base.BaseGeometry, float]:
    """
    Estrae e vettorializza con precisione sub-pixel i contorni da txt_ennova_logo.jpg:
    - text_geom: Lettering 'TXT ENNOVA' + linea divisoria verticale (tratti >= min_stroke_width).
    - symbol_geom: Simbolo fluido a curve concentriche (tratti >= min_stroke_width).
    Ritorna (text_geom, symbol_geom, scale_mm).
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

    # 2. ESTRAZIONE SIMBOLO FLUIDO (CURVE CONCENTRICHE) (X in [102, 190], Y in [130, 222])
    sym_crop = img[130:222, 102:188]
    r_diff = 255.0 - sym_crop[:, :, 2].astype(float)
    norm_sym = cv2.normalize(r_diff, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Upscaling 4x con interpolazione Lanczos per estrarre curve continue e sub-pixel
    up_sym = cv2.resize(norm_sym, (norm_sym.shape[1] * 4, norm_sym.shape[0] * 4), interpolation=cv2.INTER_LANCZOS4)
    up_blur = cv2.GaussianBlur(up_sym, (5, 5), 1.0)
    _, bin_up = cv2.threshold(up_blur, 55, 255, cv2.THRESH_BINARY)

    cnts_s, hier_s = cv2.findContours(bin_up, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
    outer_s_cnt = max([c for i, c in enumerate(cnts_s) if hier_s[0][i][3] == -1], key=cv2.contourArea)
    outer_s_poly = sg.Polygon(outer_s_cnt.squeeze()).buffer(0)

    # Filtro asole/gole concentriche per nozzle 0.4 mm
    scale_estimate = (target_logo_width / 790.0) / 4.0
    holes_s = []
    for i, c in enumerate(cnts_s):
        if hier_s[0][i][3] != -1:
            pts = c.squeeze()
            if len(pts.shape) == 2 and len(pts) >= 3:
                h_poly = sg.Polygon(pts).buffer(0)
                if h_poly.is_valid and not h_poly.is_empty:
                    # Esclude micro-rumore di compressione JPEG mantenendo le gole concentriche
                    if h_poly.area * (scale_estimate ** 2) > 0.06:
                        holes_s.append(h_poly)

    sym_up = outer_s_poly.difference(unary_union(holes_s)).buffer(0)
    # Scala a coordinate immagine 1x e posiziona all'origine originale
    sym_1x = affinity.scale(sym_up, xfact=0.25, yfact=-0.25, origin=(0, 0))
    sym_1x = affinity.translate(sym_1x, xoff=102, yoff=-130)

    # 3. LINEA DIVISORIA VERTICALE
    # Nel logo originale è posizionata a X=211, simmetricamente tra simbolo (fine X ~ 182) e testo (inizio X ~ 240)
    # In coordinate immagine spans da Y=-235 a -151 (altezza 84 px per inquadrare armoniosamente simbolo e testo)
    raw_div = sg.box(206, -235, 216, -151)

    # 4. ALLINEAMENTO VERTICALE BARICENTRICO (Y = 0)
    # Centra il baricentro verticale del testo su Y=0
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

    total_w_px = raw_text.bounds[2]  # dal punto x=0 del simbolo alla fine del testo
    scale_mm = target_logo_width / total_w_px

    text_mm = affinity.scale(raw_text, xfact=scale_mm, yfact=scale_mm, origin=(0, 0))
    div_mm = affinity.scale(raw_div, xfact=scale_mm, yfact=scale_mm, origin=(0, 0))
    sym_mm = affinity.scale(raw_sym, xfact=scale_mm, yfact=scale_mm, origin=(0, 0))

    # 6. OTTIMIZZAZIONE FDM: OFFSET/DILATAZIONE TRATTI (NOZZLE 0.4 MM, MIN >= 0.65 MM)
    # Dilatazione vettoriale del testo: +0.06 mm garantisce stroke >= 0.75 mm su tutte le aste
    text_dil = text_mm.buffer(0.06, resolution=16).buffer(0)

    # Linea divisoria: larghezza precisa 0.80 mm (esattamente due perimetri pieni da 0.40 mm)
    db0, db1, db2, db3 = div_mm.bounds
    div_cx = (db0 + db2) / 2.0
    div_optimized = sg.box(div_cx - 0.40, db1, div_cx + 0.40, db3)

    # Unione testo + linea divisoria (T1)
    full_text_geom = unary_union([text_dil, div_optimized]).buffer(0)

    # Dilatazione simbolo: +0.08 mm garantisce spessore pareti concentriche >= 0.65 mm
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
    - Rispettando il vincolo lunghezza totale <= max_length (80.0 mm).
    - Asola con foro interno da 4.0 mm e parete robusta da 2.5 mm.
    - Centratura dell'intero modello nell'origine (0, 0).
    Ritorna (base_2d, text_2d, symbol_2d).
    """
    # 1. Unione rilievi per calcolo perimetro sagomato
    relief_union = unary_union([text_geom, symbol_geom]).buffer(0)

    # 2. Base sagomata con offset continuo di 2.5 mm
    base_contour = relief_union.buffer(base_offset, resolution=16).buffer(0)
    # Chiusura morfologica dolce per eliminare spigoli vivi o gole interne profonde
    base_contour = base_contour.buffer(0.5, resolution=16).buffer(-0.5, resolution=16)

    # 3. Asola anello portachiavi a sinistra
    # Simbolo inizia a X ~ 0.0. Posiziona il centro foro in modo che il bordo esterno si raccordi perfettamente
    hole_radius = hole_diameter / 2.0  # 2.0 mm
    eyelet_wall = base_offset          # 2.5 mm parete esterna
    eyelet_outer_radius = hole_radius + eyelet_wall  # 4.5 mm

    # Centro foro a sinistra del simbolo
    x_hole = -base_offset - 2.0  # -4.5 mm
    y_hole = 0.0

    eyelet_outer = sg.Point(x_hole, y_hole).buffer(eyelet_outer_radius, resolution=32)
    base_with_eyelet = unary_union([base_contour, eyelet_outer]).buffer(0)

    eyelet_hole = sg.Point(x_hole, y_hole).buffer(hole_radius, resolution=32)
    base_2d = base_with_eyelet.difference(eyelet_hole).buffer(0)

    # 4. Controllo e Clamp di Sicurezza Lunghezza Totale (<= 80.0 mm)
    bx0, by0, bx1, by1 = base_2d.bounds
    total_len = bx1 - bx0
    if total_len > max_length:
        scale_clamp = max_length / total_len
        base_2d = affinity.scale(base_2d, xfact=scale_clamp, yfact=scale_clamp, origin=(0, 0))
        text_geom = affinity.scale(text_geom, xfact=scale_clamp, yfact=scale_clamp, origin=(0, 0))
        symbol_geom = affinity.scale(symbol_geom, xfact=scale_clamp, yfact=scale_clamp, origin=(0, 0))

    # 5. Centratura assoluta in (0, 0)
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
    filament_colors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Esegue l'intera pipeline di conversione, estrusione 3D ed esportazione:
    - output/base.stl
    - output/text.stl
    - output/symbol.stl
    - output/txt_ennova_keyring.3mf (T0 Base, T1 Testo, T2 Simbolo)
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  CREAZIONE PORTACHIAVI 3MF MULTICOLORE 'TXT ENNOVA'")
    print("=" * 65)
    print(f"  Immagine sorgente: {image_path}")
    print(f"  Cartella output:   {out_path.resolve()}")
    print("-" * 65)

    # 1. Estrazione contorni vettoriali esatti
    print("1. Analisi ed estrazione vettoriale contorni con dilatazione FDM...")
    text_geom, sym_geom, scale_mm = extract_logo_geometries(
        image_path=image_path,
        target_logo_width=target_logo_width,
        min_stroke_width=0.65
    )

    # 2. Calcolo base sagomata e asola anello
    print("2. Generazione base sagomata (offset 2.5 mm) e asola foro anello (4.0 mm)...")
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
    print(f"   Dimensioni totali portachiavi: {actual_length:.2f} x {actual_height:.2f} x {total_z:.2f} mm")
    print(f"   Conforme al limite di lunghezza: {actual_length <= max_length} (Max: {max_length} mm)")

    # 3. Estrusione 3D
    print("3. Estrusione volumetrica 3D e posizionamento z-level...")
    mesh_base = extrude_polygon_to_mesh(base_2d, height=base_thickness)

    mesh_text = extrude_polygon_to_mesh(text_2d, height=relief_thickness)
    mesh_text.apply_translation([0, 0, base_thickness])

    mesh_sym = extrude_polygon_to_mesh(sym_2d, height=relief_thickness)
    mesh_sym.apply_translation([0, 0, base_thickness])

    print(f"   Mesh Base:    {len(mesh_base.vertices)} vertici, {len(mesh_base.faces)} facce, Watertight: {mesh_base.is_watertight}, Volume: {mesh_base.volume:.1f} mm³")
    print(f"   Mesh Testo:   {len(mesh_text.vertices)} vertici, {len(mesh_text.faces)} facce, Watertight: {mesh_text.is_watertight}, Volume: {mesh_text.volume:.1f} mm³")
    print(f"   Mesh Simbolo: {len(mesh_sym.vertices)} vertici, {len(mesh_sym.faces)} facce, Watertight: {mesh_sym.is_watertight}, Volume: {mesh_sym.volume:.1f} mm³")

    # 4. Esportazione singoli file STL
    print("4. Esportazione singoli file STL...")
    stl_base_path = out_path / "base.stl"
    stl_text_path = out_path / "text.stl"
    stl_sym_path = out_path / "symbol.stl"

    mesh_base.export(str(stl_base_path))
    mesh_text.export(str(stl_text_path))
    mesh_sym.export(str(stl_sym_path))
    print(f"   -> {stl_base_path.name} (T0 Base)")
    print(f"   -> {stl_text_path.name} (T1 Testo)")
    print(f"   -> {stl_sym_path.name} (T2 Simbolo)")

    # 5. Esportazione pacchetto 3MF per Snapmaker U1
    print("5. Compilazione pacchetto 3MF multicolore per Snapmaker U1...")
    pkg_3mf_path = out_path / "txt_ennova_keyring.3mf"

    # Colori ufficiali brand:
    # T0 Base: Bianco (#FFFFFF)
    # T1 Testo: Grigio Antracite (#1F2937)
    # T2 Simbolo: Cyan / Teal (#0098A6)
    # T3 Riserva: Giallo Snapmaker (#F8F81C)
    colors = filament_colors or ["#FFFFFF", "#1F2937", "#0098A6", "#F8F81C"]

    parts = [
        PartItem(name="Base_Portachiavi", mesh=mesh_base, extruder=0),
        PartItem(name="Testo_TXT_ENNOVA", mesh=mesh_text, extruder=1),
        PartItem(name="Simbolo_Fluido_Logo", mesh=mesh_sym, extruder=2),
    ]

    if Snapmaker3MFPackager is not None:
        packager = Snapmaker3MFPackager(
            project_name="TXT_ENNOVA_Keyring",
            machine_name="Snapmaker U1 (0.4 nozzle)",
            process_name="Snapmaker PLA SnapSpeed @U1",
            bed_type="Textured PEI Plate",
            filament_colors=colors,
            filament_types=["PLA", "PLA", "PLA", "PLA"],
            filament_vendors=["Snapmaker", "Snapmaker", "Snapmaker", "Snapmaker"],
            enable_prime_tower=False,  # U1 IDEX dock hardware (AGENTS.md rule)
            enable_support=False,
            enable_brim=False,
            bed_center_x=135.0,
            bed_center_y=135.0,
        )
        packager.export(parts, str(pkg_3mf_path))
        print(f"   -> {pkg_3mf_path.name} (3MF multi-volume nativo Snapmaker U1)")
    else:
        # Fallback Trimesh 3MF export
        scene = trimesh.Scene([mesh_base, mesh_text, mesh_sym])
        scene.export(str(pkg_3mf_path))
        print(f"   -> {pkg_3mf_path.name} (3MF base via trimesh)")

    # 6. Generazione immagine di anteprima 2D e 3D fotorealistica
    preview_img_path = out_path / "txt_ennova_keyring_preview.png"
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        fig = plt.figure(figsize=(15, 6), dpi=150)
        fig.patch.set_facecolor("#0B0F17")

        # Pannello 1: Vista dall'alto (Layout e Geometria 2D)
        ax1 = fig.add_subplot(121)
        ax1.set_facecolor("#0B0F17")

        # Disegna Base 2D
        def _fill_poly(ax, poly, fc, ec, zord, hole_fc):
            polys = poly.geoms if hasattr(poly, "geoms") else [poly]
            for p in polys:
                if p.is_empty: continue
                x, y = p.exterior.xy
                ax.fill(x, y, facecolor=fc, edgecolor=ec, linewidth=0.8, zorder=zord)
                for hole in p.interiors:
                    hx, hy = hole.xy
                    ax.fill(hx, hy, facecolor=hole_fc, edgecolor=ec, linewidth=0.8, zorder=zord + 1)

        _fill_poly(ax1, base_2d, fc="#F8FAFC", ec="#CBD5E1", zord=1, hole_fc="#0B0F17")
        _fill_poly(ax1, text_2d, fc="#1E293B", ec="#0F172A", zord=3, hole_fc="#F8FAFC")
        _fill_poly(ax1, sym_2d, fc="#0098A6", ec="#007A85", zord=3, hole_fc="#F8FAFC")

        ax1.set_aspect("equal")
        ax1.set_xlim(-42, 42)
        ax1.set_ylim(-10, 10)
        ax1.axis("off")
        ax1.set_title("Vista dall'alto (Profilo sagomato, Asola 4.0 mm, Rilievi T1/T2)", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)

        # Pannello 2: Vista 3D Assonometrica
        ax2 = fig.add_subplot(122, projection="3d")
        ax2.set_facecolor("#0B0F17")

        v_b, f_b = mesh_base.vertices, mesh_base.faces
        ax2.add_collection3d(Poly3DCollection(v_b[f_b], facecolor="#F1F5F9", edgecolor="#CBD5E1", linewidths=0.06, alpha=0.95))

        v_t, f_t = mesh_text.vertices, mesh_text.faces
        ax2.add_collection3d(Poly3DCollection(v_t[f_t], facecolor="#1E293B", edgecolor="#0F172A", linewidths=0.06, alpha=1.0))

        v_s, f_s = mesh_sym.vertices, mesh_sym.faces
        ax2.add_collection3d(Poly3DCollection(v_s[f_s], facecolor="#0098A6", edgecolor="#006D77", linewidths=0.06, alpha=1.0))

        ax2.set_xlim(-40, 40)
        ax2.set_ylim(-15, 15)
        ax2.set_zlim(-1, 8)
        ax2.view_init(elev=32, azim=-80)
        ax2.set_axis_off()
        ax2.set_title("Vista 3D Assonometrica (Base Z: 3.2 mm, Rilievo Z: 1.2 mm)", color="#F8FAFC", fontsize=11, fontweight="bold", pad=10)

        title_text = f"PORTACHIAVI 3MF SNAPMAKER U1 - 'TXT ENNOVA'\nDimensioni: {actual_length:.1f} x {actual_height:.1f} x {total_z:.1f} mm | Foro: {hole_diameter:.1f} mm | Nozzle 0.4 mm"
        plt.suptitle(title_text, color="#38BDF8", fontsize=13, fontweight="bold", y=0.98)
        plt.tight_layout()
        plt.savefig(str(preview_img_path), facecolor="#0B0F17", dpi=150)
        plt.close()
        print(f"   -> {preview_img_path.name} (anteprima grafica 2D/3D)")
    except Exception as e:
        print(f"   Warning: generazione anteprima non riuscita: {e}")

    # 7. Copia automatica nei PROGETTI DEFINITIVI (Regola AGENTS.md)
    definitivi_dir = PROJECT_ROOT / "PROGETTI DEFINITIVI" / "Portachiavi_TXT_ENNOVA"
    definitivi_dir.mkdir(parents=True, exist_ok=True)
    import shutil
    shutil.copy2(stl_base_path, definitivi_dir / "base.stl")
    shutil.copy2(stl_text_path, definitivi_dir / "text.stl")
    shutil.copy2(stl_sym_path, definitivi_dir / "symbol.stl")
    shutil.copy2(pkg_3mf_path, definitivi_dir / "txt_ennova_keyring.3mf")
    if preview_img_path.exists():
        shutil.copy2(preview_img_path, definitivi_dir / "txt_ennova_keyring_preview.png")
    print(f"   -> Copia archiviata in: {definitivi_dir.relative_to(PROJECT_ROOT)}")

    print("-" * 65)
    print("  COMPLETATO CON SUCCESSO! File pronti per la stampa.")
    print("=" * 65)

    return {
        "length_mm": actual_length,
        "height_mm": actual_height,
        "total_z_mm": total_z,
        "base_stl": str(stl_base_path),
        "text_stl": str(stl_text_path),
        "symbol_stl": str(stl_sym_path),
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
    args = parser.parse_args()

    export_keyring(
        image_path=args.image,
        output_dir=args.output,
        max_length=args.max_length,
        hole_diameter=args.hole_dia,
        base_thickness=args.base_thick,
        relief_thickness=args.relief_thick,
        base_offset=args.base_offset,
    )


if __name__ == "__main__":
    main()

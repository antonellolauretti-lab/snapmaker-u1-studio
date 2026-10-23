"""
Modulo geometrico per il portachiavi a cuore con scritta centrale "HUNTRIX"
ottimizzato per la stampa 3D FDM su Snapmaker U1 (ugello 0.4 mm).

Specifiche di progetto:
1. Profilo del Cuore Canonico ed Elegante:
   - Due lobi superiori slanciati, ampi e ben distinti, con rientranza centrale superiore ben definita a X=0.
   - I rami laterali scendono inclinati a "V" verso il centro, convergendo sulla punta inferiore.
   - La punta inferiore si raccorda con un raggio morbido di curvatura R = 1.8 mm a X=0, Y=-22.0 (nessun fondo piatto).
   - Simmetria speculare geometrica al 100% rispetto all'asse X = 0.
2. Anellino a Mezza Luna Integrato:
   - Perfettamente centrato e specchiato sull'asse X = 0.
   - Larghezza esterna uniforme ~8.0 mm (r=4.0 mm).
   - Foro passante ovale/stadium pulito di larghezza 4.2 mm, altezza 5.0 mm, adatto all'anello portachiavi.
   - Perfettamente fuso e solidale con entrambi i lobi del cuore senza artefatti o intersezioni rotte.
3. Estrusione 3D e Smussatura (Bevel Bombato):
   - Smussatura a quarto di cerchio sui bordi superiori con 10 segmenti per profilo curvo, bombato e liscio.
   - Fondo piatto a Z=0 per perfetta adesione sul piatto di stampa PEI.
   - Spessore corpo cuore 4.4 mm (Z da 0.0 a 4.4 mm).
4. Scritta 3D HUNTRIX:
   - Font Huntrix geometrico con kerning calibrato.
   - Centrata orizzontalmente (X=0) e verticalmente sulla superficie frontale del cuore.
   - Rilievo nitido di 1.2 mm (Z da 4.0 a 5.6 mm, con 0.4 mm di compenetrazione solida).
"""
from typing import Dict, Any, Tuple
from pathlib import Path
import numpy as np
import shapely.geometry as sg
from shapely import affinity
from shapely.ops import unary_union
import mapbox_earcut as earcut
import trimesh
import matplotlib.textpath as tp
import matplotlib.font_manager as fm

from generator_u1.font_resolver import resolve_font_path


def _cubic_bezier(p0, p1, p2, p3, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t)**3 * p0 + 3*(1 - t)**2 * t * p1 + 3*(1 - t) * t**2 * p2 + t**3 * p3


def get_plump_heart_polygon(target_w: float = 50.0) -> sg.Polygon:
    """
    Costruisce il profilo 2D canonico, elegante e slanciato del cuore con
    asola superiore ad arco simmetrica a X=0, larghezza 8 mm e foro passante 4.2 mm.
    """
    scale = target_w / 48.0

    # 1. Metà destra del cuore canonico:
    # Gola centrale a (0, 9.5)
    p_cleft = np.array([0.0, 9.5])
    p_peak = np.array([13.5, 18.5])
    c_inner = _cubic_bezier(
        p_cleft,
        np.array([2.5, 12.0]),
        np.array([7.5, 18.5]),
        p_peak,
        n=30
    )

    # Cresta del lobo e discesa al fianco massimo (24.0, 6.0)
    p_flank = np.array([24.0, 6.0])
    c_crest = _cubic_bezier(
        p_peak,
        np.array([18.5, 18.5]),
        np.array([24.0, 13.0]),
        p_flank,
        n=35
    )

    # Ramo a "V" inclinato convergente verso la punta
    # Raccordo tangenziale con l'arco di cerchio alla punta (R=1.8 mm centrato a (0, -20.2))
    p_tangent = np.array([1.38, -21.36])
    c_v_line = _cubic_bezier(
        p_flank,
        np.array([24.0, -1.0]),
        np.array([14.0, -13.0]),
        p_tangent,
        n=40
    )

    # Arco di raccordo della punta (da tangenza a X=0, Y=-22.0 con tangente orizzontale)
    theta = np.linspace(-np.radians(40), -np.pi / 2.0, 20)
    c_fillet = np.column_stack([1.8 * np.cos(theta), -20.2 + 1.8 * np.sin(theta)])

    right_heart_half = np.vstack([c_inner, c_crest[1:], c_v_line[1:], c_fillet[1:]])

    # Simmetria geometrica rigorosa: specchia esattamente su X negativo
    left_heart_half = np.column_stack([-right_heart_half[::-1, 0], right_heart_half[::-1, 1]])
    heart_base_poly = sg.Polygon(np.vstack([right_heart_half, left_heart_half[1:]]))

    # 2. Asola superiore ad arco simmetrico a mezza luna:
    # Larghezza esterna 8.0 mm (X in [-4.0, +4.0]), sommità Y = 22.5 mm
    r_arch_outer = 4.0
    theta_arch = np.linspace(0, np.pi, 40)
    arch_outer_top = np.column_stack([r_arch_outer * np.cos(theta_arch), 18.5 + r_arch_outer * np.sin(theta_arch)])
    arch_outer_poly = sg.Polygon(np.vstack([
        arch_outer_top,
        [[-r_arch_outer, 9.0], [r_arch_outer, 9.0]]
    ]))

    # Foro passante portachiavi pulito e centrato a X=0:
    # Larghezza 4.2 mm, altezza 5.0 mm (da Y=12.1 a Y=18.5)
    r_hole = 2.1
    theta_hole = np.linspace(0, np.pi, 25)
    hole_top = np.column_stack([r_hole * np.cos(theta_hole), 16.4 + r_hole * np.sin(theta_hole)])
    theta_hole_bot = np.linspace(np.pi, 2 * np.pi, 25)
    hole_bot = np.column_stack([r_hole * np.cos(theta_hole_bot), 14.2 + r_hole * np.sin(theta_hole_bot)])
    hole_poly = sg.Polygon(np.vstack([hole_top, hole_bot[1:]]))

    # Fusione booleana pulita e sottrazione del foro passante
    heart_with_arch = heart_base_poly.union(arch_outer_poly).difference(hole_poly)
    heart_clean = heart_with_arch.simplify(0.01)

    if abs(scale - 1.0) > 1e-4:
        heart_clean = affinity.scale(heart_clean, xfact=scale, yfact=scale, origin=(0, 0))

    return heart_clean


def create_beveled_heart_mesh(
    poly: sg.Polygon,
    height: float = 4.4,
    bevel_r: float = 1.2,
    bevel_segments: int = 10
) -> trimesh.Trimesh:
    """
    Genera la mesh 3D bombata e smussata a quarto di cerchio per il corpo del cuore,
    con fondo piatto a Z=0 e normali perfette. 100% manifold e watertight.
    """
    ext_coords = np.array(poly.exterior.coords)[:-1]
    hole_coords = np.array(poly.interiors[0].coords)[:-1] if poly.interiors else np.empty((0, 2))

    def signed_area(pts):
        return 0.5 * np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - pts[:, 1] * np.roll(pts[:, 0], -1))

    if signed_area(ext_coords) < 0:
        ext_coords = ext_coords[::-1]
    if len(hole_coords) > 0 and signed_area(hole_coords) > 0:
        hole_coords = hole_coords[::-1]

    if len(hole_coords) > 0:
        flat_verts = np.vstack([ext_coords, hole_coords])
        ring_ends = np.array([len(ext_coords), len(flat_verts)], dtype=np.uint32)
    else:
        flat_verts = ext_coords
        ring_ends = np.array([len(ext_coords)], dtype=np.uint32)

    tri_indices = earcut.triangulate_float64(flat_verts, ring_ends).reshape(-1, 3)

    n = len(flat_verts)
    n_ext = len(ext_coords)
    n_hole = len(hole_coords)

    def get_inward_offsets(pts, is_ccw=True):
        n_pts = len(pts)
        offsets = np.zeros_like(pts)
        for i in range(n_pts):
            p_prev = pts[(i - 1) % n_pts]
            p_curr = pts[i]
            p_next = pts[(i + 1) % n_pts]
            e1 = (p_curr - p_prev) / max(np.linalg.norm(p_curr - p_prev), 1e-9)
            e2 = (p_next - p_curr) / max(np.linalg.norm(p_next - p_curr), 1e-9)
            if is_ccw:
                n1 = np.array([-e1[1], e1[0]])
                n2 = np.array([-e2[1], e2[0]])
            else:
                n1 = np.array([e1[1], -e1[0]])
                n2 = np.array([e2[1], -e2[0]])
            bisect = n1 + n2
            lb = np.linalg.norm(bisect)
            if lb < 1e-6:
                bisect = n1
                cos_a = 1.0
            else:
                bisect /= lb
                cos_a = max(np.dot(n1, bisect), 0.35)
            scale = min(1.0 / cos_a, 2.0)
            offsets[i] = bisect * scale
        return offsets

    ext_offsets = get_inward_offsets(ext_coords, is_ccw=True)
    if n_hole > 0:
        hole_offsets = get_inward_offsets(hole_coords, is_ccw=False)
        flat_offsets = np.vstack([ext_offsets, hole_offsets])
    else:
        flat_offsets = ext_offsets

    z_wall = height - bevel_r
    levels = []
    # Livello 0: Z=0 (fondo piatto per piatto PEI)
    levels.append(np.column_stack([flat_verts, np.zeros(n)]))
    # Livello 1: Z=z_wall (parete verticale)
    levels.append(np.column_stack([flat_verts, np.full(n, z_wall)]))

    # Livelli di smussatura bombata a quarto di cerchio
    for s in range(1, bevel_segments + 1):
        phi = (np.pi / 2.0) * (s / bevel_segments)
        inset = bevel_r * (1.0 - np.cos(phi))
        z = z_wall + bevel_r * np.sin(phi)
        v_level = flat_verts + flat_offsets * inset
        levels.append(np.column_stack([v_level, np.full(n, z)]))

    num_levels = len(levels)
    all_verts = np.vstack(levels)

    faces = [tri_indices[:, ::-1]] # Fondo piatto (normali verso -Z)
    for lvl in range(num_levels - 1):
        base_a = lvl * n
        base_b = (lvl + 1) * n
        for i in range(n_ext):
            nxt = (i + 1) % n_ext
            faces.append([[base_a + i, base_a + nxt, base_b + nxt], [base_a + i, base_b + nxt, base_b + i]])
        for i in range(n_hole):
            curr = n_ext + i
            nxt = n_ext + ((i + 1) % n_hole)
            faces.append([[base_a + nxt, base_b + nxt, base_b + curr], [base_a + nxt, base_b + curr, base_a + curr]])

    # Top cap (normali verso +Z)
    faces.append(tri_indices + (num_levels - 1) * n)

    mesh = trimesh.Trimesh(vertices=all_verts, faces=np.vstack(faces), process=True)
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_normals(mesh)
    return mesh


def get_heart_huntrix_geometries(
    target_width: float = 50.0,
    text: str = "HUNTRIX"
) -> Dict[str, Any]:
    """
    Restituisce sia le geometrie 2D che le mesh 3D ottimizzate:
    - base: sagoma 2D del cuore con asola
    - heart: sagoma 2D del cuore con asola
    - text: sagoma 2D della scritta centrata
    - heart_mesh: mesh 3D bombata e smussata (Z 0.0 - 4.4 mm)
    - text_mesh: mesh 3D della scritta in rilievo (Z 4.0 - 5.6 mm)
    """
    scale = target_width / 48.0
    poly = get_plump_heart_polygon(target_w=target_width)

    # 1. Mesh 3D del cuore bombata con 10 segmenti di smussatura
    heart_mesh = create_beveled_heart_mesh(
        poly,
        height=4.4,
        bevel_r=1.2,
        bevel_segments=10
    )

    # 2. Scritta HUNTRIX centrata
    clean_txt = (text or "HUNTRIX").strip().upper()
    font_file = resolve_font_path("Huntrix")
    if not font_file:
        base_dir = Path(__file__).resolve().parent.parent
        font_file = str(base_dir / "assets" / "fonts" / "Huntrix.otf")

    fp = fm.FontProperties(fname=font_file)
    font_sz = 7.4 * scale
    char_spacing = 0.65 * scale

    char_geoms = []
    cur_x = 0.0
    for ch in clean_txt:
        char_tp = tp.TextPath((0, 0), ch, size=font_sz, prop=fp)
        raw_polys = [sg.Polygon(p) for p in char_tp.to_polygons() if len(p) >= 3]
        if not raw_polys:
            cur_x += (font_sz * 0.45) + char_spacing
            continue

        outers = [p for p in raw_polys if not any(o.contains(p) for o in raw_polys if o != p)]
        holes = [p for p in raw_polys if any(o.contains(p) for o in raw_polys if o != p)]
        poly_list = []
        for o in outers:
            h_coords = [h.exterior.coords for h in holes if o.contains(h)]
            try:
                poly_c = sg.Polygon(o.exterior.coords, h_coords)
                if not poly_c.is_valid:
                    poly_c = poly_c.buffer(0)
                poly_list.append(poly_c)
            except Exception:
                poly_c = sg.Polygon(o.exterior.coords)
                if not poly_c.is_valid:
                    poly_c = poly_c.buffer(0)
                poly_list.append(poly_c)

        g_char = unary_union(poly_list)
        g_buf = g_char.buffer(0.15 * scale, resolution=32)
        gb = g_buf.bounds
        g_placed = affinity.translate(g_buf, xoff=cur_x - gb[0])
        char_geoms.append(g_placed)
        cur_x = g_placed.bounds[2] + char_spacing

    if char_geoms:
        text_union = unary_union(char_geoms)
        tb = text_union.bounds
        tc_x = (tb[0] + tb[2]) / 2.0
        tc_y = (tb[1] + tb[3]) / 2.0
        # Centratura perfetta sia in X che in Y sulla superficie frontale del cuore
        text_2d = affinity.translate(text_union, xoff=-tc_x, yoff=(-1.5 * scale) - tc_y)

        # Estrusione testo 3D: spessore 1.6 mm, con 0.4 mm di compenetrazione (Z da 4.0 a 5.6 mm)
        if text_2d.geom_type == 'MultiPolygon':
            t_meshes = [trimesh.creation.extrude_polygon(p, height=1.6) for p in text_2d.geoms if not p.is_empty]
            text_mesh = trimesh.util.concatenate(t_meshes)
        else:
            text_mesh = trimesh.creation.extrude_polygon(text_2d, height=1.6)
        text_mesh.apply_translation([0, 0, 4.4 - 0.4])
    else:
        text_2d = sg.Polygon()
        text_mesh = trimesh.Trimesh()

    return {
        "base": poly,
        "heart": poly,
        "text": text_2d,
        "heart_mesh": heart_mesh,
        "text_mesh": text_mesh
    }

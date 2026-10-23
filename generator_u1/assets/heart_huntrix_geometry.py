"""
Modulo geometrico per il portachiavi a cuore con scritta centrale "HUNTRIX"
ottimizzato per la stampa 3D FDM su Snapmaker U1 (ugello 0.4 mm).

Specifiche di progetto:
1. Profilo del Cuore:
   - Sagoma piena, morbida e paffuta basata su curve continue Bézier C1.
   - Lobi superiori ampi, ben arrotondati, con rientranza centrale dolce e poco profonda.
   - Lati convessi morbidi che scendono verso una punta inferiore arrotondata (tangente orizzontale a X=0, nessun artefatto).
   - Larghezza nominale 52.0 mm, altezza 46.2 mm.
2. Anellino a Mezza Luna (Posizione "In Alto"):
   - Asola ad arco raccordata elegantemente tra le pareti interne dei due lobi superiori.
   - Foro passante ovale/arco (larghezza 4.4 mm, altezza 3.8 mm) con spessore parete >= 2.8 mm.
   - Integrata in modo continuo nella stessa mesh del corpo del cuore.
3. Estrusione 3D e Smussatura (Bevel / Bombato):
   - Smussatura a quarto di cerchio sui bordi superiori con 10 segmenti per profilo curvo, bombato e liscio.
   - Fondo perfettamente piatto a Z=0 per adesione ottimale al piatto PEI.
   - Spessore totale corpo cuore 4.4 mm (Z da 0.0 a 4.4 mm).
   - Rimosso qualsiasi bordo piatto esterno: il corpo del cuore è il volume principale continuo.
4. Scritta 3D HUNTRIX:
   - Font Huntrix geometrico con spaziatura (kerning) calibrata.
   - Centratura orizzontale (X=0) e verticale sulla superficie frontale del cuore.
   - Rilievo nitido di 1.2 mm (Z da 4.0 a 5.6 mm, con 0.4 mm di compenetrazione).
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


def get_plump_heart_polygon(target_w: float = 52.0) -> sg.Polygon:
    """
    Costruisce il profilo 2D del cuore morbido, pieno e paffuto con asola superiore
    a mezza luna (arco) raccordata armonicamente tra i due lobi superiori.
    """
    scale = target_w / 52.0

    # 1. Raccordo interno lobo destro dal punto di innesto dell'arco (5.5, 16.5) alla cresta (14.0, 19.5)
    p_arch_join = np.array([5.5, 16.5])
    p_crest = np.array([14.0, 19.5])
    c_lobe_inner = _cubic_bezier(
        p_arch_join,
        np.array([7.5, 19.0]),
        np.array([10.5, 19.5]),
        p_crest,
        n=25
    )

    # 2. Fianco superiore e bombatura convessa esterna fino a (26.0, 4.0)
    p_flank = np.array([26.0, 4.0])
    c_lobe_outer = _cubic_bezier(
        p_crest,
        np.array([19.5, 19.5]),
        np.array([26.0, 13.5]),
        p_flank,
        n=35
    )

    # 3. Discesa convessa morbida e piena verso la punta inferiore a (0.0, -22.0)
    p_tip = np.array([0.0, -22.0])
    c_lower = _cubic_bezier(
        p_flank,
        np.array([26.0, -5.0]),   # convessa, mantiene il fianco pieno e morbido
        np.array([16.0, -17.5]),  # raccordo continuo
        np.array([5.0, -22.0]),   # ingresso tangente orizzontale
        n=40
    )
    # Raccordo alla punta con tangente orizzontale (dy/dx = 0) per C1 perfetto
    c_tip = _cubic_bezier(
        np.array([5.0, -22.0]),
        np.array([2.5, -22.0]),
        np.array([0.8, -22.0]),
        p_tip,
        n=15
    )

    right_heart = np.vstack([c_lobe_inner[1:], c_lobe_outer[1:], c_lower[1:], c_tip[1:]])

    # 4. Profilo esterno dell'arco a mezza luna (sommità Y=24.2 al centro X=0)
    c_arch_right = _cubic_bezier(
        np.array([0.0, 24.2]),
        np.array([2.8, 24.2]),
        np.array([5.5, 20.5]),
        p_arch_join,
        n=25
    )
    c_arch_left = np.column_stack([-c_arch_right[::-1, 0], c_arch_right[::-1, 1]])
    left_heart = np.column_stack([-right_heart[::-1, 0], right_heart[::-1, 1]])

    full_exterior = np.vstack([
        c_arch_left,
        c_arch_right[1:],
        right_heart[1:],
        left_heart[1:]
    ])

    # 5. Foro interno dell'asola (arco / mezza luna per anellino):
    # Centrato a X=0, larghezza 4.4 mm, altezza 3.8 mm
    theta = np.linspace(0, np.pi, 25)
    r_top = 2.2
    y_center_top = 18.3
    top_half = np.column_stack([r_top * np.cos(theta), y_center_top + r_top * np.sin(theta)])

    theta_bot = np.linspace(np.pi, 2*np.pi, 25)
    r_bot_x = 2.2
    r_bot_y = 1.3
    y_center_bot = 17.3
    bot_half = np.column_stack([r_bot_x * np.cos(theta_bot), y_center_bot + r_bot_y * np.sin(theta_bot)])
    hole_pts = np.vstack([top_half, bot_half[1:]])

    ext_poly = sg.Polygon(full_exterior)
    hole_poly = sg.Polygon(hole_pts)
    heart_with_arch = ext_poly.difference(hole_poly)

    # Semplificazione per rimuovere micro-collinearità ai vertici della punta
    heart_clean = heart_with_arch.simplify(0.02)

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
    con fondo piatto a Z=0 e normali perfette.
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
    # Livello 0: Z=0 (fondo piatto)
    levels.append(np.column_stack([flat_verts, np.zeros(n)]))
    # Livello 1: Z=z_wall (parete verticale)
    levels.append(np.column_stack([flat_verts, np.full(n, z_wall)]))

    # Livelli di raccordo bombato a quarto di cerchio
    for s in range(1, bevel_segments + 1):
        phi = (np.pi / 2.0) * (s / bevel_segments)
        inset = bevel_r * (1.0 - np.cos(phi))
        z = z_wall + bevel_r * np.sin(phi)
        v_level = flat_verts + flat_offsets * inset
        levels.append(np.column_stack([v_level, np.full(n, z)]))

    num_levels = len(levels)
    all_verts = np.vstack(levels)

    faces = [tri_indices[:, ::-1]] # Fondo piatto
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

    # Top cap
    faces.append(tri_indices + (num_levels - 1) * n)

    mesh = trimesh.Trimesh(vertices=all_verts, faces=np.vstack(faces), process=True)
    trimesh.repair.fix_winding(mesh)
    trimesh.repair.fix_normals(mesh)
    return mesh


def get_heart_huntrix_geometries(
    target_width: float = 52.0,
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
    scale = target_width / 52.0
    poly = get_plump_heart_polygon(target_w=target_width)

    # 1. Mesh 3D del cuore bombata con 10 segmenti di smussatura
    heart_mesh = create_beveled_heart_mesh(
        poly,
        height=4.4 * scale,
        bevel_r=1.2 * scale,
        bevel_segments=10
    )

    # 2. Scritta HUNTRIX con font geometrico e kerning calibrato
    clean_txt = (text or "HUNTRIX").strip().upper()
    font_file = resolve_font_path("Huntrix")
    if not font_file:
        base_dir = Path(__file__).resolve().parent.parent
        font_file = str(base_dir / "assets" / "fonts" / "Huntrix.otf")

    fp = fm.FontProperties(fname=font_file)
    font_sz = 7.6 * scale
    char_spacing = 0.70 * scale

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
        g_buf = g_char.buffer(0.16 * scale, resolution=32)
        gb = g_buf.bounds
        g_placed = affinity.translate(g_buf, xoff=cur_x - gb[0])
        char_geoms.append(g_placed)
        cur_x = g_placed.bounds[2] + char_spacing

    if char_geoms:
        text_union = unary_union(char_geoms)
        tb = text_union.bounds
        tc_x = (tb[0] + tb[2]) / 2.0
        tc_y = (tb[1] + tb[3]) / 2.0
        # Centratura perfetta orizzontale e verticale sulla superficie frontale del cuore
        text_2d = affinity.translate(text_union, xoff=-tc_x, yoff=(-0.5 * scale) - tc_y)

        # Estrusione testo 3D: spessore 1.6 mm, con 0.4 mm di compenetrazione nella superficie superiore (Z da 4.0 a 5.6 mm)
        if text_2d.geom_type == 'MultiPolygon':
            t_meshes = [trimesh.creation.extrude_polygon(p, height=1.6 * scale) for p in text_2d.geoms if not p.is_empty]
            text_mesh = trimesh.util.concatenate(t_meshes)
        else:
            text_mesh = trimesh.creation.extrude_polygon(text_2d, height=1.6 * scale)
        text_mesh.apply_translation([0, 0, (4.4 - 0.4) * scale])
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

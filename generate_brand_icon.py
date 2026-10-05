#!/usr/bin/env python3
"""
generate_brand_icon.py - Generatore icona moderna 3D Isometrica per il brand GadgetPoint.
Produce icone PWA, iOS Apple Touch Icon e Favicon ad altissima definizione.
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def create_gradient_square(size: int, color1: tuple, color2: tuple) -> Image.Image:
    """Crea una base con gradiente diagonale a 45 gradi."""
    base = Image.new("RGBA", (size, size), color1)
    top = Image.new("RGBA", (size, size), color2)
    mask = Image.new("L", (size, size))
    draw_mask = ImageDraw.Draw(mask)
    for y in range(size):
        for x in range(size):
            factor = (x + y) / (2.0 * size)
            mask.putpixel((x, y), int(factor * 255))
    return Image.composite(top, base, mask)


def generate_gadgetpoint_icon(size: int = 512) -> Image.Image:
    """Genera l'icona isometrica 3D high-tech GadgetPoint a risoluzione variabile."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 1. SFONDO SCURO PRINCIPALE (#090d16 -> #111827)
    c_bg1 = (9, 13, 22, 255)
    c_bg2 = (17, 24, 39, 255)
    bg_img = create_gradient_square(size, c_bg1, c_bg2)

    # 2. SQUIRCLE CON ANGOLI ARROTONDATI (iOS STYLE)
    pad = int(size * 0.035)
    badge_w = size - (2 * pad)
    radius = int(size * 0.22)

    squircle_mask = Image.new("L", (size, size), 0)
    sq_draw = ImageDraw.Draw(squircle_mask)
    sq_draw.rounded_rectangle([pad, pad, pad + badge_w, pad + badge_w], radius=radius, fill=255)

    img.paste(bg_img, (0, 0), squircle_mask)

    # 3. AMBIENT GLOW CENTRALE (Aura neon ciano e viola diffusa)
    halo_size = int(size * 0.85)
    halo = Image.new("RGBA", (halo_size, halo_size), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    halo_draw.ellipse([0, 0, halo_size, halo_size], fill=(0, 242, 254, 70))
    halo = halo.filter(ImageFilter.GaussianBlur(radius=int(size * 0.15)))
    img.paste(halo, (int((size - halo_size) / 2), int((size - halo_size) / 2)), halo)

    # 4. RIFLESSO LUCIDO VETRO CURVO (Glossy Highlight)
    gloss = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gloss)
    g_draw.ellipse(
        [pad - int(size * 0.15), pad - int(size * 0.28), pad + badge_w + int(size * 0.15), int(size * 0.40)],
        fill=(255, 255, 255, 45)
    )
    gloss = Image.composite(gloss, Image.new("RGBA", (size, size), (0, 0, 0, 0)), squircle_mask)
    img = Image.alpha_composite(img, gloss)

    # 5. BORDO LUMINOSO NEON SUL PERIMETRO
    border_draw = ImageDraw.Draw(img)
    border_w = max(2, int(size * 0.016))
    border_draw.rounded_rectangle(
        [pad, pad, pad + badge_w, pad + badge_w],
        radius=radius,
        outline=(56, 189, 248, 190),
        width=border_w
    )

    # 6. CUBO ISOMETRICO MULTI-LAYER (STAMPA 3D SLICES)
    cx = size * 0.50
    cy = size * 0.45
    w = size * 0.31
    rh = w * 0.577
    total_h = size * 0.38

    num_layers = 4
    slice_h = total_h / num_layers
    gap = size * 0.009

    layer_colors = [
        {"left": (15, 23, 42), "right": (30, 41, 59), "neon": (59, 130, 246, 200)},
        {"left": (29, 78, 216), "right": (37, 99, 235), "neon": (96, 165, 250, 230)},
        {"left": (109, 40, 217), "right": (139, 92, 246), "neon": (192, 132, 252, 240)},
        {"left": (2, 132, 199), "right": (0, 242, 254), "neon": (125, 250, 255, 255)},
    ]

    cube_draw = ImageDraw.Draw(img)

    for i in range(num_layers):
        y_base = cy + (total_h * 0.5) - (i * slice_h)
        y_top = y_base - slice_h + gap
        info = layer_colors[i]

        # Faccia sinistra
        pts_left = [
            (cx - w, y_base - rh),
            (cx, y_base),
            (cx, y_top),
            (cx - w, y_top - rh)
        ]
        cube_draw.polygon(pts_left, fill=info["left"])

        # Faccia destra
        pts_right = [
            (cx, y_base),
            (cx + w, y_base - rh),
            (cx + w, y_top - rh),
            (cx, y_top)
        ]
        cube_draw.polygon(pts_right, fill=info["right"])

        # Linea neon orizzontale
        seam_w = max(1, int(size * 0.008))
        cube_draw.line([(cx - w, y_top - rh), (cx, y_top)], fill=info["neon"], width=seam_w)
        cube_draw.line([(cx, y_top), (cx + w, y_top - rh)], fill=info["neon"], width=seam_w)

    # FACCIA SUPERIORE ISOMETRICA
    y_top_surface = cy - (total_h * 0.5) + gap
    pts_top = [
        (cx, y_top_surface - (2 * rh)),
        (cx + w, y_top_surface - rh),
        (cx, y_top_surface),
        (cx - w, y_top_surface - rh)
    ]
    cube_draw.polygon(pts_top, fill=(0, 242, 254, 255))
    top_border_w = max(1, int(size * 0.012))
    cube_draw.line(pts_top + [pts_top[0]], fill=(255, 255, 255, 240), width=top_border_w)

    # 7. UGELLO DI STAMPA 3D TECNOLOGICO
    noz_x = cx + (w * 0.48)
    noz_tip_y = y_top_surface - (rh * 0.65)
    noz_w = size * 0.052
    noz_h = size * 0.095

    # Dissipatore (alette)
    sink_h = noz_h * 0.45
    sink_y = noz_tip_y - noz_h
    for k in range(3):
        fin_y = sink_y + (k * (sink_h / 3.0))
        cube_draw.line(
            [(noz_x - (noz_w * 0.7), fin_y), (noz_x + (noz_w * 0.7), fin_y)],
            fill=(160, 175, 195, 255),
            width=max(2, int(size * 0.009))
        )

    # Blocco riscaldante
    block_y = sink_y + sink_h
    block_h = noz_h * 0.28
    cube_draw.rectangle(
        [noz_x - (noz_w * 0.5), block_y, noz_x + (noz_w * 0.5), block_y + block_h],
        fill=(203, 213, 225, 255)
    )

    # Cono ottone
    pts_nozzle = [
        (noz_x - (noz_w * 0.45), block_y + block_h),
        (noz_x + (noz_w * 0.45), block_y + block_h),
        (noz_x + (noz_w * 0.12), noz_tip_y),
        (noz_x - (noz_w * 0.12), noz_tip_y)
    ]
    cube_draw.polygon(pts_nozzle, fill=(245, 158, 11, 255))

    # Filamento neon emesso
    fil_pts = [
        (noz_x, noz_tip_y),
        (noz_x - (w * 0.15), noz_tip_y + (rh * 0.25)),
        (noz_x - (w * 0.35), noz_tip_y + (rh * 0.35))
    ]
    cube_draw.line(fil_pts, fill=(0, 242, 254, 255), width=max(2, int(size * 0.013)))

    # Punto incandescente
    pt_r = size * 0.020
    cube_draw.ellipse([noz_x - pt_r, noz_tip_y - pt_r, noz_x + pt_r, noz_tip_y + pt_r], fill=(255, 255, 255, 255))

    # 8. MONOGRAMMA "GP"
    text_y = cy + (size * 0.08)
    font_size = int(size * 0.26)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("Arial Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    # Calcolo bounding box testo
    text_str = "GP"
    bbox = cube_draw.textbbox((0, 0), text_str, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) / 2
    ty = text_y

    # Ombra profonda
    shadow_offset = max(3, int(size * 0.022))
    cube_draw.text((tx, ty + shadow_offset), text_str, font=font, fill=(4, 7, 15, 240))

    # Bevel 3D
    cube_draw.text((tx, ty + (shadow_offset * 0.5)), text_str, font=font, fill=(3, 105, 161, 255))

    # Testo frontale bianco brillante
    cube_draw.text((tx, ty), text_str, font=font, fill=(255, 255, 255, 255))

    return img


def generate_all_icons():
    """Genera e distribuisce tutte le icone nelle rispettive directory statiche."""
    dirs = [
        Path("static/icons"),
        Path("frontend/static/icons"),
        Path("generator_u1/web/static/icons"),
    ]

    sizes = [
        ("apple-touch-icon.png", 180),
        ("icon-192.png", 192),
        ("icon-512.png", 512),
        ("favicon.png", 64),
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        for fname, sz in sizes:
            out_p = d / fname
            im = generate_gadgetpoint_icon(sz)
            im.save(out_p, "PNG")
            print(f"Generato: {out_p} ({sz}x{sz})")

        # Favicon ICO
        ico_im = generate_gadgetpoint_icon(64)
        ico_im.save(d / "favicon.ico", format="ICO", sizes=[(64, 64), (32, 32), (16, 16)])
        print(f"Generato: {d / 'favicon.ico'}")


if __name__ == "__main__":
    generate_all_icons()

#!/usr/bin/env python3
"""
generate_brand_icon.py - Generatore icona moderna 3D per GadgetPoint (Stampante 3D + Portachiavi).
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
    for y in range(size):
        for x in range(size):
            factor = (x + y) / (2.0 * size)
            mask.putpixel((x, y), int(factor * 255))
    return Image.composite(top, base, mask)


def generate_gadgetpoint_icon(size: int = 512) -> Image.Image:
    """Genera l'icona con stampante 3D e portachiavi personalizzato emergente."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 1. SFONDO SCURO PRINCIPALE (#0b0f19 -> #111827)
    c_bg1 = (11, 15, 25, 255)
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

    # 3. AMBIENT GLOW CENTRALE (Aura neon ciano e arancio)
    halo_size = int(size * 0.85)
    halo = Image.new("RGBA", (halo_size, halo_size), (0, 0, 0, 0))
    halo_draw = ImageDraw.Draw(halo)
    halo_draw.ellipse([0, 0, halo_size, halo_size], fill=(0, 242, 254, 65))
    halo = halo.filter(ImageFilter.GaussianBlur(radius=int(size * 0.15)))
    img.paste(halo, (int((size - halo_size) / 2), int((size - halo_size) / 2)), halo)

    # 4. RIFLESSO LUCIDO SUPERIORE (Glossy glass highlight)
    gloss = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gloss)
    g_draw.ellipse(
        [pad - int(size * 0.15), pad - int(size * 0.28), pad + badge_w + int(size * 0.15), int(size * 0.40)],
        fill=(255, 255, 255, 40)
    )
    gloss = Image.composite(gloss, Image.new("RGBA", (size, size), (0, 0, 0, 0)), squircle_mask)
    img = Image.alpha_composite(img, gloss)

    # 5. BORDO LUMINOSO AL NEON
    border_draw = ImageDraw.Draw(img)
    border_w = max(2, int(size * 0.016))
    border_draw.rounded_rectangle(
        [pad, pad, pad + badge_w, pad + badge_w],
        radius=radius,
        outline=(56, 189, 248, 190),
        width=border_w
    )

    # 6. STAMPANTE 3D (TELAIO CUBICO E PIATTO RISCALDATO)
    cx = size * 0.50
    bed_w = size * 0.36
    bed_rh = bed_w * 0.48
    bed_y = size * 0.72

    draw = ImageDraw.Draw(img)

    # Piatto di stampa
    pts_bed = [
        (cx, bed_y - (2 * bed_rh)),
        (cx + bed_w, bed_y - bed_rh),
        (cx, bed_y),
        (cx - bed_w, bed_y - bed_rh)
    ]
    draw.polygon(pts_bed, fill=(18, 25, 40, 255))
    draw.line(pts_bed + [pts_bed[0]], fill=(56, 189, 248, 180), width=max(1, int(size * 0.008)))

    # Griglia piatto
    for g_idx in range(1, 4):
        t = g_idx / 4.0
        p1 = (cx - (bed_w * (1 - t)), bed_y - (bed_rh * (1 + t)))
        p2 = (cx + (bed_w * t), bed_y - (bed_rh * t))
        draw.line([p1, p2], fill=(56, 189, 248, 45), width=max(1, int(size * 0.003)))

        p3 = (cx + (bed_w * (1 - t)), bed_y - (bed_rh * (1 + t)))
        p4 = (cx - (bed_w * t), bed_y - (bed_rh * t))
        draw.line([p3, p4], fill=(56, 189, 248, 45), width=max(1, int(size * 0.003)))

    # Telaio cubico aperto
    frame_h = size * 0.48
    frame_top_y = bed_y - (2 * bed_rh) - frame_h
    frame_col = (71, 85, 105, 140)
    draw.line([(cx, bed_y - (2 * bed_rh)), (cx, frame_top_y)], fill=frame_col, width=max(2, int(size * 0.012)))
    draw.line([(cx + bed_w, bed_y - bed_rh), (cx + bed_w, bed_y - bed_rh - frame_h)], fill=frame_col, width=max(2, int(size * 0.012)))
    draw.line([(cx - bed_w, bed_y - bed_rh), (cx - bed_w, bed_y - bed_rh - frame_h)], fill=frame_col, width=max(2, int(size * 0.012)))
    draw.line([(cx - bed_w, bed_y - bed_rh - frame_h), (cx, frame_top_y)], fill=frame_col, width=max(2, int(size * 0.012)))
    draw.line([(cx, frame_top_y), (cx + bed_w, bed_y - bed_rh - frame_h)], fill=frame_col, width=max(2, int(size * 0.012)))

    # Traversa asse X
    gantry_y = size * 0.28
    draw.line(
        [(cx - (bed_w * 0.70), gantry_y - (bed_rh * 0.60)), (cx + (bed_w * 0.90), gantry_y + (bed_rh * 0.40))],
        fill=(148, 163, 184, 210), width=max(3, int(size * 0.016))
    )

    # Gruppo estrusore / Hotend
    car_x = cx + (size * 0.18)
    car_y = gantry_y + (size * 0.03)
    car_w = size * 0.09
    car_h = size * 0.08
    draw.rectangle([car_x - (car_w * 0.5), car_y, car_x + (car_w * 0.5), car_y + car_h], fill=(30, 41, 59, 255), outline=(56, 189, 248, 255), width=max(1, int(size * 0.006)))

    # Alette dissipatore
    for f in range(1, 4):
        fy = car_y + (f * (car_h * 0.22))
        draw.line([(car_x - (car_w * 0.4), fy), (car_x + (car_w * 0.4), fy)], fill=(148, 163, 184, 255), width=max(1, int(size * 0.007)))

    # Nozzle ottone dorato
    noz_tip_y = car_y + car_h + (size * 0.035)
    pts_nozzle = [
        (car_x - (car_w * 0.28), car_y + car_h),
        (car_x + (car_w * 0.28), car_y + car_h),
        (car_x + (car_w * 0.09), noz_tip_y),
        (car_x - (car_w * 0.09), noz_tip_y)
    ]
    draw.polygon(pts_nozzle, fill=(245, 158, 11, 255))
    tip_r = size * 0.016
    draw.ellipse([car_x - tip_r, noz_tip_y - tip_r, car_x + tip_r, noz_tip_y + tip_r], fill=(255, 255, 255, 240))

    # 7. PORTACHIAVI 3D IN USCITA
    # Inclinazione dinamica con tag layer
    tag_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    tag_draw = ImageDraw.Draw(tag_img)

    kw = int(size * 0.28)
    kh = int(size * 0.44)
    kr = int(size * 0.05)

    kx0 = int((size - kw) / 2)
    ky0 = int((size - kh) / 2)

    # Ombra
    tag_draw.rounded_rectangle([kx0 + int(size * 0.03), ky0 + int(size * 0.04), kx0 + kw + int(size * 0.03), ky0 + kh + int(size * 0.04)], radius=kr, fill=(4, 7, 15, 180))

    # Bevel 3D arancio scuro
    thick = int(size * 0.02)
    tag_draw.rounded_rectangle([kx0 + thick, ky0 + thick, kx0 + kw + thick, ky0 + kh + thick], radius=kr, fill=(194, 65, 12, 255))

    # Corpo arancio sunset
    tag_draw.rounded_rectangle([kx0, ky0, kx0 + kw, ky0 + kh], radius=kr, fill=(255, 107, 0, 255), outline=(255, 237, 213, 240), width=max(1, int(size * 0.009)))

    # Foro passante
    hole_y = ky0 + int(kr * 1.5)
    hole_cx = int(size / 2)
    hole_r = int(size * 0.03)
    tag_draw.ellipse([hole_cx - hole_r, hole_y - hole_r, hole_cx + hole_r, hole_y + hole_r], fill=(14, 20, 34, 255))

    # Anello metallico
    ring_r = int(size * 0.052)
    tag_draw.ellipse([hole_cx - ring_r, hole_y - int(ring_r * 1.1), hole_cx + ring_r, hole_y + int(ring_r * 0.9)], outline=(226, 232, 240, 255), width=max(2, int(size * 0.016)))

    # Testo "GP" in rilievo
    font_size = int(size * 0.17)
    try:
        font = ImageFont.truetype("arialbd.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("Arial Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    bbox = tag_draw.textbbox((0, 0), "GP", font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) / 2
    ty = size * 0.52

    tag_draw.text((tx, ty + 2), "GP", font=font, fill=(154, 52, 18, 180))
    tag_draw.text((tx, ty), "GP", font=font, fill=(255, 255, 255, 255))

    # Ruota il portachiavi di circa -24 gradi
    rotated_tag = tag_img.rotate(24, resample=Image.Resampling.BICUBIC, center=(size * 0.5, size * 0.5))
    img.paste(rotated_tag, (-int(size * 0.06), int(size * 0.02)), rotated_tag)

    # 8. FILAMENTO NEON FLUIDO
    draw = ImageDraw.Draw(img)
    fil_x = cx + (size * 0.08)
    fil_y = size * 0.62
    draw.line([(car_x, noz_tip_y), (fil_x, fil_y)], fill=(0, 242, 254, 255), width=max(2, int(size * 0.012)))
    c_r = size * 0.016
    draw.ellipse([fil_x - c_r, fil_y - c_r, fil_x + c_r, fil_y + c_r], fill=(0, 242, 254, 255))

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

        ico_im = generate_gadgetpoint_icon(64)
        ico_im.save(d / "favicon.ico", format="ICO", sizes=[(64, 64), (32, 32), (16, 16)])
        print(f"Generato: {d / 'favicon.ico'}")


if __name__ == "__main__":
    generate_all_icons()

"""
Modulo di risoluzione e gestione dei font incorporati nel repository.
Garantisce che tutti i font (inclusi corsivi e script) abbiano un percorso fisico
valido su disco (.ttf) sia in locale (Windows) che sul Cloud (Linux/Render).
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from matplotlib.font_manager import FontProperties

BASE_DIR = Path(__file__).resolve().parent
ASSETS_FONTS_DIR = BASE_DIR / "assets" / "fonts"
FONTS_DIR = BASE_DIR / "fonts"

# Assicura esistenza directory
ASSETS_FONTS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_DIR.mkdir(parents=True, exist_ok=True)

# Mappe di corrispondenza per font commerciali o alias verso alternative open-source bundled
FONT_ALIAS_MAP: Dict[str, str] = {
    # Script / Corsivi
    "segoe script": "DancingScript-Bold.ttf",
    "segoescript": "DancingScript-Bold.ttf",
    "dancing script": "DancingScript-Bold.ttf",
    "dancingscript": "DancingScript-Bold.ttf",
    "caveat": "Caveat-Bold.ttf",
    "great vibes": "GreatVibes-Regular.ttf",
    "greatvibes": "GreatVibes-Regular.ttf",
    "pacifico": "Pacifico.ttf",
    "lobster": "Lobster.ttf",
    # Display / Bold
    "impact": "Impact.ttf",
    "anton": "Anton.ttf",
    "bebas neue": "Bebas_Neue.ttf",
    "bebasneue": "Bebas_Neue.ttf",
    "bungee": "Bungee.ttf",
    "righteous": "Righteous.ttf",
    "bangers": "Bangers.ttf",
    "orbitron": "Orbitron.ttf",
    "oswald": "Oswald.ttf",
    "permanent marker": "Permanent_Marker.ttf",
    "permanentmarker": "Permanent_Marker.ttf",
    # Sans-serif & Serif
    "montserrat": "Montserrat.ttf",
    "poppins": "Poppins.ttf",
    "roboto": "Roboto.ttf",
    "ubuntu": "Ubuntu.ttf",
    "playfair display": "Playfair_Display.ttf",
    "playfairdisplay": "Playfair_Display.ttf",
    "cinzel": "Cinzel.ttf",
    "arial black": "Anton.ttf",
    "arial": "Roboto.ttf",
    "segoe ui": "Montserrat.ttf",
    "georgia": "Playfair_Display.ttf",
    "consolas": "Ubuntu.ttf",
}

def resolve_font_path(font_name: Optional[str], explicit_path: Optional[str] = None) -> Optional[str]:
    """
    Risolve il percorso assoluto a un file .ttf/.otf nel repository
    evitando dipendenze dall'ambiente host (Windows vs Linux cloud).
    """
    if explicit_path and os.path.isfile(explicit_path):
        return explicit_path

    if not font_name:
        p = ASSETS_FONTS_DIR / "Anton.ttf"
        if p.is_file():
            return str(p)
        return None

    clean_name = font_name.strip()
    lower_name = clean_name.lower()

    # 1. Controllo mappa alias
    target_filename = FONT_ALIAS_MAP.get(lower_name)
    if target_filename:
        for folder in [ASSETS_FONTS_DIR, FONTS_DIR]:
            candidate = folder / target_filename
            if candidate.is_file():
                return str(candidate)

    # 2. Controllo diretto del nome file nelle cartelle
    candidate_filenames = [
        clean_name if clean_name.endswith((".ttf", ".otf")) else f"{clean_name}.ttf",
        f"{clean_name.replace(' ', '_')}.ttf",
        f"{clean_name.replace(' ', '-')}.ttf",
        f"{clean_name.replace(' ', '')}.ttf",
    ]
    for folder in [ASSETS_FONTS_DIR, FONTS_DIR]:
        for fname in candidate_filenames:
            candidate = folder / fname
            if candidate.is_file():
                return str(candidate)

    # 3. Controllo case-insensitive parziale
    for folder in [ASSETS_FONTS_DIR, FONTS_DIR]:
        if folder.is_dir():
            for f in folder.glob("*.ttf"):
                stem_lower = f.stem.lower()
                if stem_lower == lower_name or stem_lower.replace("_", " ") == lower_name or stem_lower.replace("-", " ") == lower_name:
                    return str(f)

    return None

def get_font_properties(font_name: Optional[str], explicit_path: Optional[str] = None) -> FontProperties:
    """Restituisce un oggetto FontProperties con percorso fisico valido per Matplotlib."""
    path = resolve_font_path(font_name, explicit_path)
    if path and os.path.isfile(path):
        return FontProperties(fname=path)

    # Fallback se non trovato su disco
    weight = "bold" if font_name and font_name.lower() in ["arial", "segoe ui", "georgia"] else "normal"
    return FontProperties(family=font_name or "sans-serif", weight=weight)

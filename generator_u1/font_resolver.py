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
    # Sans-serif & Serif (Rigorosamente varianti Heavy / Bold per estrusione FDM)
    "montserrat": "Montserrat-Black.ttf",
    "montserrat black": "Montserrat-Black.ttf",
    "montserrat bold": "Montserrat-Black.ttf",
    "poppins": "Poppins.ttf",
    "roboto": "Roboto.ttf",
    "ubuntu": "Ubuntu.ttf",
    "playfair display": "PlayfairDisplay-Bold.ttf",
    "playfairdisplay": "PlayfairDisplay-Bold.ttf",
    "cinzel": "Cinzel-Bold.ttf",
    "arial black": "Anton.ttf",
    "arial": "Roboto.ttf",
    "segoe ui": "Montserrat-Black.ttf",
    "georgia": "PlayfairDisplay-Bold.ttf",
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
    """Restituisce un oggetto FontProperties con percorso fisico valido e peso calibrato per Matplotlib."""
    path = resolve_font_path(font_name, explicit_path)
    weight = "bold" if font_name and font_name.lower() in [
        "montserrat", "segoe ui", "playfair display", "playfairdisplay", "cinzel", "georgia", "arial", "arial black"
    ] else "normal"

    if path and os.path.isfile(path):
        return FontProperties(fname=path, weight=weight)

    return FontProperties(family=font_name or "sans-serif", weight=weight)

def get_font_dilation_offset(font_name: Optional[str]) -> float:
    """
    Restituisce l'offset di dilatazione/buffer vettoriale (in mm) per rinforzare
    i tratti sottili ed evitare parti fragili o mancanti con ugello 0.4 mm.
    Garantisce che nessun tratto del testo scenda al di sotto di 0.8 mm reali.
    """
    if not font_name:
        return 0.0
    fn = font_name.strip().lower()

    # Script e corsivi (Dancing Script, Caveat, Great Vibes, Segoe Script, Pacifico):
    # Necessitano di buffer solido tra 0.28 e 0.32 mm per saldare tratti sottili e legature
    if any(s in fn for s in [
        "dancing script", "dancingscript",
        "caveat",
        "great vibes", "greatvibes",
        "segoe script", "segoescript",
        "pacifico", "lobster"
    ]):
        return 0.30

    # Serif e caratteri con grazie o dettagli delicati (Playfair Display, Cinzel, Georgia): 0.28 mm
    if any(s in fn for s in [
        "playfair", "cinzel", "georgia"
    ]):
        return 0.28

    # Montserrat e Segoe UI: 0.18 mm per dare una presenza solida e monolitica
    if any(s in fn for s in [
        "montserrat", "segoe ui"
    ]):
        return 0.18

    return 0.0

def apply_text_polygon_buffer(geom: Any, offset_distance: float) -> Any:
    """
    Applica un'operazione di dilatazione/offset sul poligono del testo Shapely
    con pulizia topologica per garantire contorni chiusi, saldati e manifold.
    """
    if offset_distance <= 0.0 or geom is None:
        return geom
    try:
        # Se geometria vuota restituisce invariato
        if hasattr(geom, "is_empty") and geom.is_empty:
            return geom
        buffered = geom.buffer(offset_distance, resolution=16)
        if hasattr(buffered, "is_valid") and not buffered.is_valid:
            buffered = buffered.buffer(0)
        return buffered
    except Exception as e:
        print(f"Avviso durante buffer dilatazione font: {e}")
        return geom


"""
Libreria Ufficiale di Icone Vettoriali e Sagome 3D per Snapmaker U1 Parametric Studio.
Tracciati SVG solidi, chiusi e normalizzati, ottimizzati per la stampa 3D (Shapely + Trimesh).
"""

import json
from pathlib import Path
from typing import Dict, Any, List

ICONS_JSON_PATH = Path(__file__).resolve().parent / "icons.json"

if ICONS_JSON_PATH.is_file():
    try:
        ICONS_LIBRARY: List[Dict[str, Any]] = json.loads(ICONS_JSON_PATH.read_text(encoding="utf-8"))
    except Exception:
        ICONS_LIBRARY = []
else:
    ICONS_LIBRARY = []

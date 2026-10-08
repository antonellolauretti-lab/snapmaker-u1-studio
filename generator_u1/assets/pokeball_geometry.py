"""
Geometrie vettoriali esatte 2D per la Pokéball multicolore ufficiale:
- Calotta superiore (Rosso #ee1515)
- Calotta inferiore (Bianco #ffffff)
- Bottone centrale (Bianco #ffffff)
Separati da un incavo geometrico negativo di 1.0 mm (zero nero, fondo blu della base).
Tutte le parti sono disgiunte a volume pieno, senza auto-intersezioni e manifold al 100%.
"""
import shapely.geometry as sg
from shapely.ops import unary_union
from shapely import affinity

REF_DIAMETER = 92.0

def get_pokeball_modular_components(target_diameter=None, gap=1.0):
    """
    Restituisce la tupla (top_shell, bottom_shell, None, button):
    - top_shell: calotta superiore (Rosso #ee1515)
    - bottom_shell: calotta inferiore (Bianco #ffffff)
    - black_structure: None (eliminata, separazione ad incavo a vuoto)
    - button: bottone centrale (Bianco #ffffff)
    Separati da una scanalatura geometrica a vuoto costante di 1.0 mm.
    """
    diam = float(target_diameter or REF_DIAMETER)
    r = diam / 2.0
    btn_r = max(1.2, r * 0.28)
    actual_gap = min(gap, r * 0.35)
    ring_outer_r = btn_r + actual_gap
    
    full_circle = sg.Point(0, 0).buffer(r, resolution=64)
    band = sg.box(-r * 1.5, -actual_gap / 2.0, r * 1.5, actual_gap / 2.0)
    central_channel = sg.Point(0, 0).buffer(ring_outer_r, resolution=64)
    groove = band.union(central_channel)
    
    top_box = sg.box(-r * 1.5, 0, r * 1.5, r * 1.5)
    top_shell = full_circle.intersection(top_box).difference(groove)
    
    bot_box = sg.box(-r * 1.5, -r * 1.5, r * 1.5, 0)
    bot_shell = full_circle.intersection(bot_box).difference(groove)
    
    button = sg.Point(0, 0).buffer(btn_r, resolution=64)
    
    return top_shell, bot_shell, None, button

def get_pokeball_geometry(target_diameter=None):
    """Restituisce il disco circolare completo di ingombro della Pokéball."""
    diam = float(target_diameter or REF_DIAMETER)
    return sg.Point(0, 0).buffer(diam / 2.0, resolution=64)

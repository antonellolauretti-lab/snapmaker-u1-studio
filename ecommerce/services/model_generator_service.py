"""
Servizio di generazione 3MF istantaneo per il Gestionale Ordini Snapmaker U1.
Riceve la configurazione memorizzata nell'ordine (tabella order_items) e compila
il file nativo .3MF multi-volume per Snapmaker Orca con:
- Zero torre di spurgo (enable_prime_tower=False)
- Assegnazione corretta estrusori (Toolhead fisiche U1)
- Colori filamento reali dai profili SnapSpeed/Silk
"""
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple

# Radice del progetto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generator_u1.generators.keychain_generator import generate_keychain_parts
from generator_u1.generators.desk_sign_generator import generate_desk_sign_parts
from generator_u1.packager.snapmaker_3mf import Snapmaker3MFPackager
from generator_u1.font_resolver import resolve_font_path

def compile_order_item_to_3mf(order_number: str, item_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Compila il pacchetto .3MF pronto per Snapmaker Orca per un singolo articolo ordinato.
    Restituisce (filepath_assoluto, nome_file_scaricabile).
    """
    params = dict(item_data.get("generator_params") or {})
    product_type = str(item_data.get("product_type") or params.get("generator") or "keychain").lower()

    # Risolvi font
    font_id = item_data.get("font_id") or params.get("font_family")
    resolved_font = resolve_font_path(font_id)
    if resolved_font:
        params["font_path"] = resolved_font
        params["font_family"] = font_id

    # Risolvi colori
    base_hex = item_data.get("base_color_hex") or params.get("base_color", "#080A0D")
    text_hex = item_data.get("text_color_hex") or params.get("text_color", "#D9DFE5")
    icon_hex = item_data.get("icon_color_hex") or params.get("icon_color") or text_hex
    
    # Se l'icona ha colore personalizzato diverso dal testo, assegna T2 (Estrusore 2)
    has_custom_icon = bool(
        item_data.get("has_custom_icon_color") or 
        params.get("custom_icon_color") or 
        (icon_hex.lower() != text_hex.lower() and (item_data.get("icon_id") or params.get("icon_name")) not in ("none", "", None))
    )

    if has_custom_icon:
        params["extruder_icon"] = 2
        filament_colors = [base_hex, text_hex, icon_hex, "#F8F81C"]
    else:
        params["extruder_icon"] = 1
        filament_colors = [base_hex, text_hex, "#E72F1D", "#F8F81C"]

    clean_text = "".join(c for c in (item_data.get("custom_text_line1") or "Model") if c.isalnum() or c in "_-").strip() or "Model"

    if "desk_sign" in product_type:
        params["text_line1"] = item_data.get("custom_text_line1") or params.get("text_line1", "DeskSign")
        if item_data.get("custom_text_line2"):
            params["line2_enabled"] = True
            params["text_line2"] = item_data.get("custom_text_line2")
        if font_id:
            params["font_family_line1"] = font_id
            params["font_family_line2"] = font_id
        if resolved_font:
            params["font_path_line1"] = resolved_font
            params["font_path_line2"] = resolved_font
        parts = generate_desk_sign_parts(params)
        filename = f"{order_number}_{clean_text}_DeskSign_U1.3mf"
        proj_name = f"{order_number}_{clean_text}_DeskSign"
    else:
        params["text"] = item_data.get("custom_text_line1") or params.get("text", "Keychain")
        if item_data.get("custom_text_line2"):
            params["line2_enabled"] = True
            params["text_line2"] = item_data.get("custom_text_line2")
        icon_val = item_data.get("icon_id") or params.get("icon_name") or params.get("icon_id")
        if icon_val:
            params["icon_name"] = icon_val
            params["icon_id"] = icon_val
        if item_data.get("base_style"):
            params["base_style"] = item_data.get("base_style")
        if item_data.get("hole_position"):
            params["hole_position"] = item_data.get("hole_position")
        icon_pos = item_data.get("icon_position") or params.get("icon_position") or "right"
        params["icon_position"] = icon_pos

        parts = generate_keychain_parts(params)
        filename = f"{order_number}_{clean_text}_Keychain_U1.3mf"
        proj_name = f"{order_number}_{clean_text}_Keychain"

    temp_dir = Path(tempfile.gettempdir())
    out_path = temp_dir / filename

    # Packager con preferenze Snapmaker U1
    packager = Snapmaker3MFPackager(
        project_name=proj_name,
        filament_colors=filament_colors,
        enable_prime_tower=False, # Come da AGENTS.md e requisiti di sistema
        enable_support=False,
        enable_brim=False
    )

    ref_3mf = PROJECT_ROOT / "PROGETTI DEFINITIVI" / "67_mechanism_complete_bicolor_V2" / "67_mechanism_U1_P2_ROSSO.3mf"
    default_profile = PROJECT_ROOT / "generator_u1" / "packager" / "profiles" / "snapmaker_u1_default_project.json"
    ref_path = str(ref_3mf) if ref_3mf.exists() else (str(default_profile) if default_profile.exists() else None)

    packager.export(parts, str(out_path), reference_config_path=ref_path)

    return str(out_path), filename

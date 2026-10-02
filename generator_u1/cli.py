import os
import sys
import json
import argparse
from pathlib import Path

# Aggiungi cartella root del progetto a sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generator_u1.generators.keychain_generator import generate_keychain_parts
from generator_u1.packager.snapmaker_3mf import Snapmaker3MFPackager

def load_default_params():
    schema_path = PROJECT_ROOT / "generator_u1" / "schemas" / "keychain_schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    defaults = {}
    for prop, val in schema.get("properties", {}).items():
        if "default" in val:
            defaults[prop] = val["default"]
    return defaults

def main():
    parser = argparse.ArgumentParser(
        description="Generatore parametrico 3MF per Snapmaker U1",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--json", type=str, help="Percorso di un file JSON di parametri")
    parser.add_argument("--text", type=str, help="Testo personalizzato")
    parser.add_argument("--font", type=str, help="Nome font (Arial, Impact, Segoe UI, Segoe Script, Georgia, Consolas)")
    parser.add_argument("--size", type=float, help="Dimensione font in mm")
    parser.add_argument("--style", type=str, choices=["rectangle", "contour"], help="Stile base")
    parser.add_argument("--mode", type=str, choices=["embossed", "debossed", "flush"], help="Lavorazione testo")
    parser.add_argument("--base-extruder", type=int, choices=[0, 1, 2, 3], help="Estrusore base (0=T0, 1=T1, 2=T2, 3=T3)")
    parser.add_argument("--text-extruder", type=int, choices=[0, 1, 2, 3], help="Estrusore testo (0=T0, 1=T1, 2=T2, 3=T3)")
    parser.add_argument("--no-hole", action="store_true", help="Disabilita il foro portachiavi (crea una targhetta)")
    parser.add_argument("--out", type=str, help="Percorso del file 3MF in uscita")

    args = parser.parse_args()

    params = load_default_params()

    # Se fornito file JSON, sovrascrivi parametri
    if args.json:
        json_path = Path(args.json)
        if not json_path.exists():
            print(f"Errore: File JSON non trovato: {json_path}")
            sys.exit(1)
        with open(json_path, "r", encoding="utf-8") as f:
            user_json = json.load(f)
            params.update(user_json)

    # Flag CLI hanno priorità su JSON
    if args.text is not None: params["text"] = args.text
    if args.font is not None: params["font_family"] = args.font
    if args.size is not None: params["font_size"] = args.size
    if args.style is not None: params["base_style"] = args.style
    if args.mode is not None: params["text_mode"] = args.mode
    if args.base_extruder is not None: params["extruder_base"] = args.base_extruder
    if args.text_extruder is not None: params["extruder_text"] = args.text_extruder
    if args.no_hole: params["hole_enabled"] = False

    text_clean = "".join(c for c in params["text"] if c.isalnum() or c in " _-").strip() or "Keychain"
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = PROJECT_ROOT / f"{text_clean}_Keychain_U1.3mf"

    print(f"==================================================")
    print(f"  SNAPMAKER U1 PARAMETRIC GENERATOR")
    print(f"==================================================")
    print(f"  Testo:         '{params['text']}'")
    print(f"  Font:          {params.get('font_family', 'Arial')}")
    print(f"  Dimensione:    {params.get('font_size')} mm")
    print(f"  Stile Base:    {params.get('base_style')}")
    print(f"  Modalità:      {params.get('text_mode')}")
    print(f"  Foro anello:   {'Attivo (' + params.get('hole_position') + ')' if params.get('hole_enabled') else 'Disattivato (Targhetta)'}")
    print(f"  Assegnazione:  Base -> T{params.get('extruder_base')}, Testo -> T{params.get('extruder_text')}")
    print(f"--------------------------------------------------")

    print("[1/2] Calcolo geometria solida manifold...")
    parts = generate_keychain_parts(params)
    for p in parts:
        print(f"      - {p.name}: {len(p.mesh.vertices)} vertici, {len(p.mesh.faces)} triangoli (Assegnato a T{p.extruder})")

    print("[2/2] Compilazione pacchetto 3MF per Snapmaker Orca...")
    packager = Snapmaker3MFPackager(
        project_name=f"{text_clean}_Keychain",
        filament_colors=params.get("filament_colors"),
        enable_prime_tower=False,
        enable_support=False
    )
    
    # Riferimento profilo da Chernabog se presente
    ref_3mf = PROJECT_ROOT / "PROGETTI DEFINITIVI" / "Chernabog" / "Chernabog_U1_BICOLORE_NERO_GIALLO.3mf"
    packager.export(parts, str(out_path), reference_config_path=str(ref_3mf) if ref_3mf.exists() else None)

    print(f"--------------------------------------------------")
    print(f"[OK] File 3MF generato con successo:")
    print(f"  {out_path.resolve()}")
    print(f"  Dimensione file: {out_path.stat().st_size:,} bytes")
    print(f"==================================================")

if __name__ == "__main__":
    main()

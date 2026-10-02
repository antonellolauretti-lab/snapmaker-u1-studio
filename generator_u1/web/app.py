import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from matplotlib.font_manager import FontProperties

# Aggiungi cartella root del progetto a sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generator_u1.generators.keychain_generator import generate_keychain_parts
from generator_u1.generators.desk_sign_generator import generate_desk_sign_parts
from generator_u1.packager.snapmaker_3mf import Snapmaker3MFPackager

app = FastAPI(title="Snapmaker U1 Parametric Studio API")

# Configurazione CORS per deployment online (Vercel, custom domain o local)
allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins_env.strip() == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app" if "*" not in origins else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

@app.get("/api/health")
def healthcheck():
    """Endpoint di healthcheck per Render, Railway e monitoraggio."""
    return {"status": "ok", "service": "snapmaker-u1-parametric-studio", "version": "4.0"}


WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"
FONTS_DIR = WEB_DIR.parent / "fonts"
FONTS_DIR.mkdir(parents=True, exist_ok=True)
FONTS_UPLOAD_DIR = WEB_DIR / "uploads" / "fonts"
FONTS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/fonts", StaticFiles(directory=str(FONTS_DIR)), name="fonts")
app.mount("/uploads/fonts", StaticFiles(directory=str(FONTS_UPLOAD_DIR)), name="uploads_fonts")

CURATED_FONTS = [
    {
        "id": "Anton",
        "name": "Anton",
        "desc": "Massiccio Display Bold",
        "category": "display",
        "family": "'Anton', sans-serif",
        "file": "Anton.ttf",
    },
    {
        "id": "Bebas Neue",
        "name": "Bebas Neue",
        "desc": "Alto e Condensato",
        "category": "display",
        "family": "'Bebas Neue', sans-serif",
        "file": "Bebas_Neue.ttf",
    },
    {
        "id": "Pacifico",
        "name": "Pacifico",
        "desc": "Corsivo Connesso Elegante",
        "category": "script",
        "family": "'Pacifico', cursive",
        "file": "Pacifico.ttf",
    },
    {
        "id": "Lobster",
        "name": "Lobster",
        "desc": "Vintage Bold Script",
        "category": "script",
        "family": "'Lobster', cursive",
        "file": "Lobster.ttf",
    },
    {
        "id": "Bungee",
        "name": "Bungee",
        "desc": "Spesso e Dimensional",
        "category": "display",
        "family": "'Bungee', cursive",
        "file": "Bungee.ttf",
    },
    {
        "id": "Righteous",
        "name": "Righteous",
        "desc": "Retro Futuristico Techno",
        "category": "display",
        "family": "'Righteous', cursive",
        "file": "Righteous.ttf",
    },
    {
        "id": "Bangers",
        "name": "Bangers",
        "desc": "Fumetto Comic Bold",
        "category": "display",
        "family": "'Bangers', cursive",
        "file": "Bangers.ttf",
    },
    {
        "id": "Permanent Marker",
        "name": "Permanent Marker",
        "desc": "Tratto Pennarello Autentico",
        "category": "script",
        "family": "'Permanent Marker', cursive",
        "file": "Permanent_Marker.ttf",
    },
    {
        "id": "Orbitron",
        "name": "Orbitron",
        "desc": "Futuristico Sci-Fi Mecha",
        "category": "display",
        "family": "'Orbitron', sans-serif",
        "file": "Orbitron.ttf",
    },
    {
        "id": "Montserrat",
        "name": "Montserrat",
        "desc": "Geometrico Moderno Bold",
        "category": "sans-serif",
        "family": "'Montserrat', sans-serif",
        "file": "Montserrat.ttf",
    },
    {
        "id": "Poppins",
        "name": "Poppins",
        "desc": "Geometrico Morbido e Pulito",
        "category": "sans-serif",
        "family": "'Poppins', sans-serif",
        "file": "Poppins.ttf",
    },
    {
        "id": "Roboto",
        "name": "Roboto",
        "desc": "Standard Tecnico Bilanciato",
        "category": "sans-serif",
        "family": "'Roboto', sans-serif",
        "file": "Roboto.ttf",
    },
    {
        "id": "Oswald",
        "name": "Oswald",
        "desc": "Display Dinamico",
        "category": "display",
        "family": "'Oswald', sans-serif",
        "file": "Oswald.ttf",
    },
    {
        "id": "Playfair Display",
        "name": "Playfair Display",
        "desc": "Serif Elegante Tradizionale",
        "category": "serif",
        "family": "'Playfair Display', serif",
        "file": "Playfair_Display.ttf",
    },
    {
        "id": "Cinzel",
        "name": "Cinzel",
        "desc": "Classico Romano Scolpito",
        "category": "serif",
        "family": "'Cinzel', serif",
        "file": "Cinzel.ttf",
    },
    {
        "id": "Ubuntu",
        "name": "Ubuntu",
        "desc": "Humanist Moderno",
        "category": "sans-serif",
        "family": "'Ubuntu', sans-serif",
        "file": "Ubuntu.ttf",
    },
    {
        "id": "Arial",
        "name": "Arial",
        "desc": "Sans-Serif Standard",
        "category": "sans-serif",
        "family": "Arial, sans-serif",
    },
    {
        "id": "Arial Black",
        "name": "Arial Black",
        "desc": "Ultra-Spesso Massiccio",
        "category": "sans-serif",
        "family": "'Arial Black', sans-serif",
    },
    {
        "id": "Impact",
        "name": "Impact",
        "desc": "Massiccio Classico",
        "category": "display",
        "family": "Impact, sans-serif",
    },
    {
        "id": "Segoe UI",
        "name": "Segoe UI",
        "desc": "Geometrico Interfaccia",
        "category": "sans-serif",
        "family": "'Segoe UI', sans-serif",
    },
    {
        "id": "Segoe Script",
        "name": "Segoe Script",
        "desc": "Corsivo Continuo Saldato",
        "category": "script",
        "family": "'Segoe Script', cursive",
    },
    {
        "id": "Georgia",
        "name": "Georgia",
        "desc": "Serif Classico",
        "category": "serif",
        "family": "Georgia, serif",
    },
    {
        "id": "Consolas",
        "name": "Consolas",
        "desc": "Monospazio Tecnico",
        "category": "monospace",
        "family": "Consolas, monospace",
    },
]

# Cache in memoria dei font caricati dall'utente
UPLOADED_FONTS: List[Dict[str, Any]] = []

def _resolve_font_path(params: Dict[str, Any], font_key: str = "font_family", path_key: str = "font_path"):
    """Risolve il percorso fisico del font se bundled, caricato o specificato."""
    font_id = (params.get(font_key) or "").strip()
    font_path = params.get(path_key)
    if font_path and os.path.isfile(font_path):
        return font_path

    if not font_id:
        return None

    # 1. Controlla nei font curati bundled
    for cf in CURATED_FONTS:
        if cf["id"] == font_id and "file" in cf:
            candidate = FONTS_DIR / cf["file"]
            if candidate.is_file():
                return str(candidate)

    # 2. Controlla per nome file sanitizzato
    safe_name = font_id.replace(" ", "_") + ".ttf"
    candidate = FONTS_DIR / safe_name
    if candidate.is_file():
        return str(candidate)

    # 3. Cerca tra i font caricati dall'utente
    for uf in UPLOADED_FONTS:
        if uf["id"] == font_id or uf.get("path") == font_id:
            return uf["path"]

    # 4. Controlla se è un file nella cartella uploads
    candidate = FONTS_UPLOAD_DIR / font_id
    if candidate.is_file():
        return str(candidate)

    return None

@app.get("/", response_class=HTMLResponse)
def get_index():
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Template index.html non trovato.")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/fonts")
def list_fonts():
    """Restituisce l'elenco combinato dei font curati con metadati e percorsi completi."""
    all_fonts = []
    for f in CURATED_FONTS:
        entry = dict(f)
        if "file" in f:
            p = FONTS_DIR / f["file"]
            if p.is_file():
                entry["path"] = str(p)
                entry["url"] = f"/fonts/{f['file']}"
        all_fonts.append(entry)

    for uf in UPLOADED_FONTS:
        all_fonts.append({
            "id": uf["id"],
            "name": uf["name"],
            "desc": "Font Personale Caricato",
            "category": "custom",
            "family": f"'{uf['id']}', sans-serif",
            "path": uf["path"],
            "url": f"/uploads/fonts/{Path(uf['path']).name}"
        })
    return all_fonts

try:
    from generator_u1.assets.icons_data import ICONS_LIBRARY
except Exception:
    ICONS_LIBRARY = []

@app.get("/api/icons")
def list_icons():
    """Restituisce l'elenco completo delle icone vettoriali per la UI."""
    return ICONS_LIBRARY

@app.post("/api/fonts/upload")
async def upload_font(file: UploadFile = File(...)):
    """
    Riceve un file .ttf o .otf, lo salva nella cache locale e lo rende
    subito disponibile per la generazione senza installazione nel sistema operativo.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in [".ttf", ".otf"]:
        raise HTTPException(status_code=400, detail="Formato font non supportato. Carica un file .ttf o .otf.")

    safe_filename = Path(file.filename).name
    target_path = FONTS_UPLOAD_DIR / safe_filename

    # Salva il file
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Leggi il nome interno del font tramite FontProperties
    try:
        fp = FontProperties(fname=str(target_path))
        font_display_name = fp.get_name() or target_path.stem
    except Exception:
        font_display_name = target_path.stem

    font_entry = {
        "id": safe_filename,
        "name": f"{font_display_name} (Caricato)",
        "path": str(target_path)
    }

    # Evita duplicati
    existing = [i for i, f in enumerate(UPLOADED_FONTS) if f["id"] == safe_filename]
    if existing:
        UPLOADED_FONTS[existing[0]] = font_entry
    else:
        UPLOADED_FONTS.append(font_entry)

    return {
        "status": "success",
        "font": font_entry
    }

@app.post("/api/preview")
def preview_model(params: Dict[str, Any]):
    """
    Genera rapidamente la geometria manifold ed esporta i dati mesh
    per il rendering 3D in Three.js con allineamento metrico realistico.
    Supporta sia il template 'keychain' che 'desk_sign'.
    """
    generator_type = params.get("generator", "keychain").lower()

    if generator_type == "desk_sign":
        fp1 = _resolve_font_path(params, font_key="font_family_line1", path_key="font_path_line1")
        if fp1:
            params["font_path_line1"] = fp1
        fp2 = _resolve_font_path(params, font_key="font_family_line2", path_key="font_path_line2")
        if fp2:
            params["font_path_line2"] = fp2

        try:
            parts = generate_desk_sign_parts(params)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Errore generazione targhetta: {str(e)}")
    else:
        font_path = _resolve_font_path(params, font_key="font_family", path_key="font_path")
        if font_path:
            params["font_path"] = font_path

        try:
            parts = generate_keychain_parts(params)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Errore generazione portachiavi: {str(e)}")

    preview_parts = []
    all_vertices = []

    for part in parts:
        v = part.mesh.vertices.astype(float)
        f = part.mesh.faces.astype(int)
        all_vertices.append(v)

        preview_parts.append({
            "name": part.name,
            "extruder": part.extruder,
            "vertices": v.flatten().tolist(),
            "faces": f.flatten().tolist(),
            "vertex_count": len(v),
            "face_count": len(f)
        })

    stacked_v = np.vstack(all_vertices)
    min_b = stacked_v.min(axis=0)
    max_b = stacked_v.max(axis=0)
    dim = max_b - min_b

    return {
        "status": "success",
        "parts": preview_parts,
        "bounds": {
            "min": min_b.tolist(),
            "max": max_b.tolist()
        },
        "dimensions": {
            "width": round(float(dim[0]), 2),
            "height": round(float(dim[1]), 2),
            "depth": round(float(dim[2]), 2)
        }
    }

@app.post("/api/generate")
def generate_3mf(params: Dict[str, Any]):
    """
    Compila il pacchetto .3MF nativo multi-volume per Snapmaker U1
    e lo invia direttamente come allegato scaricabile per Snapmaker Orca.
    """
    generator_type = params.get("generator", "keychain").lower()

    if generator_type == "desk_sign":
        fp1 = _resolve_font_path(params, font_key="font_family_line1", path_key="font_path_line1")
        if fp1:
            params["font_path_line1"] = fp1
        fp2 = _resolve_font_path(params, font_key="font_family_line2", path_key="font_path_line2")
        if fp2:
            params["font_path_line2"] = fp2

        try:
            parts = generate_desk_sign_parts(params)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Errore geometrico: {str(e)}")

        text = params.get("text_line1", "DeskSign").strip()
        clean_name = "".join(c for c in text if c.isalnum() or c in " _-").strip() or "DeskSign"
        filename = f"{clean_name}_DeskSign_Snapmaker_U1.3mf"
        proj_name = f"{clean_name}_DeskSign"
    else:
        font_path = _resolve_font_path(params, font_key="font_family", path_key="font_path")
        if font_path:
            params["font_path"] = font_path

        try:
            parts = generate_keychain_parts(params)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Errore geometrico: {str(e)}")

        text = params.get("text", "Model").strip()
        clean_name = "".join(c for c in text if c.isalnum() or c in " _-").strip() or "Keychain"
        filename = f"{clean_name}_Keychain_Snapmaker_U1.3mf"
        proj_name = f"{clean_name}_Keychain"

    temp_dir = Path(tempfile.gettempdir())
    out_path = temp_dir / filename

    packager = Snapmaker3MFPackager(
        project_name=proj_name,
        filament_colors=params.get("filament_colors"),
        enable_prime_tower=False,
        enable_support=False,
        enable_brim=False
    )

    ref_3mf = PROJECT_ROOT / "PROGETTI DEFINITIVI" / "67_mechanism_complete_bicolor_V2" / "67_mechanism_U1_P2_ROSSO.3mf"
    default_profile = PROJECT_ROOT / "generator_u1" / "packager" / "profiles" / "snapmaker_u1_default_project.json"
    ref_path = str(ref_3mf) if ref_3mf.exists() else (str(default_profile) if default_profile.exists() else None)
    packager.export(parts, str(out_path), reference_config_path=ref_path)

    return FileResponse(
        path=str(out_path),
        filename=filename,
        media_type="application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

import os
import sys
import tempfile
import shutil
import json
import re
import ipaddress
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, Depends, Header, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from matplotlib.font_manager import FontProperties

# Aggiungi cartella root del progetto a sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Caricamento variabili d'ambiente (.env)
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from generator_u1.generators.keychain_generator import generate_keychain_parts
from generator_u1.generators.desk_sign_generator import generate_desk_sign_parts
from generator_u1.packager.snapmaker_3mf import Snapmaker3MFPackager
from ecommerce.api_router import router as ecommerce_router, verify_admin_auth

app = FastAPI(title="Snapmaker U1 Parametric Studio API")
app.include_router(ecommerce_router)

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

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Aggiunge header difensivi HTTP a tutte le risposte per prevenire clickjacking, MIME sniffing e XSS."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

@app.get("/api/health")
def healthcheck():
    """Endpoint di healthcheck per Render, Railway e monitoraggio."""
    return {"status": "ok", "service": "snapmaker-u1-parametric-studio", "version": "4.0"}


from generator_u1.packager.snapmaker_3mf import Snapmaker3MFPackager, PartItem
from generator_u1.generators.keychain_generator import generate_keychain_parts
from generator_u1.generators.desk_sign_generator import generate_desk_sign_parts
from generator_u1.font_resolver import resolve_font_path, ASSETS_FONTS_DIR, FONTS_DIR

WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"
FONTS_UPLOAD_DIR = WEB_DIR / "uploads" / "fonts"
FONTS_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ECOMMERCE_DIR = PROJECT_ROOT / "ecommerce"

def _is_safe_font_path(p: Path) -> bool:
    """Verifica che il percorso del file risieda rigorosamente nelle directory dei font autorizzate."""
    try:
        resolved = p.resolve()
        allowed_dirs = [
            FONTS_UPLOAD_DIR.resolve(),
            FONTS_DIR.resolve(),
            ASSETS_FONTS_DIR.resolve() if ASSETS_FONTS_DIR.is_dir() else FONTS_DIR.resolve()
        ]
        return any(resolved == d or resolved.is_relative_to(d) for d in allowed_dirs)
    except Exception:
        return False

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/fonts", StaticFiles(directory=str(ASSETS_FONTS_DIR if ASSETS_FONTS_DIR.is_dir() else FONTS_DIR)), name="fonts")
app.mount("/uploads/fonts", StaticFiles(directory=str(FONTS_UPLOAD_DIR)), name="uploads_fonts")
app.mount("/ecommerce", StaticFiles(directory=str(ECOMMERCE_DIR)), name="ecommerce")

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
        "name": "Montserrat Black",
        "desc": "Geometrico Moderno Black 900",
        "category": "sans-serif",
        "family": "'Montserrat', sans-serif",
        "file": "Montserrat-Black.ttf",
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
        "name": "Playfair Display Bold",
        "desc": "Serif Elegante Bold 700",
        "category": "serif",
        "family": "'Playfair Display', serif",
        "file": "PlayfairDisplay-Bold.ttf",
    },
    {
        "id": "Cinzel",
        "name": "Cinzel Bold",
        "desc": "Classico Romano Scolpito Bold 700",
        "category": "serif",
        "family": "'Cinzel', serif",
        "file": "Cinzel-Bold.ttf",
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
        "id": "Dancing Script",
        "name": "Dancing Script",
        "desc": "Corsivo Elegante Fluido",
        "category": "script",
        "family": "'Dancing Script', cursive",
        "file": "DancingScript-Bold.ttf",
    },
    {
        "id": "Caveat",
        "name": "Caveat",
        "desc": "Corsivo Scrittura a Mano",
        "category": "script",
        "family": "'Caveat', cursive",
        "file": "Caveat-Bold.ttf",
    },
    {
        "id": "Great Vibes",
        "name": "Great Vibes",
        "desc": "Calligrafico Tradizionale",
        "category": "script",
        "family": "'Great Vibes', cursive",
        "file": "GreatVibes-Regular.ttf",
    },
    {
        "id": "Segoe Script",
        "name": "Segoe Script",
        "desc": "Corsivo Continuo Saldato",
        "category": "script",
        "family": "'Dancing Script', 'Segoe Script', cursive",
        "file": "DancingScript-Bold.ttf",
    },
    {
        "id": "Impact",
        "name": "Impact",
        "desc": "Massiccio Classico",
        "category": "display",
        "family": "Impact, 'Anton', sans-serif",
        "file": "Impact.ttf",
    },
    {
        "id": "Arial Black",
        "name": "Arial Black",
        "desc": "Ultra-Spesso Massiccio",
        "category": "sans-serif",
        "family": "'Arial Black', 'Anton', sans-serif",
        "file": "Anton.ttf",
    },
    {
        "id": "Segoe UI",
        "name": "Segoe UI",
        "desc": "Geometrico Interfaccia Bold",
        "category": "sans-serif",
        "family": "'Segoe UI', 'Montserrat', sans-serif",
        "file": "Montserrat-Black.ttf",
    },
    {
        "id": "Georgia",
        "name": "Georgia",
        "desc": "Serif Classico Bold",
        "category": "serif",
        "family": "Georgia, 'Playfair Display', serif",
        "file": "PlayfairDisplay-Bold.ttf",
    },
    {
        "id": "Consolas",
        "name": "Consolas",
        "desc": "Monospazio Tecnico",
        "category": "monospace",
        "family": "Consolas, 'Ubuntu', monospace",
        "file": "Ubuntu.ttf",
    },
    {
        "id": "Arial",
        "name": "Arial",
        "desc": "Sans-Serif Standard",
        "category": "sans-serif",
        "family": "Arial, 'Roboto', sans-serif",
        "file": "Roboto.ttf",
    },
]

# Cache in memoria dei font caricati dall'utente
UPLOADED_FONTS: List[Dict[str, Any]] = []

def _resolve_font_path(params: Dict[str, Any], font_key: str = "font_family", path_key: str = "font_path"):
    """Risolve il percorso fisico del font se bundled, caricato o specificato in modo sicuro."""
    font_id = (params.get(font_key) or "").strip()
    raw_font_path = params.get(path_key)
    if raw_font_path:
        p = Path(raw_font_path)
        if p.is_file() and _is_safe_font_path(p):
            return str(p.resolve())

    if not font_id:
        return None

    safe_font_id = Path(font_id).name

    # 1. Cerca tra i font caricati dall'utente
    for uf in UPLOADED_FONTS:
        if uf["id"] == font_id or uf["id"] == safe_font_id:
            p = Path(uf["path"])
            if p.is_file() and _is_safe_font_path(p):
                return str(p.resolve())

    # 2. Controlla nella cartella uploads
    candidate = (FONTS_UPLOAD_DIR / safe_font_id).resolve()
    if candidate.is_file() and _is_safe_font_path(candidate):
        return str(candidate)

    # 3. Risoluzione centralizzata tramite font_resolver (assets/fonts o fonts)
    safe_explicit = raw_font_path if (raw_font_path and _is_safe_font_path(Path(raw_font_path))) else None
    resolved = resolve_font_path(safe_font_id, explicit_path=safe_explicit)
    if resolved and _is_safe_font_path(Path(resolved)):
        return resolved

    return None

STOREFRONT_HTML = ECOMMERCE_DIR / "frontend" / "index.html"
STUDIO_HTML = TEMPLATES_DIR / "index.html"
ADMIN_HTML = ECOMMERCE_DIR / "admin" / "index.html"

@app.get("/", response_class=FileResponse)
@app.get("/index.html", response_class=FileResponse)
async def serve_storefront():
    """Homepage pubblica Storefront E-Commerce (cliente finale)."""
    if not STOREFRONT_HTML.is_file():
        raise HTTPException(status_code=404, detail="Storefront index.html non trovato.")
    return FileResponse(str(STOREFRONT_HTML), media_type="text/html")

@app.get("/manifest.json", response_class=FileResponse)
async def serve_manifest():
    """Manifest PWA accessibile direttamente alla radice."""
    manifest_p = STATIC_DIR / "manifest.json"
    if manifest_p.is_file():
        return FileResponse(str(manifest_p), media_type="application/manifest+json")
    raise HTTPException(status_code=404, detail="Manifest non trovato.")

@app.get("/sw.js", response_class=FileResponse)
async def serve_service_worker():
    """Service worker PWA accessibile alla radice per scope globale."""
    sw_p = STATIC_DIR / "sw.js"
    if sw_p.is_file():
        return FileResponse(str(sw_p), media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Service worker non trovato.")

@app.get("/apple-touch-icon.png", response_class=FileResponse)
@app.get("/apple-touch-icon-precomposed.png", response_class=FileResponse)
async def serve_apple_touch_icon():
    """Icona Apple Touch per iOS Home Screen."""
    icon_p = STATIC_DIR / "icons" / "apple-touch-icon.png"
    if icon_p.is_file():
        return FileResponse(str(icon_p), media_type="image/png")
    raise HTTPException(status_code=404, detail="Icona non trovata.")

@app.get("/favicon.ico", response_class=FileResponse)
@app.get("/favicon.png", response_class=FileResponse)
async def serve_favicon():
    """Favicon per browser desktop e mobile."""
    fav_p = STATIC_DIR / "icons" / "favicon.png"
    if fav_p.is_file():
        return FileResponse(str(fav_p), media_type="image/png")
    raise HTTPException(status_code=404, detail="Favicon non trovata.")

@app.get("/studio", response_class=FileResponse)
@app.get("/studio/", response_class=FileResponse)
async def serve_studio():
    """Studio parametrico 3D tecnico avanzato (per uso interno e test geometrici)."""
    if not STUDIO_HTML.is_file():
        raise HTTPException(status_code=404, detail="Studio 3D template index.html non trovato.")
    return FileResponse(str(STUDIO_HTML), media_type="text/html")

@app.get("/admin", response_class=FileResponse)
@app.get("/admin/", response_class=FileResponse)
async def serve_admin():
    """Pannello gestionale ordini e inventario filamenti Snapmaker."""
    if not ADMIN_HTML.is_file():
        raise HTTPException(status_code=404, detail="Pannello admin non trovato.")
    return FileResponse(str(ADMIN_HTML), media_type="text/html")

@app.post("/admin/verify-pin")
@app.get("/admin/verify-pin")
async def handle_verify_pin_direct(
    request: Request,
    payload: Optional[Dict[str, Any]] = None,
    x_admin_pin: Optional[str] = Header(None),
    pin: Optional[str] = Query(None)
):
    """Verifica PIN accessibile anche senza prefisso /api."""
    from ecommerce.api_router import api_verify_pin
    return await api_verify_pin(request=request, payload=payload, x_admin_pin=x_admin_pin, pin=pin)

@app.post("/api/store/orders/create-test")
@app.post("/store/orders/create-test")
def handle_create_test_order(payload: Dict[str, Any], request: Request):
    """Endpoint diretto per ordini di prova (test rapido senza pagamento)."""
    from ecommerce.api_router import api_create_test_order
    return api_create_test_order(payload, request=request)

@app.post("/api/orders/create-paypal-order")
@app.post("/orders/create-paypal-order")
def handle_create_paypal_order_alias(payload: Dict[str, Any], request: Request):
    """Alias diretto per creazione ordine PayPal."""
    from ecommerce.api_router import api_create_paypal_order
    return api_create_paypal_order(payload, request=request)

@app.post("/api/orders/capture-paypal-order")
@app.post("/orders/capture-paypal-order")
def handle_capture_paypal_order_alias(payload: Dict[str, Any], request: Request):
    """Alias diretto per cattura ordine PayPal."""
    from ecommerce.api_router import api_capture_paypal_order
    return api_capture_paypal_order(payload, request=request)

@app.get("/api/admin/items/{item_id}/download-3mf")
@app.get("/admin/items/{item_id}/download-3mf")
async def download_order_item_3mf(item_id: str, auth: bool = Depends(verify_admin_auth)):
    """Endpoint protetto per download del pacchetto 3MF per Snapmaker U1."""
    from ecommerce.api_router import api_download_order_item_3mf
    return await api_download_order_item_3mf(item_id=item_id, auth=auth)

@app.get("/api/fonts")
def list_fonts():
    """Restituisce l'elenco combinato dei font curati con metadati e percorsi completi."""
    all_fonts = []
    for f in CURATED_FONTS:
        entry = dict(f)
        resolved_p = resolve_font_path(f.get("file", f["id"]))
        if resolved_p and os.path.isfile(resolved_p):
            entry["path"] = resolved_p
            entry["url"] = f"/fonts/{Path(resolved_p).name}"
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

MAX_FONT_FILE_SIZE = 10 * 1024 * 1024  # 10 MB massimo

@app.post("/api/fonts/upload")
async def upload_font(file: UploadFile = File(...)):
    """
    Riceve un file .ttf o .otf, verifica la dimensione (max 10MB) e il nome sicuro,
    lo salva nella cache locale e lo rende subito disponibile.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome file mancante.")

    ext = Path(file.filename).suffix.lower()
    if ext not in [".ttf", ".otf"]:
        raise HTTPException(status_code=400, detail="Formato font non supportato. Carica un file .ttf o .otf.")

    raw_name = Path(file.filename).name
    clean_stem = re.sub(r"[^a-zA-Z0-9_\-]", "_", Path(raw_name).stem)[:50]
    safe_filename = f"{clean_stem}{ext}"
    target_path = (FONTS_UPLOAD_DIR / safe_filename).resolve()

    if not _is_safe_font_path(target_path):
        raise HTTPException(status_code=400, detail="Nome file font non valido o non autorizzato.")

    content = await file.read()
    if len(content) > MAX_FONT_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File troppo grande. Il limite massimo per i font è 10MB.")

    with open(target_path, "wb") as buffer:
        buffer.write(content)

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
        if params.get("line2_enabled"):
            fp2 = _resolve_font_path(params, font_key="font_family_line2", path_key="font_path_line2")
            if fp2:
                params["font_path_line2"] = fp2

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
        if params.get("line2_enabled"):
            fp2 = _resolve_font_path(params, font_key="font_family_line2", path_key="font_path_line2")
            if fp2:
                params["font_path_line2"] = fp2

        try:
            parts = generate_keychain_parts(params)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Errore geometrico: {str(e)}")

        text = params.get("text", "Model").strip()
        clean_name = "".join(c for c in text if c.isalnum() or c in " _-").strip() or "Keychain"
        if params.get("line2_enabled") and params.get("text_line2"):
            clean_t2 = "".join(c for c in params.get("text_line2") if c.isalnum() or c in " _-").strip()
            if clean_t2:
                clean_name = f"{clean_name}_{clean_t2}"
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
    
    thumbnail_b64 = params.get("thumbnail_base64")
    packager.export(parts, str(out_path), reference_config_path=ref_path, thumbnail_base64=thumbnail_b64)

    return FileResponse(
        path=str(out_path),
        filename=filename,
        media_type="application/vnd.ms-package.3dmanufacturing-3dmodel+xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ==============================================================================
# SINCRONIZZAZIONE PALETTE DA SNAPMAKER U1 LOCALE (RFID / COLORI REALI)
# ==============================================================================

NAMED_COLORS_MAP = {
    "black": "#080A0D", "nero": "#080A0D",
    "white": "#D9DFE5", "bianco": "#D9DFE5", "cool white": "#D9DFE5", "pearl white": "#E2DEDB",
    "red": "#E72F1D", "rosso": "#E72F1D",
    "yellow": "#F8F81C", "giallo": "#F8F81C", "bright yellow": "#F8F81C",
    "blue": "#003776", "blu": "#003776",
    "green": "#2D9E59", "verde": "#2D9E59",
    "orange": "#F97429", "arancione": "#F97429",
    "magenta": "#F24574",
    "grey": "#C4C7D9", "gray": "#C4C7D9", "grigio": "#C4C7D9",
    "silver": "#C4C7D9", "argento": "#C4C7D9",
    "gold": "#D9A63A", "oro": "#D9A63A",
    "purple": "#9675CD", "viola": "#9675CD",
    "pink": "#E68FBD", "rosa": "#E68FBD",
    "cyan": "#44ADE5", "ciano": "#44ADE5",
}

def _parse_snapmaker_palette_data(data: Any) -> Tuple[List[str], List[str]]:
    """
    Estrae fino a 4 colori esadecimali e nomi materiale da un payload Snapmaker/Moonraker.
    """
    default_colors = ["#080A0D", "#D9DFE5", "#E72F1D", "#F8F81C"]
    default_materials = ["PLA Slot 1", "PLA Slot 2", "PLA Slot 3", "PLA Slot 4"]
    found_colors: List[str] = []
    found_materials: List[str] = []

    def normalize_color(val: Any) -> Optional[str]:
        if not val:
            return None
        s = str(val).strip()
        if s.lower() in NAMED_COLORS_MAP:
            return NAMED_COLORS_MAP[s.lower()]
        s_clean = s.lstrip('#')
        if len(s_clean) == 8:
            s_clean = s_clean[:6]
        if len(s_clean) == 6 and all(c in '0123456789abcdefABCDEF' for c in s_clean):
            return f"#{s_clean.lower()}"
        return None

    # 1. Ricerca strutturata in array comuni (filaments, slots, spools, trays, extruders)
    candidates = []
    if isinstance(data, dict):
        for key in ["filaments", "filament_info", "slots", "trays", "spools", "materials", "tools"]:
            if key in data and isinstance(data[key], list):
                candidates = data[key]
                break
        if not candidates and "data" in data and isinstance(data["data"], dict):
            for key in ["filaments", "filament_info", "slots", "trays", "spools"]:
                if key in data["data"] and isinstance(data["data"][key], list):
                    candidates = data["data"][key]
                    break
        if not candidates and "result" in data and isinstance(data["result"], dict):
            status = data["result"].get("status", {})
            for key in ["filaments", "slots", "spools"]:
                if key in status and isinstance(status[key], list):
                    candidates = status[key]
                    break

    if candidates and isinstance(candidates, list):
        for item in candidates[:4]:
            col = None
            mat = None
            if isinstance(item, dict):
                for col_key in ["color", "tray_color", "filament_color", "hex"]:
                    if col_key in item:
                        col = normalize_color(item[col_key])
                        if col:
                            break
                for mat_key in ["material", "name", "type", "filament_type"]:
                    if mat_key in item and item[mat_key]:
                        mat = str(item[mat_key]).strip()
                        break
            elif isinstance(item, str):
                col = normalize_color(item)

            if col:
                found_colors.append(col)
                found_materials.append(mat or f"Slot {len(found_colors)}")

    # 2. Se non abbiamo trovato abbastanza colori, scansiona ricorsivamente
    if len(found_colors) < 4:
        def scan_for_colors(obj):
            if isinstance(obj, dict):
                for v in obj.values():
                    scan_for_colors(v)
            elif isinstance(obj, list):
                for v in obj:
                    scan_for_colors(v)
            elif isinstance(obj, str):
                c = normalize_color(obj)
                if c and c not in found_colors and len(found_colors) < 4:
                    found_colors.append(c)
                    found_materials.append(f"Slot {len(found_colors)}")

        scan_for_colors(data)

    # 3. Completa fino a 4 slot con i colori e materiali standard U1
    final_colors = []
    final_materials = []
    for i in range(4):
        if i < len(found_colors):
            final_colors.append(found_colors[i])
            final_materials.append(found_materials[i] if i < len(found_materials) else default_materials[i])
        else:
            final_colors.append(default_colors[i])
            final_materials.append(default_materials[i])

    return final_colors, final_materials


@app.post("/api/printer/sync")
def sync_printer_palette(payload: Dict[str, Any]):
    """
    Interroga la Snapmaker U1 locale sulla rete LAN (tramite Moonraker / Snapmaker Luban / RFID)
    per recuperare in tempo reale i colori dei filamenti e materiali correntemente caricati nei 4 estrusori.
    """
    raw_ip = payload.get("ip", "").strip()
    try:
        port = int(payload.get("port") or 8080)
    except (ValueError, TypeError):
        port = 8080
    token = payload.get("token", "").strip() or None

    if not raw_ip:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": "Inserisci un indirizzo IP valido per la Snapmaker U1."}
        )

    # Pulisci prefissi protocollo ed eventuali porte annidate
    clean_ip = raw_ip.replace("http://", "").replace("https://", "").strip().rstrip("/")
    if ":" in clean_ip:
        parts = clean_ip.split(":")
        clean_ip = parts[0]
        try:
            port = int(parts[1])
        except (ValueError, IndexError):
            pass

    try:
        ip_obj = ipaddress.ip_address(clean_ip)
    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": f"L'indirizzo IP '{clean_ip}' non è valido."}
        )

    # Protezione SSRF: blocca indirizzi link-local (169.254.x.x, cloud metadata) e multicast
    if ip_obj.is_link_local or ip_obj.is_multicast:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "detail": "Indirizzo IP non consentito."}
        )

    # Rilevamento ambiente cloud (Render, Vercel, Railway) vs locale
    is_cloud_env = bool(os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("VERCEL"))
    if is_cloud_env:
        return JSONResponse(
            status_code=200,
            content={
                "status": "info",
                "detail": f"La sincronizzazione LAN diretta con la stampante non è disponibile nell'ambiente cloud ospitato (la macchina è nella tua rete locale {clean_ip}). Avvia l'app in locale oppure seleziona i filamenti manualmente."
            }
        )

    # Sequenza di porte ed endpoint da interrogare
    ports_to_try = [port]
    for fallback_p in [8080, 80, 7125, 8888]:
        if fallback_p not in ports_to_try:
            ports_to_try.append(fallback_p)

    headers = {
        "User-Agent": "Snapmaker-U1-Parametric-Studio/4.5",
        "Accept": "application/json"
    }
    if token:
        headers["Snapmaker-Token"] = token
        headers["Authorization"] = f"Bearer {token}"

    endpoints = [
        "/filament/data",
        "/filament/status",
        "/api/v1/filament",
        "/api/v1/status",
        "/printer/objects/query?toolhead&extruder&extruder1&extruder2&extruder3&save_variables",
        "/server/spoolman/spool_id",
        "/api/printer"
    ]

    last_error = None
    printer_data = None

    for p in ports_to_try:
        for ep in endpoints:
            url = f"http://{clean_ip}:{p}{ep}"
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=2.2) as resp:
                    if resp.status == 200:
                        raw_body = resp.read().decode("utf-8", errors="ignore")
                        try:
                            printer_data = json.loads(raw_body)
                            break
                        except Exception:
                            continue
            except (urllib.error.URLError, TimeoutError, OSError) as err:
                last_error = str(err)
                continue
        if printer_data:
            break

    if not printer_data:
        err_msg = last_error or "Nessuna risposta ricevuta dalla macchina"
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "detail": f"Impossibile raggiungere la Snapmaker U1 all'indirizzo {clean_ip}. Verifica che la macchina sia accesa e collegata alla rete Wi-Fi. (Dettaglio: {err_msg})"
            }
        )

    colors, materials = _parse_snapmaker_palette_data(printer_data)

    return {
        "status": "success",
        "ip": clean_ip,
        "colors": colors,
        "materials": materials,
        "message": f"Sincronizzati con successo i 4 estrusori dalla Snapmaker U1 ({clean_ip})"
    }


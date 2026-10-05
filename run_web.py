import os
import sys
import uvicorn
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

def start_server():
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("ENVIRONMENT") == "production" else "127.0.0.1")
    reload = os.environ.get("ENVIRONMENT", "development") != "production"

    print("=" * 60)
    print("  GADGETPOINT.IT - 3D PARAMETRIC STUDIO")
    print("=" * 60)
    print(f"  Server Web attivo su: http://{host}:{port}")
    print("=" * 60)
    print("  Premi Ctrl+C per arrestare il server.")
    print("-" * 60)
    uvicorn.run("generator_u1.web.app:app", host=host, port=port, reload=reload)

if __name__ == "__main__":
    start_server()

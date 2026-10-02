import sys
import uvicorn
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def start_server():
    print("=" * 60)
    print("  SNAPMAKER U1 - 3D PARAMETRIC STUDIO")
    print("=" * 60)
    print("  Server Web attivo in locale su:")
    print("  👉 http://localhost:8000")
    print("=" * 60)
    print("  Premi Ctrl+C per arrestare il server.")
    print("-" * 60)
    uvicorn.run("generator_u1.web.app:app", host="127.0.0.1", port=8000, reload=False)

if __name__ == "__main__":
    start_server()

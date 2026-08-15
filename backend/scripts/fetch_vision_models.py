#!/usr/bin/env python3
"""
Descarga los modelos que el Boost 1 (cámara real) necesita para funcionar
SIN INTERNET durante la feria.

Por defecto baja BlazeFace, el detector de ROSTROS que usa la demo: pesa
menos de 1 MB. Con --all baja además los detectores de cuerpo COCO-SSD
(~83 MB), que quedan como plan B.

Los pesos no viven en el repositorio: se bajan una vez y quedan en
backend/static/vendor/models/ (ignorado por git).

Uso:
    python3 backend/scripts/fetch_vision_models.py            # rostros (lo que usa la feria)
    python3 backend/scripts/fetch_vision_models.py --all      # + los de cuerpo (plan B)
    python3 backend/scripts/fetch_vision_models.py --check    # verifica sin descargar

⚠️  Ejecutar CON internet, antes del día de la feria.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://storage.googleapis.com/tfjs-models/savedmodel"

# nombre local  ->  URL base remota.
# BlazeFace no vive en el bucket de savedmodel sino en TFHub, y ahí el
# manifiesto y los shards se piden con ?tfjs-format=file.
MODELS = {
    "coco-ssd":      f"{BASE_URL}/ssd_mobilenet_v2",       # cuerpos (~65 MB), plan B
    "coco-ssd-lite": f"{BASE_URL}/ssdlite_mobilenet_v2",   # lite (~18 MB)
    "blazeface":     "https://tfhub.dev/tensorflow/tfjs-model/blazeface/1/default/1",
}

# El detector de rostros es el que usa la feria. Pesa menos de 1 MB, así
# que descargarlo siempre sale gratis.
DEFAULT_MODELS = ["blazeface"]

# Modelos que se piden con el sufijo de TFHub
TFHUB = {"blazeface"}

VENDOR_DIR = Path(__file__).resolve().parents[1] / "static" / "vendor" / "models"


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=120) as resp:
        return resp.read()


def download_model(local_name: str, remote: str) -> None:
    dest = VENDOR_DIR / local_name
    dest.mkdir(parents=True, exist_ok=True)
    suffix = "?tfjs-format=file" if local_name in TFHUB else ""

    print(f"\n▶ {local_name}  ←  {remote}")

    manifest_path = dest / "model.json"
    print("  · model.json …", end="", flush=True)
    manifest_bytes = fetch(f"{remote}/model.json{suffix}")
    manifest_path.write_bytes(manifest_bytes)
    print(f" {len(manifest_bytes) / 1024:.0f} KB")

    manifest = json.loads(manifest_bytes)
    shards = [p for group in manifest["weightsManifest"] for p in group["paths"]]

    total = 0
    for i, shard in enumerate(shards, 1):
        print(f"  · {shard}  ({i}/{len(shards)}) …", end="", flush=True)
        data = fetch(f"{remote}/{shard}{suffix}")
        (dest / shard).write_bytes(data)
        total += len(data)
        print(f" {len(data) / 1024 / 1024:.1f} MB")

    print(f"  ✓ {local_name}: {len(shards)} shards, {total / 1024 / 1024:.0f} MB en {dest}")


def check_model(local_name: str) -> bool:
    """True si el modelo está completo en disco (todos los shards del manifiesto)."""
    dest = VENDOR_DIR / local_name
    manifest_path = dest / "model.json"
    if not manifest_path.is_file():
        print(f"  ✗ {local_name}: falta model.json")
        return False
    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        print(f"  ✗ {local_name}: model.json corrupto")
        return False

    shards = [p for group in manifest["weightsManifest"] for p in group["paths"]]
    missing = [s for s in shards if not (dest / s).is_file()]
    if missing:
        print(f"  ✗ {local_name}: faltan {len(missing)}/{len(shards)} shards")
        return False

    size = sum((dest / s).stat().st_size for s in shards)
    print(f"  ✓ {local_name}: {len(shards)} shards, {size / 1024 / 1024:.0f} MB")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true",
                        help="descarga también los detectores de cuerpo (plan B)")
    parser.add_argument("--check", action="store_true",
                        help="solo verifica lo que ya está en disco")
    args = parser.parse_args()

    wanted = list(MODELS) if args.all else DEFAULT_MODELS

    if args.check:
        print("Verificando modelos en", VENDOR_DIR)
        ok = all(check_model(name) for name in wanted)
        if ok:
            print("\nTodo listo — la cámara real funciona sin internet.")
        else:
            print("\nFaltan pesos. Corré este script sin --check (necesita internet).")
        return 0 if ok else 1

    print("Descargando modelos a", VENDOR_DIR)
    for name in wanted:
        try:
            download_model(name, MODELS[name])
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            print(f"\n✗ Error descargando {name}: {exc}", file=sys.stderr)
            return 1

    print("\nListo. Verificá la carga offline abriendo, con el server corriendo:")
    print("  http://localhost:8000/app/_test_vision.html")
    print("Debe imprimir RESULT: OFFLINE_LOAD_OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

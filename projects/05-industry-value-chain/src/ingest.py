"""Ingest: resolve each Damodaran .xls download link from its datafile HTML
page (robust to the R&D/'&' filename), download into the pinned raw vintage
folder, and record a SHA-256 manifest. Idempotent: an already-hashed file is
not re-downloaded. Local files are used as-is. Failures are logged, not fatal —
the rest of the pipeline still builds from whatever landed.
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from urllib.parse import urljoin

import requests

from . import config

MANIFEST = os.path.join(config.RAW_DIR, "SHA256SUMS")


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_xls_url(page: str) -> str | None:
    """Fetch datafile/<page>.html and return the absolute URL of the .xls link."""
    page_url = urljoin(config.DATAFILE_BASE, page)
    r = requests.get(page_url, headers={"User-Agent": config.USER_AGENT}, timeout=30)
    r.raise_for_status()
    # Prefer a /datasets/ link; else any href ending .xls/.xlsx
    hrefs = re.findall(r'href=["\']([^"\']+\.xlsx?)["\']', r.text, flags=re.IGNORECASE)
    if not hrefs:
        return None
    hrefs.sort(key=lambda h: (0 if "/datasets/" in h.lower() else 1, len(h)))
    return urljoin(page_url, hrefs[0])


def download(url: str, dest: str) -> None:
    r = requests.get(url, headers={"User-Agent": config.USER_AGENT}, timeout=60)
    r.raise_for_status()
    with open(dest, "wb") as fh:
        fh.write(r.content)


def local_filename(ds: dict, url: str) -> str:
    stem = os.path.basename(url.split("?")[0]) or f"{ds['code']}.xls"
    # keep the code prefix so files are self-describing in the raw folder
    return f"{ds['code']}__{stem}"


def run() -> int:
    os.makedirs(config.RAW_DIR, exist_ok=True)
    landed: dict[str, str] = {}
    errors = 0

    for ds in config.DATASETS:
        if ds.get("local"):
            path = os.path.join(config.RAW_DIR, ds["local"])
            if os.path.exists(path):
                landed[ds["code"]] = ds["local"]
                print(f"  [local ] {ds['code']:14s} -> {ds['local']}")
            else:
                print(f"  [MISS  ] {ds['code']:14s} local file not found: {ds['local']}")
                errors += 1
            continue
        if not ds.get("xls") and not ds.get("page"):
            continue
        try:
            # Prefer the explicit canonical /pc/datasets/<stem>.xls URL; the
            # datafile HTML pages mislabel their download links.
            url = urljoin(config.DATASETS_BASE, ds["xls"]) if ds.get("xls") else resolve_xls_url(ds["page"])
            if not url:
                print(f"  [FAIL  ] {ds['code']:14s} no .xls link on {ds['page']}")
                errors += 1
                continue
            dest_name = local_filename(ds, url)
            dest = os.path.join(config.RAW_DIR, dest_name)
            if os.path.exists(dest):
                print(f"  [cached] {ds['code']:14s} -> {dest_name}")
            else:
                download(url, dest)
                print(f"  [get   ] {ds['code']:14s} {url}  -> {dest_name} ({os.path.getsize(dest)} B)")
            landed[ds["code"]] = dest_name
        except Exception as exc:  # noqa: BLE001 - non-fatal by design
            print(f"  [ERROR ] {ds['code']:14s} {exc}")
            errors += 1

    # (re)write the manifest across everything present in the raw folder
    files = sorted(f for f in os.listdir(config.RAW_DIR)
                   if f.lower().endswith((".xls", ".xlsx")))
    with open(MANIFEST, "w") as fh:
        for f in files:
            fh.write(f"{_sha256(os.path.join(config.RAW_DIR, f))}  {f}\n")
    print(f"\nRaw vintage: {config.RAW_DIR}")
    print(f"Files: {len(files)} | manifest: {MANIFEST} | landed: {len(landed)} | errors: {errors}")
    # Save a code->filename map for the parser
    with open(os.path.join(config.RAW_DIR, "_manifest_codes.txt"), "w") as fh:
        for code, name in sorted(landed.items()):
            fh.write(f"{code}\t{name}\n")
    return 0 if errors == 0 else 0  # non-fatal: always succeed so the build continues


if __name__ == "__main__":
    sys.exit(run())

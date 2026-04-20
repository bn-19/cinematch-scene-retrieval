#!/usr/bin/env python3
"""
CineMatch — Remove black/corrupt frames from dataset.

Deletes any scene image under a size threshold (default 15KB),
removes it from metadata.json, and re-ingests.

Usage:
    python cleanup_black_frames.py
    python cleanup_black_frames.py --threshold 20  # KB threshold
    python cleanup_black_frames.py --dry-run       # preview only
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT  = Path(__file__).resolve().parent
SCENES_DIR    = PROJECT_ROOT / "data" / "scenes"
META_PATH     = PROJECT_ROOT / "data" / "metadata.json"
SITE_PACKAGES = "/Users/boaznakhimovsky/Library/Python/3.12/lib/python/site-packages"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=int, default=15,
                        help="Remove frames smaller than this many KB (default: 15)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    threshold_bytes = args.threshold * 1024

    with open(META_PATH) as f:
        records = json.load(f)

    to_remove = []
    for rec in records:
        path = SCENES_DIR / rec["filename"]
        if path.exists() and path.stat().st_size < threshold_bytes:
            to_remove.append(rec)

    if not to_remove:
        print(f"No frames under {args.threshold}KB found — nothing to clean up.")
        return

    print(f"Found {len(to_remove)} black/corrupt frames under {args.threshold}KB:\n")
    for rec in to_remove:
        path = SCENES_DIR / rec["filename"]
        kb = path.stat().st_size / 1024
        print(f"  {rec['filename']:60s}  {kb:.1f} KB  [{rec['source']}]")

    if args.dry_run:
        print("\nDry run — no files deleted.")
        return

    print(f"\nRemoving {len(to_remove)} frames...")
    remove_ids = {r["id"] for r in to_remove}
    for rec in to_remove:
        path = SCENES_DIR / rec["filename"]
        path.unlink(missing_ok=True)
        print(f"  deleted {rec['filename']}")

    clean_records = [r for r in records if r["id"] not in remove_ids]
    with open(META_PATH, "w") as f:
        json.dump(clean_records, f, indent=2, ensure_ascii=False)

    print(f"\nMetadata updated: {len(records)} → {len(clean_records)} scenes")
    print("\nRe-ingesting into ChromaDB...")

    result = subprocess.run(
        ["/Applications/anaconda3/bin/python", "-m", "backend.ingest"],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print("\n[warn] ingest.py exited with an error.")
    else:
        print(f"\nDone — {len(clean_records)} clean scenes in ChromaDB. Restart the server.")

if __name__ == "__main__":
    main()

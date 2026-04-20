#!/usr/bin/env python3
"""
CineMatch — Dataset Population Script

Downloads royalty-free cinematic images for each mood/tone category,
merges them into data/metadata.json, then runs ingest.py so the new
scenes are immediately available for querying.

Primary source : Unsplash Source API (no key required)
                 https://source.unsplash.com/{w}x{h}/?{query}
Fallback source: Lorem Picsum (always reliable)
                 https://picsum.photos/{w}/{h}?random={seed}

Usage:
    python populate_dataset.py           # download + ingest
    python populate_dataset.py --no-ingest   # download only
"""

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
SCENES_DIR   = PROJECT_ROOT / "data" / "scenes"
META_PATH    = PROJECT_ROOT / "data" / "metadata.json"

# ── Config ─────────────────────────────────────────────────────────────────
IMAGES_PER_QUERY  = 3
IMAGE_W, IMAGE_H  = 1280, 800
REQUEST_TIMEOUT   = 20       # seconds
MAX_RETRIES       = 3
RETRY_BACKOFF     = 2.0      # seconds (doubles each retry)
MIN_IMAGE_BYTES   = 10_000   # skip suspiciously small files

UNSPLASH_URL = "https://source.unsplash.com/{w}x{h}/?{query}"
PICSUM_URL   = "https://picsum.photos/{w}/{h}?random={seed}"

# ── Tone catalogue ─────────────────────────────────────────────────────────
# Each entry: slug (used in filename/id), query string, human description,
# and tone tags that will be stored in metadata.json.
QUERIES = [
    {
        "slug":        "dinner_dramatic",
        "query":       "cinematic dinner table dramatic",
        "description": "A dramatically lit dinner table scene suggesting tension or unspoken emotion.",
        "tone_tags":   ["intimate", "dramatic", "warm", "domestic"],
    },
    {
        "slug":        "lone_figure_landscape",
        "query":       "lone figure vast landscape cinematic",
        "description": "A solitary figure dwarfed by a vast open landscape.",
        "tone_tags":   ["wide", "epic", "desolate", "contemplative"],
    },
    {
        "slug":        "dark_alley_noir",
        "query":       "dark alley noir night",
        "description": "A shadowy alleyway at night with hard pools of light — classic noir staging.",
        "tone_tags":   ["dark", "noir", "tense", "urban"],
    },
    {
        "slug":        "sunlit_field_hope",
        "query":       "sunlit field hope cinematic",
        "description": "A bright open field bathed in sunlight evoking hope and freedom.",
        "tone_tags":   ["bright", "hopeful", "wide", "warm"],
    },
    {
        "slug":        "city_street_chaos",
        "query":       "crowded city street chaos",
        "description": "A chaotic crowded city street full of energy and visual noise.",
        "tone_tags":   ["urban", "dynamic", "chaotic", "wide"],
    },
    {
        "slug":        "empty_room_isolation",
        "query":       "empty room isolation cinematic",
        "description": "A bare empty room that communicates loneliness and psychological isolation.",
        "tone_tags":   ["isolated", "claustrophobic", "somber", "minimalist"],
    },
    {
        "slug":        "argument_confrontation",
        "query":       "two people argument confrontation",
        "description": "Two people in a charged confrontation — faces close, bodies tense.",
        "tone_tags":   ["tense", "intimate", "dramatic", "confrontational"],
    },
    {
        "slug":        "hero_silhouette_sunset",
        "query":       "hero silhouette sunset epic",
        "description": "A heroic silhouette backlit by a blazing sunset — iconic wide shot.",
        "tone_tags":   ["epic", "wide", "warm", "triumphant"],
    },
    {
        "slug":        "war_battlefield_smoke",
        "query":       "war battlefield smoke cinematic",
        "description": "A smoke-filled battlefield — grim, chaotic, and visually overwhelming.",
        "tone_tags":   ["dark", "war", "chaotic", "gritty"],
    },
    {
        "slug":        "peaceful_forest_morning",
        "query":       "peaceful forest morning light",
        "description": "A quiet forest in soft morning light — serene and timeless.",
        "tone_tags":   ["peaceful", "ethereal", "bright", "natural"],
    },
    {
        "slug":        "rain_window_melancholy",
        "query":       "rain window melancholy",
        "description": "Rain streaking a window — the classic visual shorthand for melancholy.",
        "tone_tags":   ["melancholy", "intimate", "moody", "atmospheric"],
    },
    {
        "slug":        "celebration_crowd_joyful",
        "query":       "celebration crowd joyful",
        "description": "A crowd in joyful celebration — wide, bright, and full of energy.",
        "tone_tags":   ["joyful", "wide", "bright", "energetic"],
    },
    {
        "slug":        "chase_running_urgency",
        "query":       "chase running urgency cinematic",
        "description": "A figure running at full speed — urgency and kinetic energy in motion.",
        "tone_tags":   ["tense", "action", "dynamic", "urgent"],
    },
    {
        "slug":        "old_man_portrait_dramatic",
        "query":       "old man alone portrait dramatic",
        "description": "A weathered face in dramatic close-up — time, loss, and hard-won dignity.",
        "tone_tags":   ["intimate", "dramatic", "somber", "close"],
    },
    {
        "slug":        "two_people_intimate",
        "query":       "two people close intimate",
        "description": "Two people in an intensely close, intimate moment — whispered or unspoken.",
        "tone_tags":   ["intimate", "romantic", "close", "warm"],
    },
    {
        "slug":        "abandoned_building_decay",
        "query":       "abandoned building decay",
        "description": "A decaying abandoned building — beauty in ruin and the passage of time.",
        "tone_tags":   ["abandoned", "dark", "melancholy", "gritty"],
    },
    {
        "slug":        "child_wonder_discovery",
        "query":       "child wonder discovery",
        "description": "A child encountering something wondrous for the first time.",
        "tone_tags":   ["hopeful", "warm", "nostalgic", "intimate"],
    },
    {
        "slug":        "night_sky_stars_vast",
        "query":       "night sky stars vast",
        "description": "A breathtaking starfield — the universe framed as awe and insignificance.",
        "tone_tags":   ["wide", "ethereal", "awe", "dark"],
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────

def load_metadata() -> list[dict]:
    if META_PATH.exists():
        with open(META_PATH) as f:
            return json.load(f)
    return []


def save_metadata(records: list[dict]):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(META_PATH, "w") as f:
        json.dump(records, f, indent=2)


def existing_filenames(records: list[dict]) -> set[str]:
    return {r["filename"] for r in records}


def existing_ids(records: list[dict]) -> set[str]:
    return {r["id"] for r in records}


def is_valid_image(data: bytes) -> bool:
    """Check that the downloaded bytes are a real image and large enough."""
    if len(data) < MIN_IMAGE_BYTES:
        return False
    try:
        Image.open(BytesIO(data)).verify()
        return True
    except Exception:
        return False


def fetch_with_retry(url: str, attempt: int, slug: str) -> bytes | None:
    """
    GET the URL and return raw bytes, or None on failure.
    Uses a cache-busting param so Unsplash returns varied results
    across the three downloads for the same query.
    """
    delay = RETRY_BACKOFF
    for retry in range(MAX_RETRIES):
        try:
            resp = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "CineMatch/1.0 (academic project)"},
                # Unsplash Source follows a redirect; requests handles it.
            )
            resp.raise_for_status()
            ct = resp.headers.get("Content-Type", "")
            if "image" not in ct:
                print(f"    [warn] Non-image content-type: {ct}")
                return None
            data = resp.content
            if not is_valid_image(data):
                print(f"    [warn] Downloaded file failed image validation")
                return None
            return data
        except requests.RequestException as e:
            if retry < MAX_RETRIES - 1:
                print(f"    [retry {retry + 1}/{MAX_RETRIES}] {e}")
                time.sleep(delay)
                delay *= 2
            else:
                print(f"    [error] Failed after {MAX_RETRIES} attempts: {e}")
    return None


def download_image(slug: str, idx: int, query: str) -> bytes | None:
    """Try Unsplash Source, fall back to Picsum."""
    # Append a unique token so repeated requests for the same query return
    # different images (Unsplash Source caches by URL).
    unique_query = f"{query} {slug}{idx}"
    unsplash_url = UNSPLASH_URL.format(
        w=IMAGE_W, h=IMAGE_H,
        query=requests.utils.quote(unique_query, safe=""),
    )
    data = fetch_with_retry(unsplash_url, idx, slug)
    if data:
        return data

    # Fallback: Picsum with a deterministic-but-varied seed
    seed = abs(hash(f"{slug}_{idx}")) % 1000
    picsum_url = PICSUM_URL.format(w=IMAGE_W, h=IMAGE_H, seed=seed)
    print(f"    [fallback] Unsplash failed, trying Picsum ({picsum_url})")
    return fetch_with_retry(picsum_url, idx, slug)


def save_image(data: bytes, path: Path):
    """Save raw bytes as a JPEG (re-encode through Pillow to normalise format)."""
    img = Image.open(BytesIO(data)).convert("RGB")
    img.save(path, "JPEG", quality=90)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Populate CineMatch dataset")
    parser.add_argument(
        "--no-ingest", action="store_true",
        help="Skip running ingest.py after downloading"
    )
    args = parser.parse_args()

    SCENES_DIR.mkdir(parents=True, exist_ok=True)

    records = load_metadata()
    existing_files = existing_filenames(records)
    existing_id_set = existing_ids(records)

    downloaded = 0
    skipped    = 0
    failed     = 0
    tag_counter: Counter = Counter()

    total_images = len(QUERIES) * IMAGES_PER_QUERY
    print(f"\nCineMatch Dataset Populator")
    print(f"{'─' * 42}")
    print(f"Queries        : {len(QUERIES)}")
    print(f"Images/query   : {IMAGES_PER_QUERY}")
    print(f"Target total   : {total_images} images")
    print(f"{'─' * 42}\n")

    for entry in QUERIES:
        slug        = entry["slug"]
        query       = entry["query"]
        tone_tags   = entry["tone_tags"]
        description = entry["description"]

        print(f"[{slug}]  \"{query}\"")

        for i in range(1, IMAGES_PER_QUERY + 1):
            filename = f"{slug}_{i:02d}.jpg"
            scene_id = f"dl_{slug}_{i:02d}"
            dest     = SCENES_DIR / filename

            if filename in existing_files or scene_id in existing_id_set:
                print(f"  [skip] {filename} — already exists")
                skipped += 1
                continue

            print(f"  Downloading: {query} {i}/{IMAGES_PER_QUERY}...", end=" ", flush=True)
            data = download_image(slug, i, query)

            if data is None:
                print("FAILED")
                failed += 1
                continue

            save_image(data, dest)
            kb = dest.stat().st_size // 1024
            print(f"saved ({kb} KB)")

            records.append({
                "id":          scene_id,
                "filename":    filename,
                "source":      "Unsplash",
                "description": description,
                "tone_tags":   tone_tags,
            })
            existing_files.add(filename)
            existing_id_set.add(scene_id)
            tag_counter.update(tone_tags)
            downloaded += 1

            # Be polite — avoid hammering the API
            time.sleep(0.5)

        print()

    save_metadata(records)

    # ── Summary ────────────────────────────────────────────────────────────
    print("─" * 42)
    print(f"Downloaded : {downloaded}")
    print(f"Skipped    : {skipped}  (already existed)")
    print(f"Failed     : {failed}")
    print(f"Total in DB: {len(records)} scenes")
    print()
    print("Tone tag distribution:")
    for tag, count in tag_counter.most_common():
        bar = "█" * count
        print(f"  {tag:<20} {bar} ({count})")
    print()

    if downloaded == 0:
        print("No new images downloaded — skipping ingest.")
        return

    if args.no_ingest:
        print("--no-ingest set. Run  python -m backend.ingest  to encode manually.")
        return

    # ── Auto-ingest ────────────────────────────────────────────────────────
    print("─" * 42)
    print("Running ingest.py to encode new images into ChromaDB...\n")
    site_packages = (
        "/Users/boaznakhimovsky/Library/Python/3.12/lib/python/site-packages"
    )
    env = {
        **__import__("os").environ,
        "PYTHONPATH": site_packages,
    }
    result = subprocess.run(
        [sys.executable, "-m", "backend.ingest"],
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    if result.returncode != 0:
        print("\n[warn] ingest.py exited with an error. Check output above.")
    else:
        print("\nDataset ready. Start the server and query away.")


if __name__ == "__main__":
    main()

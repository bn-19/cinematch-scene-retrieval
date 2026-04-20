#!/usr/bin/env python3
"""
CineMatch — Modern Film Trailer Frame Extractor

Extracts frames from YouTube trailers of modern films to expand the dataset
with contemporary cinematography styles.

Usage:
    python populate_modern_trailers.py              # extract + ingest
    python populate_modern_trailers.py --no-ingest  # extract only
    python populate_modern_trailers.py --dry-run    # print plan only
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
SCENES_DIR   = PROJECT_ROOT / "data" / "scenes"
META_PATH    = PROJECT_ROOT / "data" / "metadata.json"

YTDLP_BIN  = "/Users/boaznakhimovsky/Library/Python/3.12/bin/yt-dlp"
FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg"

SITE_PACKAGES = (
    "/Users/boaznakhimovsky/Library/Python/3.12/lib/python/site-packages"
)

# ── Modern Film Catalogue ──────────────────────────────────────────────────
# 20 films with strong, diverse visual identities
# Frames pulled from official YouTube trailers

FILMS = [
    {
        "title":      "Blade Runner 2049",
        "year":       2017,
        "director":   "Denis Villeneuve",
        "url":        "https://www.youtube.com/watch?v=gCcx85zbxz4",
        "tone_tags":  ["futuristic", "neo-noir", "desolate", "wide"],
        "timestamps": ["00:00:20", "00:00:45", "00:01:10", "00:01:35",
                       "00:02:00", "00:02:25", "00:02:45", "00:03:00"],
    },
    {
        "title":      "The Revenant",
        "year":       2015,
        "director":   "Alejandro G. Iñárritu",
        "url":        "https://www.youtube.com/watch?v=QRfj1VCg16E",
        "tone_tags":  ["survival", "wilderness", "epic", "brutal"],
        "timestamps": ["00:00:15", "00:00:40", "00:01:05", "00:01:30",
                       "00:01:55", "00:02:15", "00:02:35", "00:02:50"],
    },
    {
        "title":      "No Country for Old Men",
        "year":       2007,
        "director":   "Joel Coen",
        "url":        "https://www.youtube.com/watch?v=38A__WT3-o0",
        "tone_tags":  ["tense", "noir", "desolate", "suspense"],
        "timestamps": ["00:00:20", "00:00:45", "00:01:05", "00:01:25",
                       "00:01:45", "00:02:00", "00:02:20", "00:02:35"],
    },
    {
        "title":      "Mad Max: Fury Road",
        "year":       2015,
        "director":   "George Miller",
        "url":        "https://www.youtube.com/watch?v=hEJnMQG9ev8",
        "tone_tags":  ["action", "wide", "post-apocalyptic", "kinetic"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:55", "00:02:15", "00:02:30"],
    },
    {
        "title":      "Parasite",
        "year":       2019,
        "director":   "Bong Joon-ho",
        "url":        "https://www.youtube.com/watch?v=5xH0HfJHsaY",
        "tone_tags":  ["domestic", "tense", "dark comedy", "claustrophobic"],
        "timestamps": ["00:00:20", "00:00:45", "00:01:05", "00:01:25",
                       "00:01:45", "00:02:00", "00:02:20", "00:02:35"],
    },
    {
        "title":      "Children of Men",
        "year":       2006,
        "director":   "Alfonso Cuarón",
        "url":        "https://www.youtube.com/watch?v=pNsVoGjLvdg",
        "tone_tags":  ["dystopian", "gritty", "urban", "tense"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:55", "00:02:10", "00:02:25"],
    },
    {
        "title":      "There Will Be Blood",
        "year":       2007,
        "director":   "Paul Thomas Anderson",
        "url":        "https://www.youtube.com/watch?v=UelwUXPi_Vc",
        "tone_tags":  ["epic", "wide", "desolate", "dramatic"],
        "timestamps": ["00:00:20", "00:00:45", "00:01:05", "00:01:25",
                       "00:01:45", "00:02:00", "00:02:20", "00:02:35"],
    },
    {
        "title":      "Interstellar",
        "year":       2014,
        "director":   "Christopher Nolan",
        "url":        "https://www.youtube.com/watch?v=zSWdZVtXT7E",
        "tone_tags":  ["epic", "wide", "sci-fi", "emotional"],
        "timestamps": ["00:00:20", "00:00:45", "00:01:10", "00:01:35",
                       "00:02:00", "00:02:25", "00:02:45", "00:03:00"],
    },
    {
        "title":      "Roma",
        "year":       2018,
        "director":   "Alfonso Cuarón",
        "url":        "https://www.youtube.com/watch?v=sPS2JKDQ8xY",
        "tone_tags":  ["intimate", "domestic", "melancholy", "wide"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:55", "00:02:10", "00:02:25"],
    },
    {
        "title":      "Pan's Labyrinth",
        "year":       2006,
        "director":   "Guillermo del Toro",
        "url":        "https://www.youtube.com/watch?v=6rMoFfVlKJw",
        "tone_tags":  ["dark fantasy", "gothic", "dreamlike", "warm"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:55", "00:02:10", "00:02:25"],
    },
    {
        "title":      "Sicario",
        "year":       2015,
        "director":   "Denis Villeneuve",
        "url":        "https://www.youtube.com/watch?v=sSFCKK4eZRQ",
        "tone_tags":  ["tense", "dark", "wide", "atmospheric"],
        "timestamps": ["00:00:20", "00:00:40", "00:01:00", "00:01:20",
                       "00:01:40", "00:02:00", "00:02:15", "00:02:30"],
    },
    {
        "title":      "The Grand Budapest Hotel",
        "year":       2014,
        "director":   "Wes Anderson",
        "url":        "https://www.youtube.com/watch?v=1Fg5iWmQjwk",
        "tone_tags":  ["symmetrical", "colorful", "whimsical", "warm"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:30", "00:01:45", "00:02:00", "00:02:15"],
    },
    {
        "title":      "Gravity",
        "year":       2013,
        "director":   "Alfonso Cuarón",
        "url":        "https://www.youtube.com/watch?v=OiTiKOy59o4",
        "tone_tags":  ["sci-fi", "wide", "isolated", "tense"],
        "timestamps": ["00:00:20", "00:00:45", "00:01:05", "00:01:25",
                       "00:01:45", "00:02:00", "00:02:20", "00:02:35"],
    },
    {
        "title":      "Her",
        "year":       2013,
        "director":   "Spike Jonze",
        "url":        "https://www.youtube.com/watch?v=WzV6mXIOVl4",
        "tone_tags":  ["warm", "intimate", "futuristic", "melancholy"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:50", "00:02:05", "00:02:20"],
    },
    {
        "title":      "Dunkirk",
        "year":       2017,
        "director":   "Christopher Nolan",
        "url":        "https://www.youtube.com/watch?v=F-eMt3S0T4Y",
        "tone_tags":  ["war", "tense", "wide", "epic"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:55", "00:02:10", "00:02:25"],
    },
    {
        "title":      "Moonlight",
        "year":       2016,
        "director":   "Barry Jenkins",
        "url":        "https://www.youtube.com/watch?v=9NJj12tJzqc",
        "tone_tags":  ["intimate", "warm", "emotional", "close-up"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:10",
                       "00:01:25", "00:01:40", "00:01:55", "00:02:10"],
    },
    {
        "title":      "The Tree of Life",
        "year":       2011,
        "director":   "Terrence Malick",
        "url":        "https://www.youtube.com/watch?v=RrAz1YLh8nY",
        "tone_tags":  ["ethereal", "wide", "natural", "dreamlike"],
        "timestamps": ["00:00:20", "00:00:45", "00:01:05", "00:01:25",
                       "00:01:45", "00:02:00", "00:02:20", "00:02:35"],
    },
    {
        "title":      "Oldboy",
        "year":       2003,
        "director":   "Park Chan-wook",
        "url":        "https://www.youtube.com/watch?v=2G1CliE0mJk",
        "tone_tags":  ["dark", "tense", "claustrophobic", "psychological"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:50", "00:02:05", "00:02:20"],
    },
    {
        "title":      "1917",
        "year":       2019,
        "director":   "Sam Mendes",
        "url":        "https://www.youtube.com/watch?v=YqNYrYUiMfg",
        "tone_tags":  ["war", "tense", "wide", "continuous"],
        "timestamps": ["00:00:20", "00:00:40", "00:01:00", "00:01:20",
                       "00:01:40", "00:02:00", "00:02:20", "00:02:35"],
    },
    {
        "title":      "The Lighthouse",
        "year":       2019,
        "director":   "Robert Eggers",
        "url":        "https://www.youtube.com/watch?v=Hyag7lR8CPA",
        "tone_tags":  ["dark", "isolated", "psychological", "claustrophobic"],
        "timestamps": ["00:00:15", "00:00:35", "00:00:55", "00:01:15",
                       "00:01:35", "00:01:50", "00:02:05", "00:02:20"],
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────

def load_metadata() -> list[dict]:
    if META_PATH.exists():
        try:
            with open(META_PATH) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("[warn] metadata.json corrupt — starting fresh")
    return []


def save_metadata(records: list[dict]):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(META_PATH, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def ts_to_slug(ts: str) -> str:
    return ts.replace(":", "")


def title_to_slug(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def get_stream_url(youtube_url: str) -> str | None:
    try:
        result = subprocess.run(
            [YTDLP_BIN, "--get-url", "--no-warnings", "--quiet",
             "-f", "bestvideo[ext=mp4]/bestvideo/best", youtube_url],
            capture_output=True, text=True, timeout=60,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if not lines:
            err = result.stderr.strip().splitlines()
            print(f"    [warn] yt-dlp: {err[-1] if err else 'no output'}")
            return None
        return lines[0]
    except subprocess.TimeoutExpired:
        print("    [warn] yt-dlp timed out")
        return None
    except FileNotFoundError:
        print(f"    [error] yt-dlp not found at {YTDLP_BIN}")
        return None


def extract_frame(stream_url: str, timestamp: str, output_path: Path) -> bool:
    try:
        result = subprocess.run(
            [
                FFMPEG_BIN,
                "-ss", timestamp,
                "-i", stream_url,
                "-vframes", "1",
                "-q:v", "2",
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease",
                "-y",
                str(output_path),
            ],
            capture_output=True, timeout=120,
        )
        if result.returncode != 0:
            err = result.stderr.decode(errors="replace").strip().splitlines()
            for line in reversed(err):
                if any(w in line for w in ["Error", "Invalid", "failed", "403", "404"]):
                    print(f"    [ffmpeg] {line.strip()}")
                    break
            return False
        if not output_path.exists() or output_path.stat().st_size < 5_000:
            print(f"    [warn] output missing or too small")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"    [warn] ffmpeg timed out at {timestamp}")
        if output_path.exists():
            output_path.unlink()
        return False


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-ingest", action="store_true")
    parser.add_argument("--dry-run",   action="store_true")
    args = parser.parse_args()

    SCENES_DIR.mkdir(parents=True, exist_ok=True)

    records      = load_metadata()
    existing     = {r["filename"] for r in records}
    existing_ids = {r["id"] for r in records}

    total_frames = sum(len(f["timestamps"]) for f in FILMS)
    extracted = skipped = failed = 0

    print(f"\nCineMatch — Modern Trailer Frame Extraction")
    print(f"{'─' * 50}")
    print(f"Films          : {len(FILMS)}")
    print(f"Frames planned : {total_frames}")
    print(f"Already in DB  : {len(records)}")
    print(f"{'─' * 50}\n")

    for film in FILMS:
        title      = film["title"]
        year       = film["year"]
        director   = film["director"]
        url        = film["url"]
        tone_tags  = film["tone_tags"]
        timestamps = film["timestamps"]
        slug       = title_to_slug(title)

        film_existing = sum(
            1 for ts in timestamps
            if f"{slug}_{year}_{ts_to_slug(ts)}.jpg" in existing
        )
        remaining = len(timestamps) - film_existing

        print(f"[{title} ({year})] — Dir. {director}")
        if remaining == 0:
            print(f"  All {len(timestamps)} frames already exist — skipping\n")
            skipped += len(timestamps)
            continue

        if args.dry_run:
            for ts in timestamps:
                fname = f"{slug}_{year}_{ts_to_slug(ts)}.jpg"
                status = "exists" if fname in existing else "will download"
                print(f"  {ts}  →  {fname}  [{status}]")
            print()
            continue

        print(f"  Resolving stream URL ({remaining} new frames)...", end=" ", flush=True)
        stream_url = get_stream_url(url)
        if stream_url is None:
            print("FAILED — skipping film")
            failed += remaining
            print()
            continue
        print("ok")

        for ts in timestamps:
            fname    = f"{slug}_{year}_{ts_to_slug(ts)}.jpg"
            scene_id = f"mod_{slug}_{year}_{ts_to_slug(ts)}"
            dest     = SCENES_DIR / fname

            if fname in existing or scene_id in existing_ids:
                print(f"  [{ts}]  skip")
                skipped += 1
                continue

            print(f"  [{ts}]  → {fname}...", end=" ", flush=True)
            ok = extract_frame(stream_url, ts, dest)

            if ok:
                kb = dest.stat().st_size // 1024
                print(f"ok ({kb} KB)")
                records.append({
                    "id":          scene_id,
                    "filename":    fname,
                    "source":      f"{title} ({year})",
                    "film_title":  title,
                    "director":    director,
                    "year":        year,
                    "timestamp":   ts,
                    "description": f"{title} ({year}) — frame at {ts}",
                    "tone_tags":   tone_tags,
                })
                existing.add(fname)
                existing_ids.add(scene_id)
                extracted += 1
            else:
                print("FAILED")
                failed += 1

            time.sleep(0.2)

        print()

    if not args.dry_run:
        save_metadata(records)

    print("─" * 50)
    if args.dry_run:
        print("Dry run — no files downloaded.")
        return

    print(f"Extracted  : {extracted} new frames")
    print(f"Skipped    : {skipped}  (already existed)")
    print(f"Failed     : {failed}")
    print(f"Total in DB: {len(records)} scenes")
    print()

    if extracted == 0:
        print("No new frames — skipping ingest.")
        return

    if args.no_ingest:
        print("--no-ingest set. Run  python -m backend.ingest  manually.")
        return

    print("─" * 50)
    print("Ingesting into ChromaDB...\n")
    env = {**os.environ, "PYTHONPATH": SITE_PACKAGES}
    result = subprocess.run(
        [sys.executable, "-m", "backend.ingest"],
        cwd=str(PROJECT_ROOT),
        env=env,
    )
    if result.returncode != 0:
        print("\n[warn] ingest.py exited with an error.")
    else:
        print(f"\nDone — {len(records)} scenes ready. Restart the server.")


if __name__ == "__main__":
    main()

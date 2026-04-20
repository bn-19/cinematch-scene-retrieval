#!/usr/bin/env python3
"""
CineMatch — Public Domain Film Stills Extractor (Expanded)

Extracts frames from a large catalogue of public domain films on Internet Archive.
Run this script to populate the dataset with diverse cinematic frames.

Usage:
    python populate_film_stills.py              # extract + ingest
    python populate_film_stills.py --no-ingest  # extract only
    python populate_film_stills.py --dry-run    # print plan, download nothing
"""

import argparse
import json
import os
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

# ── Expanded Film Catalogue ────────────────────────────────────────────────
# 20 films x ~8 frames each = ~160 frames
# Covers: horror, expressionism, sci-fi, action, romance, comedy, war,
#         crowd/epic, noir, melodrama, landscape, urban, Western, documentary

FILMS = [
    # ── Already extracted (will be skipped if files exist) ────────────────
    {
        "title":      "Nosferatu",
        "year":       1922,
        "director":   "F.W. Murnau",
        "archive_id": "nosferatu_1922",
        "tone_tags":  ["dark", "horror", "expressionist", "shadow"],
        "timestamps": ["00:08:00", "00:12:30", "00:20:00", "00:28:45",
                       "00:38:00", "00:45:10", "00:55:00", "01:02:20"],
    },
    {
        "title":      "Metropolis",
        "year":       1927,
        "director":   "Fritz Lang",
        "archive_id": "metropolis-phantom-of-the-opera-loy-cook",
        "tone_tags":  ["futuristic", "industrial", "epic", "crowd"],
        "timestamps": ["00:10:00", "00:15:00", "00:25:00", "00:32:00",
                       "00:45:00", "00:55:00", "01:10:00", "01:20:00"],
    },
    {
        "title":      "The General",
        "year":       1926,
        "director":   "Buster Keaton",
        "archive_id": "the-general-1926_202506",
        "tone_tags":  ["wide", "outdoor", "action", "epic"],
        "timestamps": ["00:05:00", "00:10:00", "00:16:00", "00:22:00",
                       "00:30:00", "00:38:00", "00:45:00", "00:52:00"],
    },
    {
        "title":      "The Cabinet of Dr. Caligari",
        "year":       1920,
        "director":   "Robert Wiene",
        "archive_id": "Gabinet.doktora.Caligari.1920Rez.RobertWiene",
        "tone_tags":  ["expressionist", "disorienting", "dark", "psychological"],
        "timestamps": ["00:05:00", "00:08:00", "00:14:00", "00:20:00",
                       "00:28:00", "00:35:00", "00:42:00", "00:48:00"],
    },
    {
        "title":      "Sunrise: A Song of Two Humans",
        "year":       1927,
        "director":   "F.W. Murnau",
        "archive_id": "sunrise-a-song-of-two-humans-1927",
        "tone_tags":  ["intimate", "romantic", "rural", "emotional"],
        "timestamps": ["00:06:00", "00:10:00", "00:18:00", "00:25:00",
                       "00:35:00", "00:42:00", "00:52:00", "01:00:00"],
    },
    {
        "title":      "Battleship Potemkin",
        "year":       1925,
        "director":   "Sergei Eisenstein",
        "archive_id": "BattleshipPotemkin",
        "tone_tags":  ["crowd", "dramatic", "revolutionary", "wide"],
        "timestamps": ["00:05:00", "00:08:00", "00:14:00", "00:20:00",
                       "00:28:00", "00:38:00", "00:46:00", "00:55:00"],
    },
    {
        "title":      "It Happened One Night",
        "year":       1934,
        "director":   "Frank Capra",
        "archive_id": "it-happened-one-night-1934_202501",
        "tone_tags":  ["domestic", "comedic", "warm", "dialogue"],
        "timestamps": ["00:08:00", "00:18:00", "00:28:00", "00:38:00",
                       "00:45:00", "00:55:00", "01:05:00", "01:15:00"],
    },

    # ── New films ─────────────────────────────────────────────────────────
    {
        "title":      "The Phantom of the Opera",
        "year":       1925,
        "director":   "Rupert Julian",
        "archive_id": "phantom-of-the-opera-1925",
        "tone_tags":  ["dark", "gothic", "dramatic", "mysterious"],
        "timestamps": ["00:10:00", "00:22:00", "00:35:00", "00:48:00",
                       "01:00:00", "01:12:00", "01:25:00", "01:35:00"],
    },
    {
        "title":      "The Gold Rush",
        "year":       1925,
        "director":   "Charlie Chaplin",
        "archive_id": "sircharliechaplin",
        "tone_tags":  ["comedic", "survival", "snow", "intimate"],
        "timestamps": ["00:08:00", "00:18:00", "00:30:00", "00:42:00",
                       "00:52:00", "01:02:00", "01:12:00", "01:22:00"],
    },
    {
        "title":      "Safety Last!",
        "year":       1923,
        "director":   "Fred C. Newmeyer",
        "archive_id": "safety-last-1923",
        "tone_tags":  ["comedic", "urban", "tense", "action"],
        "timestamps": ["00:05:00", "00:14:00", "00:24:00", "00:34:00",
                       "00:44:00", "00:52:00", "01:00:00", "01:08:00"],
    },
    {
        "title":      "Intolerance",
        "year":       1916,
        "director":   "D.W. Griffith",
        "archive_id": "intolerance-dw-griffith-1916",
        "tone_tags":  ["epic", "crowd", "ancient", "dramatic"],
        "timestamps": ["00:10:00", "00:25:00", "00:45:00", "01:05:00",
                       "01:25:00", "01:50:00", "02:10:00", "02:30:00"],
    },
    {
        "title":      "Way Down East",
        "year":       1920,
        "director":   "D.W. Griffith",
        "archive_id": "WayDownEast",
        "tone_tags":  ["melodrama", "snow", "rural", "emotional"],
        "timestamps": ["00:10:00", "00:25:00", "00:40:00", "00:58:00",
                       "01:15:00", "01:30:00", "01:45:00", "01:58:00"],
    },
    {
        "title":      "The Crowd",
        "year":       1928,
        "director":   "King Vidor",
        "archive_id": "TheCrowd1928",
        "tone_tags":  ["urban", "modern", "intimate", "melancholy"],
        "timestamps": ["00:08:00", "00:18:00", "00:30:00", "00:42:00",
                       "00:54:00", "01:05:00", "01:16:00", "01:28:00"],
    },
    {
        "title":      "Greed",
        "year":       1924,
        "director":   "Erich von Stroheim",
        "archive_id": "greed-1924-erich-von-stroheim",
        "tone_tags":  ["gritty", "close-up", "dramatic", "dark"],
        "timestamps": ["00:12:00", "00:28:00", "00:48:00", "01:05:00",
                       "01:25:00", "01:45:00", "02:05:00", "02:20:00"],
    },
    {
        "title":      "The Hunchback of Notre Dame",
        "year":       1923,
        "director":   "Wallace Worsley",
        "archive_id": "the-hunchback-of-notre-dame-1923",
        "tone_tags":  ["gothic", "dark", "crowd", "dramatic"],
        "timestamps": ["00:10:00", "00:22:00", "00:36:00", "00:50:00",
                       "01:04:00", "01:18:00", "01:30:00", "01:42:00"],
    },
    {
        "title":      "Sherlock Jr.",
        "year":       1924,
        "director":   "Buster Keaton",
        "archive_id": "sherlock-jr-1924-restored-720p-hd",
        "tone_tags":  ["comedic", "dreamlike", "action", "playful"],
        "timestamps": ["00:05:00", "00:12:00", "00:20:00", "00:28:00",
                       "00:36:00", "00:44:00", "00:52:00", "00:58:00"],
    },
    {
        "title":      "The Navigator",
        "year":       1924,
        "director":   "Buster Keaton",
        "archive_id": "the-navigator-1924-buster-keaton",
        "tone_tags":  ["comedic", "ocean", "wide", "isolation"],
        "timestamps": ["00:05:00", "00:12:00", "00:20:00", "00:30:00",
                       "00:38:00", "00:46:00", "00:54:00", "01:00:00"],
    },
    {
        "title":      "Dr. Jekyll and Mr. Hyde",
        "year":       1920,
        "director":   "John S. Robertson",
        "archive_id": "dr.-jekyll-and-mr.-hyde-1920",
        "tone_tags":  ["horror", "transformation", "dark", "psychological"],
        "timestamps": ["00:08:00", "00:18:00", "00:28:00", "00:40:00",
                       "00:52:00", "01:02:00", "01:12:00", "01:20:00"],
    },
    {
        "title":      "The Mark of Zorro",
        "year":       1920,
        "director":   "Fred Niblo",
        "archive_id": "the-mark-of-zorro-1920",
        "tone_tags":  ["action", "adventure", "swashbuckler", "dramatic"],
        "timestamps": ["00:08:00", "00:18:00", "00:30:00", "00:42:00",
                       "00:54:00", "01:04:00", "01:14:00", "01:24:00"],
    },
    {
        "title":      "Strike",
        "year":       1925,
        "director":   "Sergei Eisenstein",
        "archive_id": "strike-1925-eisenstein",
        "tone_tags":  ["crowd", "revolutionary", "gritty", "wide"],
        "timestamps": ["00:06:00", "00:15:00", "00:25:00", "00:36:00",
                       "00:46:00", "00:56:00", "01:06:00", "01:15:00"],
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────

def load_metadata() -> list[dict]:
    if META_PATH.exists():
        try:
            with open(META_PATH) as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("[warn] metadata.json is corrupt — starting fresh")
    return []


def save_metadata(records: list[dict]):
    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(META_PATH, "w") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def ts_to_slug(ts: str) -> str:
    return ts.replace(":", "")


def title_to_slug(title: str) -> str:
    import re
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


def get_stream_url(archive_id: str) -> str | None:
    url = f"https://archive.org/details/{archive_id}"
    try:
        result = subprocess.run(
            [YTDLP_BIN, "--get-url", "--no-warnings", "--quiet", url],
            capture_output=True, text=True, timeout=60,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if not lines:
            err = result.stderr.strip().splitlines()
            print(f"    [warn] yt-dlp returned no URL: {err[-1] if err else 'no output'}")
            return None
        ranked = sorted(lines, key=lambda u: (
            0 if u.endswith(".mp4") or u.endswith(".m4v") else
            1 if u.endswith(".mkv") else 2
        ))
        return ranked[0]
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
                if any(w in line for w in ["Error", "Invalid", "failed", "No such"]):
                    print(f"    [ffmpeg] {line.strip()}")
                    break
            return False
        if not output_path.exists() or output_path.stat().st_size < 5_000:
            print(f"    [warn] output file missing or too small")
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

    print(f"\nCineMatch — Expanded Film Stills Extraction")
    print(f"{'─' * 50}")
    print(f"Films          : {len(FILMS)}")
    print(f"Frames planned : {total_frames}")
    print(f"Already in DB  : {len(records)}")
    print(f"{'─' * 50}\n")

    for film in FILMS:
        title      = film["title"]
        year       = film["year"]
        director   = film.get("director", "Unknown")
        archive_id = film["archive_id"]
        tone_tags  = film["tone_tags"]
        timestamps = film["timestamps"]
        slug       = title_to_slug(title)

        # Check how many frames from this film already exist
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

        print(f"  Resolving stream URL ({remaining} new frames needed)...", end=" ", flush=True)
        stream_url = get_stream_url(archive_id)
        if stream_url is None:
            print("FAILED — skipping film")
            failed += remaining
            print()
            continue
        print("ok")

        for ts in timestamps:
            fname    = f"{slug}_{year}_{ts_to_slug(ts)}.jpg"
            scene_id = f"fs_{slug}_{year}_{ts_to_slug(ts)}"
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

            time.sleep(0.3)

        print()

    if not args.dry_run:
        save_metadata(records)

    print("─" * 50)
    if args.dry_run:
        print("Dry run complete — no files downloaded.")
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
    print("Ingesting new frames into ChromaDB...\n")
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

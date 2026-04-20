"""
CineMatch — Dataset Ingestion Script

Loads scene images and metadata, generates CLIP embeddings, and stores
them in ChromaDB. Run this script before starting the server:

    python -m backend.ingest
"""

import json
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.embedder import encode_image
from backend.database import add_scene, clear_collection, collection_count


def ingest():
    data_dir = PROJECT_ROOT / "data"
    scenes_dir = data_dir / "scenes"
    metadata_path = data_dir / "metadata.json"

    if not metadata_path.exists():
        print(f"Error: metadata.json not found at {metadata_path}")
        sys.exit(1)

    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    print(f"Found {len(metadata)} scenes in metadata.json")
    print("Clearing existing collection...")
    clear_collection()

    success_count = 0
    skip_count = 0

    for scene in metadata:
        image_path = scenes_dir / scene["filename"]
        if not image_path.exists():
            print(f"  [SKIP] {scene['filename']} — file not found")
            skip_count += 1
            continue

        print(f"  [ENCODE] {scene['filename']}...", end=" ", flush=True)
        try:
            embedding = encode_image(str(image_path))
            add_scene(
                scene_id=scene["id"],
                embedding=embedding,
                metadata={
                    "source": scene["source"],
                    "description": scene["description"],
                    "filename": scene["filename"],
                    "tone_tags": ", ".join(scene["tone_tags"]),
                    "film_title": scene.get("film_title", ""),
                    "director": scene.get("director", ""),
                    "year": str(scene.get("year", "")),
                    "timestamp": scene.get("timestamp", ""),
                },
            )
            print("done")
            success_count += 1
        except Exception as e:
            print(f"error: {e}")
            skip_count += 1

    print(f"\nIngestion complete: {success_count} encoded, {skip_count} skipped")
    print(f"Collection now contains {collection_count()} scenes")


if __name__ == "__main__":
    ingest()

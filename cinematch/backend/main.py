"""
CineMatch — FastAPI Application

Provides the API endpoint for natural language film scene retrieval
and serves the frontend static files.
"""

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from backend.embedder import encode_text
from backend.database import query_scenes, collection_count

PROJECT_ROOT = Path(__file__).resolve().parent.parent

app = FastAPI(title="CineMatch", version="1.0.0")


@app.get("/api/search")
def search_scenes(q: str = Query(..., min_length=1, description="Scene description")):
    """
    Encode the user's natural language query with CLIP's text encoder
    and retrieve the top 5 most similar film scenes from ChromaDB.
    """
    text_embedding = encode_text(q)
    results = query_scenes(text_embedding, n_results=5)

    scenes = []
    if results and results["ids"] and results["ids"][0]:
        for i, scene_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            # ChromaDB cosine distance is in [0, 2]; convert to similarity in [0, 1]
            similarity = 1.0 - (distance / 2.0)
            scenes.append(
                {
                    "id": scene_id,
                    "source": meta["source"],
                    "description": meta["description"],
                    "filename": meta["filename"],
                    "tone_tags": meta["tone_tags"],
                    "similarity": round(similarity, 4),
                    "film_title": meta.get("film_title", ""),
                    "director": meta.get("director", ""),
                    "year": meta.get("year", ""),
                    "timestamp": meta.get("timestamp", ""),
                }
            )

    return {"query": q, "results": scenes}


@app.get("/api/status")
def status():
    """Return the number of scenes currently indexed."""
    return {"scenes_indexed": collection_count()}


# Serve scene images from data/scenes/
app.mount(
    "/images",
    StaticFiles(directory=str(PROJECT_ROOT / "data" / "scenes")),
    name="images",
)

# Serve frontend static files
app.mount(
    "/static",
    StaticFiles(directory=str(PROJECT_ROOT / "frontend")),
    name="frontend",
)


@app.get("/")
def serve_frontend():
    return FileResponse(str(PROJECT_ROOT / "frontend" / "index.html"))

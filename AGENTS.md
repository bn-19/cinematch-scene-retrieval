# CineMatch Agent Notes

This repository contains a school project in `cinematch/`. The app is a FastAPI
backend plus static HTML/CSS/JS frontend for CLIP-based film scene retrieval.

## Project Layout

- `cinematch/backend/main.py` defines the FastAPI app.
- `cinematch/backend/embedder.py` loads OpenCLIP and encodes image/text vectors.
- `cinematch/backend/database.py` wraps the local ChromaDB collection.
- `cinematch/backend/ingest.py` rebuilds the vector index from `data/metadata.json`
  and `data/scenes/`.
- `cinematch/frontend/` contains static assets served by FastAPI.
- `cinematch/data/scenes/` contains the scene images.
- `cinematch/data/chromadb_store/` is a generated local ChromaDB index.
- `cinematch/Dockerfile` is the production deploy path for Hugging Face Spaces.

## Local Run

From `cinematch/`:

```bash
python3 -m compileall -q backend *.py
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000
```

Useful checks:

```bash
curl -sS http://127.0.0.1:8000/api/status
curl -sS 'http://127.0.0.1:8000/api/search?q=dark%20shadow'
```

## Hugging Face Space

The public hosted app is:

```text
https://bn19-cinematch-scene-retrieval.hf.space
```

The Hugging Face repo is:

```text
https://huggingface.co/spaces/bn19/cinematch-scene-retrieval
```

The Space ID is:

```text
bn19/cinematch-scene-retrieval
```

It is a Docker Space on free `cpu-basic` hardware. Do not upgrade hardware or add
paid storage unless the user explicitly asks.

## Deployment Workflow

### Automatic GitHub Deploys

This repo has a GitHub Actions workflow at:

```text
.github/workflows/deploy-huggingface.yml
```

On every push to `main` that changes `cinematch/**`, the workflow uploads the
`cinematch/` folder to the existing Hugging Face Space. It uses the GitHub
repository secret `HF_TOKEN`, which must be a Hugging Face token with write
access to `bn19/cinematch-scene-retrieval`.

The workflow intentionally ignores and deletes `data/chromadb_store/**` on the
Space because the Dockerfile rebuilds that Chroma index inside the image.

The workflow can also be run manually from the GitHub Actions tab with
`workflow_dispatch`.

### Manual Deploys

The local Hugging Face CLI must be authenticated as `bn19`:

```bash
hf auth whoami
```

If not logged in, ask the user to run:

```bash
hf auth login --add-to-git-credential
```

Upload from `cinematch/`:

```bash
python3 - <<'PY'
from huggingface_hub import HfApi

api = HfApi()
info = api.upload_folder(
    repo_id="bn19/cinematch-scene-retrieval",
    repo_type="space",
    folder_path=".",
    commit_message="Update CineMatch Space",
    ignore_patterns=[
        "__pycache__/**",
        "*.pyc",
        ".DS_Store",
        ".claude/**",
    ],
)
print(info.commit_url)
PY
```

Watch status/logs:

```bash
python3 - <<'PY'
from huggingface_hub import HfApi
print(HfApi().get_space_runtime("bn19/cinematch-scene-retrieval"))
PY

hf spaces logs bn19/cinematch-scene-retrieval --build -n 120
hf spaces logs bn19/cinematch-scene-retrieval -n 120
```

Verify production:

```bash
curl -sS -L --max-time 30 https://bn19-cinematch-scene-retrieval.hf.space/ | sed -n '1,20p'
curl -sS -L --max-time 30 https://bn19-cinematch-scene-retrieval.hf.space/api/status
curl -sS -L --max-time 90 'https://bn19-cinematch-scene-retrieval.hf.space/api/search?q=dark%20shadow'
```

Expected status response:

```json
{"scenes_indexed":172}
```

## Dockerfile Notes

The Dockerfile intentionally:

- Uses `python:3.12-slim`.
- Installs `libgomp1`, required by Torch/OpenCLIP dependencies.
- Installs CPU-only `torch==2.4.1` and `torchvision==0.19.1` before
  `requirements.txt` to avoid CUDA packages on the free CPU Space.
- Sets `HF_HOME=/app/.cache/huggingface` so model weights are cached in the image.
- Sets `ANONYMIZED_TELEMETRY=False` to reduce Chroma telemetry noise.
- Deletes `data/chromadb_store` and runs `python -m backend.ingest` during image
  build. This is important: the previously committed local Chroma index failed in
  the Space with `KeyError: '_type'`. Rebuilding inside the image makes the index
  compatible with the installed ChromaDB version and preloads CLIP weights.

The build can take several minutes because it downloads PyTorch, OpenCLIP, the
CLIP model weights, and encodes all scene images.

## Important Gotchas

- Do not use Vercel for the full app. Vercel is a poor fit because this project
  needs PyTorch/OpenCLIP and a local vector index.
- The first request after the free Space sleeps may be slow while it wakes up.
- `HEAD /` returns 405 because only `GET /` is defined. Use `GET` for checks.
- The README frontmatter must keep `sdk: docker` and `app_port: 7860`.
- Hugging Face requires `emoji` metadata to be a real emoji.
- Keep generated cache and bytecode out of uploads.

## Editing Guidance

- Keep changes scoped to `cinematch/` unless the user asks for repo-level files.
- Prefer preserving the current FastAPI/static frontend structure.
- If dependencies change, verify the Docker build logs after upload.
- If scene metadata or images change, make sure `python -m backend.ingest` can
  rebuild the index successfully.
- Before telling the user the app is working, verify `/api/status` and one
  `/api/search` query against the public Space URL.

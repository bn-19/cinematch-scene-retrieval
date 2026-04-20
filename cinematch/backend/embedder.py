"""
CineMatch — CLIP Embedding Module

This module implements the core retrieval mechanism described in:

    Radford, A., Kim, J.W., Hallacy, C., et al. (2021).
    "Learning Transferable Visual Models From Natural Language Supervision."
    Proceedings of the 38th International Conference on Machine Learning (ICML).

Approach:
    CLIP (Contrastive Language-Image Pre-Training) learns a shared embedding space
    for images and text by training on 400 million image-text pairs. Both modalities
    are projected into the same vector space such that semantically related images
    and text descriptions have high cosine similarity.

    CineMatch leverages this shared space as follows:
    1. Film scene stills are encoded using CLIP's vision encoder (ViT-B/32) to
       produce image embeddings.
    2. User queries (natural language scene descriptions) are encoded using CLIP's
       text encoder to produce text embeddings.
    3. Cosine similarity between the text embedding and all stored image embeddings
       identifies the scenes that most closely match the user's described mood,
       composition, and visual tone.

    This zero-shot retrieval approach requires no task-specific fine-tuning — the
    pretrained CLIP model generalizes to film scene matching because its training
    data encompasses a broad distribution of visual and linguistic concepts.
"""

import open_clip
import torch
from PIL import Image


_model = None
_preprocess = None
_tokenizer = None
_device = None


def _get_device():
    global _device
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    return _device


def _load_model():
    global _model, _preprocess, _tokenizer
    if _model is None:
        device = _get_device()
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        _tokenizer = open_clip.get_tokenizer("ViT-B-32")
        _model = _model.to(device)
        _model.eval()
    return _model, _preprocess, _tokenizer


def encode_image(image_path: str) -> list[float]:
    """Encode a single image file into a CLIP embedding vector."""
    model, preprocess, _ = _load_model()
    device = _get_device()

    image = Image.open(image_path).convert("RGB")
    image_tensor = preprocess(image).unsqueeze(0).to(device)

    with torch.no_grad():
        embedding = model.encode_image(image_tensor)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)

    return embedding.squeeze().cpu().tolist()


def encode_text(text: str) -> list[float]:
    """Encode a text query into a CLIP embedding vector."""
    model, _, tokenizer = _load_model()
    device = _get_device()

    tokens = tokenizer([text]).to(device)

    with torch.no_grad():
        embedding = model.encode_text(tokens)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)

    return embedding.squeeze().cpu().tolist()

"""
Generate visually distinct placeholder images for the CineMatch scene dataset.
Each image is 800x600 with gradients, colors, and text overlays matching the scene mood.
"""

import json
import os
import math
import random
from PIL import Image, ImageDraw, ImageFont

SCENE_DIR = os.path.join(os.path.dirname(__file__), "data", "scenes")
METADATA_PATH = os.path.join(os.path.dirname(__file__), "data", "metadata.json")
WIDTH, HEIGHT = 800, 600

# Color palettes keyed by tone keywords
TONE_COLORS = {
    "dark":        ((20, 15, 25),    (50, 40, 55)),
    "moody":       ((30, 25, 45),    (70, 55, 80)),
    "noir":        ((15, 12, 10),    (60, 50, 35)),
    "mysterious":  ((10, 20, 35),    (45, 55, 75)),
    "bright":      ((220, 200, 150), (255, 240, 200)),
    "hopeful":     ((200, 180, 100), (255, 230, 160)),
    "warm":        ((180, 100, 40),  (240, 170, 80)),
    "epic":        ((60, 40, 80),    (180, 120, 60)),
    "tense":       ((40, 20, 20),    (100, 50, 50)),
    "intimate":    ((120, 70, 40),   (200, 140, 80)),
    "peaceful":    ((100, 160, 200), (180, 220, 240)),
    "serene":      ((120, 180, 210), (200, 230, 245)),
    "ethereal":    ((80, 60, 130),   (160, 140, 210)),
    "horror":      ((20, 10, 10),    (80, 30, 30)),
    "desolate":    ((140, 120, 80),  (210, 190, 150)),
    "romantic":    ((160, 60, 80),   (230, 140, 160)),
    "urban":       ((30, 30, 40),    (80, 80, 100)),
    "cold":        ((60, 80, 120),   (140, 170, 210)),
    "action":      ((40, 10, 10),    (200, 60, 30)),
    "isolated":    ((40, 50, 60),    (100, 120, 140)),
    "nostalgic":   ((150, 120, 70),  (220, 190, 140)),
    "somber":      ((40, 40, 50),    (90, 90, 100)),
    "clinical":    ((180, 200, 210), (230, 240, 245)),
    "industrial":  ((50, 50, 45),    (120, 115, 100)),
    "elegant":     ((100, 70, 50),   (220, 190, 150)),
    "energetic":   ((180, 40, 20),   (255, 160, 30)),
    "contemplative": ((40, 50, 70),  (100, 120, 160)),
    "colorful":    ((180, 100, 40),  (220, 180, 50)),
    "gritty":      ((60, 50, 40),    (130, 110, 90)),
    "triumphant":  ((200, 160, 60),  (255, 220, 100)),
    "awe":         ((30, 20, 60),    (120, 80, 180)),
    "psychological": ((50, 30, 50),  (110, 70, 110)),
    "confrontational": ((80, 20, 15), (150, 50, 40)),
    "grief":       ((30, 30, 35),    (70, 70, 80)),
    "domestic":    ((200, 170, 120), (240, 220, 180)),
    "dynamic":     ((40, 20, 60),    (180, 80, 40)),
    "formal":      ((50, 40, 30),    (140, 120, 100)),
    "architectural": ((120, 110, 100), (200, 190, 175)),
    "intellectual": ((80, 60, 40),   (160, 130, 100)),
    "blue":        ((10, 30, 80),    (40, 100, 200)),
    "musical":     ((40, 20, 50),    (120, 60, 100)),
    "journey":     ((100, 80, 50),   (200, 170, 120)),
    "dangerous":   ((30, 10, 10),    (120, 30, 20)),
    "war":         ((50, 45, 35),    (130, 110, 80)),
    "abandoned":   ((60, 55, 50),    (130, 120, 105)),
    "atmospheric": ((40, 40, 60),    (100, 100, 140)),
    "claustrophobic": ((25, 20, 20), (70, 60, 55)),
    "wide":        ((80, 100, 140),  (180, 200, 230)),
    "close":       ((100, 70, 50),   (170, 130, 100)),
}


def blend(c1, c2, t):
    """Linearly interpolate between two RGB tuples."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def get_palette(tone_tags):
    """Derive top and bottom gradient colors from tone tags."""
    top_r, top_g, top_b = 0, 0, 0
    bot_r, bot_g, bot_b = 0, 0, 0
    count = 0
    for tag in tone_tags:
        if tag in TONE_COLORS:
            t, b = TONE_COLORS[tag]
            top_r += t[0]; top_g += t[1]; top_b += t[2]
            bot_r += b[0]; bot_g += b[1]; bot_b += b[2]
            count += 1
    if count == 0:
        return (80, 80, 80), (160, 160, 160)
    top = (top_r // count, top_g // count, top_b // count)
    bot = (bot_r // count, bot_g // count, bot_b // count)
    return top, bot


def add_texture(draw, width, height, tone_tags, seed):
    """Add visual texture elements based on mood."""
    rng = random.Random(seed)

    # Scattered light spots for night/neon scenes
    if any(t in tone_tags for t in ["noir", "urban", "atmospheric", "moody"]):
        for _ in range(rng.randint(15, 40)):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            r = rng.randint(2, 8)
            brightness = rng.randint(120, 255)
            color_choice = rng.choice([
                (brightness, brightness, int(brightness * 0.7)),
                (int(brightness * 0.7), brightness, brightness),
                (brightness, int(brightness * 0.8), int(brightness * 0.6)),
            ])
            draw.ellipse([x - r, y - r, x + r, y + r], fill=color_choice + (rng.randint(40, 120),))

    # Horizontal streaks for action/dynamic
    if any(t in tone_tags for t in ["action", "dynamic", "energetic"]):
        for _ in range(rng.randint(8, 20)):
            y = rng.randint(0, height)
            x1 = rng.randint(0, width // 2)
            x2 = x1 + rng.randint(100, 400)
            brightness = rng.randint(150, 255)
            draw.line([(x1, y), (x2, y)], fill=(brightness, brightness, brightness, rng.randint(30, 80)), width=rng.randint(1, 3))

    # Vertical bars for claustrophobic/prison
    if any(t in tone_tags for t in ["claustrophobic", "institutional"]):
        bar_count = rng.randint(5, 10)
        for i in range(bar_count):
            x = width // (bar_count + 1) * (i + 1) + rng.randint(-10, 10)
            draw.line([(x, 0), (x, height)], fill=(0, 0, 0, rng.randint(40, 100)), width=rng.randint(3, 8))

    # Stars for space/ethereal
    if any(t in tone_tags for t in ["ethereal", "awe", "epic"]):
        for _ in range(rng.randint(30, 80)):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            r = rng.randint(1, 3)
            b = rng.randint(180, 255)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, b, rng.randint(80, 200)))

    # Warm glow for intimate/romantic
    if any(t in tone_tags for t in ["intimate", "romantic", "warm"]):
        cx, cy = width // 2, height // 2
        for radius in range(min(width, height) // 3, 0, -5):
            alpha = int(40 * (1 - radius / (min(width, height) // 3)))
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                         fill=(255, 200, 100, alpha))

    # Rain lines
    if any(t in tone_tags for t in ["grief", "somber"]) or "rain" in str(tone_tags):
        for _ in range(rng.randint(40, 100)):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            length = rng.randint(10, 30)
            draw.line([(x, y), (x + 2, y + length)], fill=(180, 190, 200, rng.randint(30, 80)), width=1)

    # Light beam from top for dramatic/tense
    if any(t in tone_tags for t in ["dramatic", "tense"]):
        cx = width // 2 + rng.randint(-100, 100)
        for i in range(60):
            alpha = max(0, 50 - i)
            x_spread = i * 3
            draw.polygon(
                [(cx, 0), (cx - x_spread, min(i * 10, height)), (cx + x_spread, min(i * 10, height))],
                fill=(255, 240, 200, alpha)
            )


def generate_image(scene, output_dir):
    """Generate a single placeholder image for a scene."""
    filename = scene["filename"]
    description = scene["description"]
    tone_tags = scene["tone_tags"]
    scene_id = scene["id"]

    top_color, bot_color = get_palette(tone_tags)

    # Create base image with gradient
    img = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # Diagonal gradient for more visual interest
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Blend based on diagonal position
            t = (x / WIDTH * 0.4 + y / HEIGHT * 0.6)
            t = max(0.0, min(1.0, t))
            color = blend(top_color, bot_color, t)
            img.putpixel((x, y), color + (255,))

    # Add texture overlay
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    add_texture(overlay_draw, WIDTH, HEIGHT, tone_tags, hash(scene_id))
    img = Image.alpha_composite(img, overlay)

    # Add vignette effect
    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vignette_draw = ImageDraw.Draw(vignette)
    cx, cy = WIDTH // 2, HEIGHT // 2
    max_dist = math.sqrt(cx ** 2 + cy ** 2)
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            alpha = int(min(255, max(0, (dist / max_dist) ** 2 * 180)))
            vignette_draw.rectangle([x, y, x + 1, y + 1], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img, vignette)

    # Add text overlay
    text_overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_overlay)

    # Try to use a decent font
    font_large = None
    font_small = None
    font_tag = None
    for font_path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(font_path):
            try:
                font_large = ImageFont.truetype(font_path, 28)
                font_small = ImageFont.truetype(font_path, 16)
                font_tag = ImageFont.truetype(font_path, 14)
                break
            except Exception:
                continue

    if font_large is None:
        font_large = ImageFont.load_default()
        font_small = font_large
        font_tag = font_large

    # Scene ID badge
    badge_text = scene_id.upper()
    bbox = text_draw.textbbox((0, 0), badge_text, font=font_small)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    text_draw.rounded_rectangle([20, 20, 40 + bw, 36 + bh], radius=6, fill=(0, 0, 0, 140))
    text_draw.text((30, 25), badge_text, fill=(255, 255, 255, 220), font=font_small)

    # Filename as title
    title = filename.replace(".jpg", "").replace("_", " ").title()
    bbox = text_draw.textbbox((0, 0), title, font=font_large)
    tw = bbox[2] - bbox[0]
    text_draw.text(((WIDTH - tw) // 2, HEIGHT // 2 - 30), title, fill=(255, 255, 255, 200), font=font_large)

    # Draw description (wrapped)
    words = description.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        bbox = text_draw.textbbox((0, 0), test, font=font_small)
        if bbox[2] - bbox[0] > WIDTH - 80:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    y_offset = HEIGHT // 2 + 10
    for line in lines[:3]:
        bbox = text_draw.textbbox((0, 0), line, font=font_small)
        lw = bbox[2] - bbox[0]
        text_draw.text(((WIDTH - lw) // 2, y_offset), line, fill=(220, 220, 220, 180), font=font_small)
        y_offset += 22

    # Tone tags at bottom
    tag_str = "  ".join(f"#{t}" for t in tone_tags)
    bbox = text_draw.textbbox((0, 0), tag_str, font=font_tag)
    tag_w = bbox[2] - bbox[0]
    text_draw.text(((WIDTH - tag_w) // 2, HEIGHT - 40), tag_str, fill=(200, 200, 200, 150), font=font_tag)

    img = Image.alpha_composite(img, text_overlay)

    # Convert to RGB and save as JPEG
    final = img.convert("RGB")
    out_path = os.path.join(output_dir, filename)
    final.save(out_path, "JPEG", quality=90)
    return out_path


def main():
    os.makedirs(SCENE_DIR, exist_ok=True)

    with open(METADATA_PATH, "r") as f:
        scenes = json.load(f)

    print(f"Generating {len(scenes)} placeholder images...")
    for i, scene in enumerate(scenes, 1):
        path = generate_image(scene, SCENE_DIR)
        print(f"  [{i:2d}/{len(scenes)}] {scene['filename']}")

    print(f"\nDone! {len(scenes)} images saved to {SCENE_DIR}")


if __name__ == "__main__":
    main()

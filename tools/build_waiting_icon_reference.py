from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "imagegen" / "waiting_icon_20260922"
OUT.mkdir(parents=True, exist_ok=True)

frame = Image.open(ROOT / "tools" / "assets" / "RMC-assets-pack" / "Focus Frames" / "Shield.png").convert("RGBA")
tower = Image.open(ROOT / "tools" / "assets" / "vanilla-cutouts" / "Watch post.png").convert("RGBA")
flag = Image.open(ROOT / ".." / "kr_icon_component_library" / "extracted" / "components" / "flags_colored" / "military_training__02__3.png").convert("RGBA")

canvas = Image.new("RGBA", (1024, 1024), (22, 25, 24, 255))

def fit(image, size):
    image = image.copy()
    scale = min(size[0] / image.width, size[1] / image.height)
    image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
    return image

frame = fit(frame, (900, 900))
tower = fit(tower, (460, 650))
flag = fit(flag, (300, 220))

# Keep the flag behind the lookout, with the shield as the rear frame.
canvas.alpha_composite(frame, ((1024 - frame.width) // 2, (1024 - frame.height) // 2))
flag = ImageEnhance.Color(flag).enhance(0.8)
flag = ImageEnhance.Contrast(flag).enhance(0.9)
canvas.alpha_composite(flag, (360, 250))
canvas.alpha_composite(tower, ((1024 - tower.width) // 2, 215))

# A restrained painted grain helps the API preserve the old illustrated game-icon feel.
canvas = canvas.filter(ImageFilter.GaussianBlur(radius=0.25))
canvas.save(OUT / "waiting_icon_material_reference.png")

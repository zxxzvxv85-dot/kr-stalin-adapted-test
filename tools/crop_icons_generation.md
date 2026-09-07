# Crop Icon Generation Record

Date: 2026-09-07

- Mode: ImageGen bundled CLI/API, user confirmed service quota use before generation.
- Requested model: `gpt-image-2`; no model fallback.
- Five independent prompts, one image each. Requested 1024x1024; the configured service returned five 1254x1254 PNGs. Actual dimensions were measured rather than inferred from the request.
- Generated files: `output/imagegen/crop-icons-20260907/{wheat,rye,beet,flax,cotton}.png`.
- Native assets: `gfx/interface/RUS_agri_crops/RUS_agri_{wheat,rye,beet,flax,cotton}.png`, 64x64 RGBA; GUI scale 0.5, displayed at 32x32.
- Used bundled `remove_chroma_key.py` with corner sampling, soft matte, thresholds 28/100, and spill cleanup; then `tools/build_agri_crop_icons.py` for crop, fit, and preview.
- Validation: all five inspected together at enlarged and native sizes on dark/light backgrounds; nonblank alpha, no detected opaque magenta spill, no frames/text, distinguishable crop silhouettes. Rye is intentionally narrower than wheat. GUI/GFX CWT file checks green; new asset references resolve. Native HOI4 rendering is not yet verified.
- Preview: `output/imagegen/crop-icons-20260907/crop-icons-preview.png`; detailed metrics alongside in `validation.json`.

## Executed CLI Command

```powershell
python 'C:/Users/Administrator/.codex/skills/.system/imagegen/scripts/image_gen.py' generate-batch --input tmp/imagegen/crop-icons-20260907.jsonl --out-dir output/imagegen/crop-icons-20260907 --model gpt-image-2 --size 1024x1024 --quality medium --concurrency 5 --max-attempts 1 --no-augment
```

The temporary JSONL was removed after use; its exact content is archived at `tools/crop_icon_prompts.jsonl`. Use that path for a reproducible new batch and a new output folder to avoid overwriting originals.

## Final Prompts

### wheat.png

```text
Use case: stylized-concept
Asset type: a single crop resource icon for a historical grand strategy game, shown at only 32x32 pixels.
Primary request: Paint ONLY the crop described below as a compact, instantly recognizable inventory icon.
Scene/backdrop: perfectly uniform vivid magenta RGB(255,0,255), a flat chroma-key matte for local removal. No shadows on the background, no gradient or vignette, no magenta anywhere on the plant.
Style/medium: hand-painted old strategy-game resource sprite, restrained natural material shading, broad light and dark planes, subtle dark contour. Neither photorealistic botanical illustration nor modern flat vector nor pixel art.
Composition: ONE centered compact cluster, fully visible, occupying approximately 80% of the square, 10% empty margin on every edge. Big robust forms and short thick stems. A clean silhouette with very few internal details, legible at 32 pixels.
Lighting: clear upper-left warm-neutral highlights, deep localized lower-right shadows, strong volume without fine textures.
Constraints: no text, numbers, badges, wreaths, frames, gears, flags, soil, basket, scenery, watermark, loose detached pieces, tiny veins or hairline details.
Subject: Three short, broad, plump mature golden wheat ears fanning gently outward, each with only a few large overlapping kernels, short ochre stems joined at the bottom. The middle ear tallest. Warm gold and pale straw highlights. Make the heads visibly thick and rounded, with no long whiskers.
```

### rye.png

```text
Use case: stylized-concept
Asset type: a single crop resource icon for a historical grand strategy game, shown at only 32x32 pixels.
Primary request: Paint ONLY the crop described below as a compact, instantly recognizable inventory icon.
Scene/backdrop: perfectly uniform vivid magenta RGB(255,0,255), a flat chroma-key matte for local removal. No shadows on the background, no gradient or vignette, no magenta anywhere on the plant.
Style/medium: hand-painted old strategy-game resource sprite, restrained natural material shading, broad light and dark planes, subtle dark contour. Neither photorealistic botanical illustration nor modern flat vector nor pixel art.
Composition: ONE centered compact cluster, fully visible, occupying approximately 80% of the square, 10% empty margin on every edge. Big robust forms and short thick stems. A clean silhouette with very few internal details, legible at 32 pixels.
Lighting: clear upper-left warm-neutral highlights, deep localized lower-right shadows, strong volume without fine textures.
Constraints: no text, numbers, badges, wreaths, frames, gears, flags, soil, basket, scenery, watermark, loose detached pieces, tiny veins or hairline details.
Subject: Two tall slender mature rye ears leaning apart in a narrow V, muted silver-straw and olive-gold color, long tapered narrow heads and a few bold awns integrated into the silhouette, short joined stems. Distinguish rye from broad golden wheat by its slim spear-shaped heads and cool pale highlights. Do not make a fluffy mass of fine bristles.
```

### beet.png

```text
Use case: stylized-concept
Asset type: a single crop resource icon for a historical grand strategy game, shown at only 32x32 pixels.
Primary request: Paint ONLY the crop described below as a compact, instantly recognizable inventory icon.
Scene/backdrop: perfectly uniform vivid magenta RGB(255,0,255), a flat chroma-key matte for local removal. No shadows on the background, no gradient or vignette, no magenta anywhere on the plant.
Style/medium: hand-painted old strategy-game resource sprite, restrained natural material shading, broad light and dark planes, subtle dark contour. Neither photorealistic botanical illustration nor modern flat vector nor pixel art.
Composition: ONE centered compact cluster, fully visible, occupying approximately 80% of the square, 10% empty margin on every edge. Big robust forms and short thick stems. A clean silhouette with very few internal details, legible at 32 pixels.
Lighting: clear upper-left warm-neutral highlights, deep localized lower-right shadows, strong volume without fine textures.
Constraints: no text, numbers, badges, wreaths, frames, gears, flags, soil, basket, scenery, watermark, loose detached pieces, tiny veins or hairline details.
Subject: One harvested sugar beet, a large ivory-white tapered bulbous root with a single short pointed tip and two broad dark-green leaves at its crown. The white root fills most of the icon and the leaves are compact and chunky. Sugar beet, NOT a round red table beet, radish or carrot.
```

### flax.png

```text
Use case: stylized-concept
Asset type: a single crop resource icon for a historical grand strategy game, shown at only 32x32 pixels.
Primary request: Paint ONLY the crop described below as a compact, instantly recognizable inventory icon.
Scene/backdrop: perfectly uniform vivid magenta RGB(255,0,255), a flat chroma-key matte for local removal. No shadows on the background, no gradient or vignette, no magenta anywhere on the plant.
Style/medium: hand-painted old strategy-game resource sprite, restrained natural material shading, broad light and dark planes, subtle dark contour. Neither photorealistic botanical illustration nor modern flat vector nor pixel art.
Composition: ONE centered compact cluster, fully visible, occupying approximately 80% of the square, 10% empty margin on every edge. Big robust forms and short thick stems. A clean silhouette with very few internal details, legible at 32 pixels.
Lighting: clear upper-left warm-neutral highlights, deep localized lower-right shadows, strong volume without fine textures.
Constraints: no text, numbers, badges, wreaths, frames, gears, flags, soil, basket, scenery, watermark, loose detached pieces, tiny veins or hairline details.
Subject: A compact sprig of flax with two prominent sky-blue five-petalled flowers, tiny ochre centers, a few short joined sage-green stems and two simple narrow leaves. Make the blue flower faces large and clearly distinct, one slightly higher than the other; avoid a delicate tangled bouquet or purple flowers.
```

### cotton.png

```text
Use case: stylized-concept
Asset type: a single crop resource icon for a historical grand strategy game, shown at only 32x32 pixels.
Primary request: Paint ONLY the crop described below as a compact, instantly recognizable inventory icon.
Scene/backdrop: perfectly uniform vivid magenta RGB(255,0,255), a flat chroma-key matte for local removal. No shadows on the background, no gradient or vignette, no magenta anywhere on the plant.
Style/medium: hand-painted old strategy-game resource sprite, restrained natural material shading, broad light and dark planes, subtle dark contour. Neither photorealistic botanical illustration nor modern flat vector nor pixel art.
Composition: ONE centered compact cluster, fully visible, occupying approximately 80% of the square, 10% empty margin on every edge. Big robust forms and short thick stems. A clean silhouette with very few internal details, legible at 32 pixels.
Lighting: clear upper-left warm-neutral highlights, deep localized lower-right shadows, strong volume without fine textures.
Constraints: no text, numbers, badges, wreaths, frames, gears, flags, soil, basket, scenery, watermark, loose detached pieces, tiny veins or hairline details.
Subject: A short branch with two large open cotton bolls, each rendered as three or four bold round ivory-white lobes, with a few chestnut-brown triangular husks and a short dark stem. One boll higher and slightly left, one lower and right. Clean broad white masses, no hair fibers or texture noise.
```

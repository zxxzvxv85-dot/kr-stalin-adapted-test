from __future__ import annotations

from pathlib import Path

from PIL import Image

import process_bolshevik_web_icons_v28 as processor


OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output/imagegen"

processor.DEST_DIR = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_final_100px_v29"
processor.PREVIEW_DARK = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_final_dark_v29.png"
processor.PREVIEW_WHITE = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_final_white_v29.png"
processor.COMPARISON = OUTPUT_DIR / "RUS_kamenev_bolshevik_web_v29_vs_v28_vs_official.png"

processor.TARGET_CONTENT_SIZE = 82
processor.RESAMPLING = Image.Resampling.LANCZOS
processor.SHARPEN_RADIUS = 0.55
processor.SHARPEN_PERCENT = 70
processor.SHARPEN_THRESHOLD = 2
processor.VERSION_LABEL = "缩小锐化 V29"


if __name__ == "__main__":
    processor.main()

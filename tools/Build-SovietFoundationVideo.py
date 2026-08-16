#!/usr/bin/env python3
"""Build the Soviet foundation cinematic atlases and audio.

The source used for the checked-in assets is the 01:44:00-01:44:43 segment
from https://www.youtube.com/watch?v=390tSoW927o (Lenin in October).
"""

from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image


FPS = 25
FRAME_WIDTH = 496
FRAME_HEIGHT = 360
FRAMES_PER_ATLAS = 32
ATLAS_MARKER_SLOTS = 1
DEFAULT_DURATION = 43.0


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Local source video")
    parser.add_argument("--ffmpeg", required=True, type=Path)
    parser.add_argument("--mod-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--start", default="0")
    parser.add_argument("--duration", default=DEFAULT_DURATION, type=float)
    args = parser.parse_args()

    source = args.source.resolve()
    ffmpeg = args.ffmpeg.resolve()
    mod_root = args.mod_root.resolve()
    atlas_dir = mod_root / "gfx" / "interface" / "rus_soviet_foundation_video"
    audio_dir = mod_root / "music"
    atlas_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Two identical frames let the black screen use a 43-second native GUI
    # animation timer and become transparent exactly when the film ends.
    black_strip = Image.new("RGB", (128, 64), "black")
    try:
        black_strip.save(atlas_dir / "RUS_soviet_foundation_video_black.png")
    finally:
        black_strip.close()

    expected_frames = round(args.duration * FPS)
    atlas_count = math.ceil(expected_frames / FRAMES_PER_ATLAS)

    with tempfile.TemporaryDirectory(prefix="rus_soviet_foundation_video_") as temp_name:
        temp_dir = Path(temp_name)
        frame_pattern = temp_dir / "frame_%04d.png"

        run(
            [
                str(ffmpeg),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(args.start),
                "-i",
                str(source),
                "-t",
                str(args.duration),
                "-vf",
                (
                    f"fps={FPS},"
                    f"scale={FRAME_WIDTH}:{FRAME_HEIGHT}:force_original_aspect_ratio=decrease,"
                    f"pad={FRAME_WIDTH}:{FRAME_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black"
                ),
                str(frame_pattern),
            ]
        )

        frames = sorted(temp_dir.glob("frame_*.png"))
        if len(frames) < expected_frames:
            raise RuntimeError(f"Expected {expected_frames} frames, found {len(frames)}")
        frames = frames[:expected_frames]

        for stale in atlas_dir.glob("RUS_soviet_foundation_video_*.dds"):
            stale.unlink()

        last_frame = Image.open(frames[-1]).convert("RGB")
        try:
            for atlas_index in range(atlas_count):
                atlas = Image.new(
                    "RGB",
                    (FRAME_WIDTH * (FRAMES_PER_ATLAS + ATLAS_MARKER_SLOTS), FRAME_HEIGHT),
                    "black",
                )
                try:
                    marker_colour = (
                        round((atlas_index % 32) * 255 / 31),
                        255 if atlas_index >= 32 else 0,
                        0,
                    )
                    marker = Image.new("RGB", (FRAME_WIDTH, FRAME_HEIGHT), marker_colour)
                    try:
                        atlas.paste(marker, (0, 0))
                    finally:
                        marker.close()

                    for local_index in range(FRAMES_PER_ATLAS):
                        frame_index = atlas_index * FRAMES_PER_ATLAS + local_index
                        frame_x = (local_index + ATLAS_MARKER_SLOTS) * FRAME_WIDTH
                        if frame_index < len(frames):
                            with Image.open(frames[frame_index]) as frame:
                                atlas.paste(frame.convert("RGB"), (frame_x, 0))
                        else:
                            atlas.paste(last_frame, (frame_x, 0))

                    output = atlas_dir / f"RUS_soviet_foundation_video_{atlas_index:02d}.dds"
                    atlas.save(output, pixel_format="DXT1")
                finally:
                    atlas.close()
        finally:
            last_frame.close()

        audio_temp = temp_dir / "RUS_soviet_foundation_video_audio.ogg"
        run(
            [
                str(ffmpeg),
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                str(args.start),
                "-i",
                str(source),
                "-t",
                str(args.duration),
                "-vn",
                "-ac",
                "2",
                "-ar",
                "44100",
                "-c:a",
                "libvorbis",
                "-q:a",
                "4",
                str(audio_temp),
            ]
        )
        shutil.copy2(audio_temp, audio_dir / audio_temp.name)

    print(f"Built {atlas_count} atlases ({expected_frames} frames at {FPS} FPS)")


if __name__ == "__main__":
    main()

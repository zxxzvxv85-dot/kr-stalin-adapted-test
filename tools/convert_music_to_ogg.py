#!/usr/bin/env python3
"""Convert a source track (MP3/WAV/FLAC/...) into the mod's OGG Vorbis convention.

Every music file the mod ships is 44.1 kHz stereo Vorbis, so anything else is
resampled with a polyphase filter and encoded at the same quality band the existing
radio tracks use (~180 kbps). Requires soundfile (libsndfile) and scipy; both can be
installed into a scratch directory with:

    python -m pip install --target tmp/pyaudio_libs soundfile scipy

Usage:
    PYTHONPATH=tmp/pyaudio_libs python tools/convert_music_to_ogg.py <source> <output.ogg>
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

RATE = 44100
CHUNK = 1 << 18             # libsndfile aborts with a stack overflow on one huge write
# libsndfile maps a *higher* compression level to a *smaller* Vorbis file; 0.3 lands at
# roughly 175 kbps, the same band as the radio tracks the mod already ships.
COMPRESSION = 0.3


def convert(source: pathlib.Path, target: pathlib.Path) -> None:
    info = sf.info(source)
    data, rate = sf.read(source, dtype="float32", always_2d=True)
    if rate != RATE:
        divisor = np.gcd(int(rate), RATE)
        data = resample_poly(data, RATE // divisor, int(rate) // divisor, axis=0)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    peak = float(np.max(np.abs(data))) if data.size else 0.0
    if peak > 1.0:                                  # never encode clipped samples
        data = data / peak
    target.parent.mkdir(parents=True, exist_ok=True)
    with sf.SoundFile(target, "w", RATE, data.shape[1], format="OGG", subtype="VORBIS",
                      compression_level=COMPRESSION) as handle:
        for start in range(0, len(data), CHUNK):
            handle.write(data[start:start + CHUNK])
    out = sf.info(target)
    rms = float(np.sqrt(np.mean(data.astype(np.float64) ** 2)))
    print(
        f"{source.name}: {info.samplerate}Hz {info.channels}ch {info.duration:.1f}s"
        f" -> {target.name}: {out.samplerate}Hz {out.channels}ch {out.duration:.1f}s"
        f" rms={rms:.4f} peak={peak:.3f} bytes={target.stat().st_size}"
    )


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    source, target = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
    if not source.is_file():
        print(f"missing source: {source}")
        return 2
    convert(source, target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

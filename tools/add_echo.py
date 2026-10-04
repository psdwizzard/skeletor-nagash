#!/usr/bin/env python3
"""Add a sepulchral echo to the fitted takes (non-destructive).

Reads work/gen/minimax_fit/*.wav -> writes work/gen/minimax_echo/*.wav.
Pads the tail first so the echo can ring out (clip length is free in-engine),
then re-matches loudness to the original line so the game mix stays balanced.

Usage: add_echo.py [--preset light|heavy]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import glob
import json
import os
import subprocess

PRESETS = {
    # in_gain : out_gain : delays(ms) : decays
    "light": "aecho=0.9:0.9:66|132:0.32|0.16",
    "heavy": "aecho=0.85:0.9:70|150|240:0.42|0.28|0.16",
}


def lufs(path):
    r = subprocess.run(
        ["ffmpeg", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    block = r[r.rindex("{"):r.rindex("}") + 1]
    return float(json.loads(block)["input_i"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", default="light", choices=list(PRESETS))
    ap.add_argument("--indir", default="work/gen/minimax_fit")
    ap.add_argument("--outdir", default="work/gen/minimax_echo")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    echo = PRESETS[a.preset]

    def work(src):
        wid = os.path.basename(src).split(".")[0]
        out = os.path.join(a.outdir, f"{wid}.wav")
        if os.path.exists(out):
            return "cached"
        target = lufs(f"work/original_wav/{wid}.wav")
        af = (f"apad=pad_dur=0.45,{echo},"
              f"loudnorm=I={max(min(target, -8), -40):.1f}:TP=-1.0:LRA=11")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", af,
                        "-ar", "48000", "-ac", "1", "-sample_fmt", "s16", out],
                       check=True)
        return "ok"

    srcs = sorted(glob.glob(os.path.join(a.indir, "*.wav")))
    with cf.ThreadPoolExecutor(8) as ex:
        results = list(ex.map(work, srcs))
    print(f"preset={a.preset}: {results.count('ok')} processed, "
          f"{results.count('cached')} cached, total {len(srcs)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fit generated takes to their originals: duration check, optional time-stretch,
loudness match, resample to 48 kHz mono 16-bit.

Usage: postprocess.py --model <name> [--stretch-limit 1.15] [--report-only]

Reads work/gen/<model>/<id>.wav, writes work/gen/<model>_fit/<id>.wav.
Flags lines whose generated/original duration ratio is outside 0.85-1.20 even
after stretching — those need their text shortened/lengthened and a re-run.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess


def probe(path, entries="format=duration"):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()


def lufs(path):
    r = subprocess.run(
        ["ffmpeg", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    block = r[r.rindex("{"):r.rindex("}") + 1]
    return float(json.loads(block)["input_i"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--stretch-limit", type=float, default=1.15)
    ap.add_argument("--ratio-lo", type=float, default=0.85)
    ap.add_argument("--ratio-hi", type=float, default=1.20)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()

    manifest = json.load(open("work/manifest.json"))
    indir = f"work/gen/{a.model}"
    outdir = f"work/gen/{a.model}_fit"
    os.makedirs(outdir, exist_ok=True)

    flagged, fitted = [], 0
    for m in manifest:
        wid = m["wem_id"]
        gen = f"{indir}/{wid}.wav"
        if not os.path.exists(gen):
            continue
        orig_d = m["duration_s"]
        gen_d = float(probe(gen))
        ratio = gen_d / orig_d if orig_d else 1.0
        # tempo factor to land exactly on original duration
        tempo = ratio  # atempo >1 speeds up (shortens)
        needed = max(min(tempo, a.stretch_limit), 1 / a.stretch_limit)
        final_ratio = (gen_d / needed) / orig_d if orig_d else 1.0
        status = "ok"
        if not (a.ratio_lo <= final_ratio <= a.ratio_hi):
            status = "text_edit_needed"
            flagged.append({"wem_id": wid, "orig_s": orig_d, "gen_s": round(gen_d, 2),
                            "ratio": round(ratio, 2)})
        m["gen_duration_s"] = round(gen_d, 3)
        m["fit_status"] = status
        if a.report_only:
            continue
        out = f"{outdir}/{wid}.wav"
        target_lufs = lufs(f"work/original_wav/{wid}.wav")
        af = []
        if abs(needed - 1.0) > 0.02 and status == "ok":
            af.append(f"atempo={needed:.4f}")
        af.append(f"loudnorm=I={max(min(target_lufs, -8), -40):.1f}:TP=-1.0:LRA=11")
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-i", gen, "-af", ",".join(af),
             "-ar", "48000", "-ac", "1", "-sample_fmt", "s16", out], check=True)
        fitted += 1

    json.dump(manifest, open("work/manifest.json", "w"), indent=1)
    print(f"fitted {fitted}, flagged for text edit: {len(flagged)}")
    for f in flagged[:40]:
        print(f)


if __name__ == "__main__":
    main()

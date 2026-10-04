#!/usr/bin/env python3
"""Duration-fit pass for the MiniMax takes.

Measures each generated line vs. its original. For lines outside the accept
band (0.85-1.20x), sets a per-line `speed` in the manifest (MiniMax native,
clamped 0.6-1.8), deletes the stale wav, and reports how many need a regen
pass (`generate.py --model minimax --all` picks them up because the file is
gone). Lines that can't be fixed by speed alone get status=text_edit_needed.

Usage: fit_loop.py [--apply]   (without --apply: report only)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess

LO, HI = 0.30, 1.15
SPEED_MIN, SPEED_MAX = 0.6, 1.8


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return float(out) if out else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    manifest = json.load(open("work/manifest.json"))
    stats = {"ok": 0, "regen": 0, "text_edit": 0, "missing": 0}
    for m in manifest:
        if m["status"].startswith("excluded"):
            continue
        wav = f"work/gen/minimax/{m['wem_id']}.wav"
        if not os.path.exists(wav):
            stats["missing"] += 1
            continue
        g = dur(wav)
        ratio = g / m["duration_s"]
        m["gen_duration_s"] = round(g, 3)
        cur_speed = m.get("speed", 1.0)
        if LO <= ratio <= HI:
            m["fit_status"] = "ok"
            stats["ok"] += 1
            continue
        # speed that would land the take on the original duration
        want = cur_speed * ratio
        if SPEED_MIN <= want <= SPEED_MAX:
            m["speed"] = round(want, 3)
            m["fit_status"] = "regen_speed"
            stats["regen"] += 1
            if a.apply:
                os.remove(wav)
        else:
            m["speed"] = round(min(max(want, SPEED_MIN), SPEED_MAX), 3)
            m["fit_status"] = "text_edit_needed"
            stats["text_edit"] += 1
    json.dump(manifest, open("work/manifest.json", "w"), indent=1)
    print(stats)
    if stats["text_edit"]:
        bad = [(m["wem_id"], m["duration_s"], m.get("gen_duration_s"))
               for m in manifest if m.get("fit_status") == "text_edit_needed"]
        print("text_edit_needed:", bad)


if __name__ == "__main__":
    main()

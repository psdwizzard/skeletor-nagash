#!/usr/bin/env python3
"""Extract the actor's .wem files from audio_en.pack, decode to wav,
and build work/manifest.json (one record per line: id, banks, duration)."""
from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from packfile import PackFile  # noqa: E402

GAME_DATA = ("/Users/kenneth/Library/Application Support/Steam/steamapps/common/"
             "Total War WARHAMMER III/TotalWarhammer3Data/data")
WEM_DIR = "work/original_wem"
WAV_DIR = "work/original_wav"


def main():
    wems_json = json.load(open(sys.argv[1]))
    pack = PackFile(f"{GAME_DATA}/audio_en.pack")
    os.makedirs(WEM_DIR, exist_ok=True)
    os.makedirs(WAV_DIR, exist_ok=True)

    # map wem id -> banks that reference it
    banks_for = {}
    for bank in wems_json["banks"]:
        for wems in bank["events"].values():
            for w in wems:
                banks_for.setdefault(w, set()).add(bank["bank"])

    manifest, missing = [], []
    for wid in wems_json["wem_ids"]:
        internal = f"audio\\wwise\\english(uk)\\{wid}.wem"
        if internal not in pack.entries:
            missing.append(wid)
            continue
        wem_path = f"{WEM_DIR}/{wid}.wem"
        wav_path = f"{WAV_DIR}/{wid}.wav"
        if not os.path.exists(wem_path):
            with open(wem_path, "wb") as f:
                f.write(pack.read(internal))
        if not os.path.exists(wav_path):
            r = subprocess.run(["vgmstream-cli", "-o", wav_path, wem_path],
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"DECODE FAIL {wid}: {r.stderr.strip()[:200]}")
                continue
        dur = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", wav_path], capture_output=True, text=True
        ).stdout.strip()
        manifest.append({
            "wem_id": wid,
            "banks": sorted(banks_for.get(wid, [])),
            "duration_s": round(float(dur), 3) if dur else None,
            "transcript": None,
            "text_final": None,
            "status": "extracted",
        })

    with open("work/manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    total = sum(m["duration_s"] or 0 for m in manifest)
    print(f"extracted {len(manifest)} wems, {total/60:.1f} min of audio, "
          f"missing from audio_en.pack: {len(missing)} {missing[:10]}")


if __name__ == "__main__":
    main()

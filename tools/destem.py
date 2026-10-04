#!/usr/bin/env python3
"""Isolate vocals from the Skeletor reference candidates via fal-ai/demucs.

Reads work/ref/candidates/*.wav (+ reference_main.wav), writes vocals-only
versions to work/ref/clean/<name>.wav. Env: FAL_KEY.
"""
from __future__ import annotations

import concurrent.futures as cf
import glob
import os
import subprocess
import urllib.request

import fal_client

OUT = "work/ref/clean"


def destem(path):
    name = os.path.basename(path)
    out = os.path.join(OUT, name)
    if os.path.exists(out):
        return name, "cached"
    try:
        url = fal_client.upload_file(path)
        r = fal_client.subscribe("fal-ai/demucs", arguments={
            "audio_url": url,
            "model": "htdemucs_ft",
            "stems": ["vocals"],
            "shifts": 2,
            "output_format": "wav",
        })
        voc = r["vocals"]["url"] if isinstance(r.get("vocals"), dict) else r["vocals"]
        tmp = out + ".dl"
        urllib.request.urlretrieve(voc, tmp)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp,
                        "-ar", "44100", "-ac", "1", out], check=True)
        os.remove(tmp)
        return name, "ok"
    except Exception as e:  # noqa: BLE001
        return name, f"ERR {e}"


def main():
    os.makedirs(OUT, exist_ok=True)
    targets = sorted(glob.glob("work/ref/candidates/*.wav"))
    targets.append("work/ref/reference_main.wav")
    with cf.ThreadPoolExecutor(5) as ex:
        for name, status in ex.map(destem, targets):
            print(name, status, flush=True)


if __name__ == "__main__":
    main()

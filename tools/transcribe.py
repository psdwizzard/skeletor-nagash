#!/usr/bin/env python3
"""Transcribe work/original_wav/*.wav into the manifest with mlx-whisper."""
import json

import mlx_whisper

MODEL = "mlx-community/whisper-large-v3-turbo"

manifest = json.load(open("work/manifest.json"))
done = 0
for m in manifest:
    if m.get("transcript"):
        done += 1
        continue
    wav = f"work/original_wav/{m['wem_id']}.wav"
    r = mlx_whisper.transcribe(wav, path_or_hf_repo=MODEL, language="en")
    m["transcript"] = r["text"].strip()
    done += 1
    if done % 25 == 0:
        json.dump(manifest, open("work/manifest.json", "w"), indent=1)
        print(f"{done}/{len(manifest)}", flush=True)

json.dump(manifest, open("work/manifest.json", "w"), indent=1)
print(f"done: {done}/{len(manifest)} transcribed")

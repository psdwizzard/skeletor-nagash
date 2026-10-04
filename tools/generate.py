#!/usr/bin/env python3
"""Generate cloned-voice audio for manifest lines via fal.ai.

Usage:
  generate.py --model <minimax|chatterboxhd|f5|indextts2> \
      --ref work/ref/reference_main.wav [--ref-text work/ref/reference_main.txt] \
      [--ids 542776923,775047685] [--all] [--concurrency 8]

Env: FAL_KEY (source tools/falenv.sh). Reads/writes work/manifest.json
('text_final' falls back to 'transcript'). Output: work/gen/<model>/<wem_id>.wav
(44.1/48k source rate as delivered; normalization happens later in postprocess).
Resume-safe: skips ids whose output file already exists.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import urllib.request

import fal_client

STATE_PATH = "work/gen/state.json"  # remembers ref upload url + minimax voice id


def load_state():
    return json.load(open(STATE_PATH)) if os.path.exists(STATE_PATH) else {}


def save_state(st):
    os.makedirs("work/gen", exist_ok=True)
    json.dump(st, open(STATE_PATH, "w"), indent=1)


def ensure_ref_url(st, ref_path):
    key = f"ref_url::{os.path.abspath(ref_path)}::{os.path.getmtime(ref_path)}"
    if st.get("ref_key") == key and st.get("ref_url"):
        return st["ref_url"]
    url = fal_client.upload_file(ref_path)
    st["ref_key"], st["ref_url"] = key, url
    save_state(st)
    return url


def ensure_minimax_voice(st, ref_url):
    if st.get("minimax_voice_id"):
        return st["minimax_voice_id"]
    r = fal_client.subscribe("fal-ai/minimax/voice-clone", arguments={
        "audio_url": ref_url,
        "noise_reduction": True,
        "need_volume_normalization": True,
    })
    vid = r["custom_voice_id"]
    st["minimax_voice_id"] = vid
    save_state(st)
    return vid


def _find_url(resp):
    """Models disagree on response shape; dig out the first audio url."""
    for key in ("audio", "audio_url", "audio_file"):
        v = resp.get(key)
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        if isinstance(v, str) and v.startswith("http"):
            return v
    raise KeyError(f"no audio url in response keys={list(resp)}")


def gen_one(model, text, ref_url, ref_text, extra):
    if model == "minimax":
        r = fal_client.subscribe("fal-ai/minimax/speech-2.8-hd", arguments={
            "prompt": text,
            "voice_setting": {"voice_id": extra["voice_id"],
                              "speed": extra.get("speed", 1.0)},
            "audio_setting": {"format": "flac", "sample_rate": 44100},
            "output_format": "url",
        })
        return _find_url(r)
    if model == "chatterboxhd":
        r = fal_client.subscribe("resemble-ai/chatterboxhd/text-to-speech", arguments={
            "text": text, "audio_url": ref_url,
            "exaggeration": extra.get("exaggeration", 0.6),
            "cfg": extra.get("cfg", 0.35),
            "high_quality_audio": True, "seed": 42,
        })
        return _find_url(r)
    if model == "f5":
        args = {"gen_text": text, "ref_audio_url": ref_url,
                "model_type": "F5-TTS", "remove_silence": True}
        if ref_text:
            args["ref_text"] = ref_text
        r = fal_client.subscribe("fal-ai/f5-tts", arguments=args)
        return _find_url(r)
    if model == "indextts2":
        r = fal_client.subscribe("fal-ai/index-tts-2/text-to-speech", arguments={
            "prompt": text, "audio_url": ref_url,
        })
        return _find_url(r)
    raise ValueError(model)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True,
                    choices=["minimax", "chatterboxhd", "f5", "indextts2"])
    ap.add_argument("--ref", required=True)
    ap.add_argument("--ref-text")
    ap.add_argument("--ids")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--concurrency", type=int, default=8)
    a = ap.parse_args()

    manifest = json.load(open("work/manifest.json"))
    if a.ids:
        want = {int(x) for x in a.ids.split(",")}
        lines = [m for m in manifest if m["wem_id"] in want]
    elif a.all:
        lines = [m for m in manifest if not m["status"].startswith("excluded")]
    else:
        sys.exit("pass --ids or --all")

    ref_text = open(a.ref_text).read().strip() if a.ref_text else None
    st = load_state()
    ref_url = ensure_ref_url(st, a.ref)
    extra = {}
    if a.model == "minimax":
        extra["voice_id"] = ensure_minimax_voice(st, ref_url)

    outdir = f"work/gen/{a.model}"
    os.makedirs(outdir, exist_ok=True)

    def work(m):
        out = f"{outdir}/{m['wem_id']}.wav"
        if os.path.exists(out):
            return (m["wem_id"], "cached")
        text = (m.get("text_final") or m.get("transcript") or "").strip()
        if not text:
            return (m["wem_id"], "NO TEXT")
        try:
            ex = dict(extra, speed=m.get("speed", 1.0))
            url = gen_one(a.model, text, ref_url, ref_text, ex)
            tmp = out + ".dl"
            urllib.request.urlretrieve(url, tmp)
            # normalize container to wav (some models return mp3)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, out],
                           check=True)
            os.remove(tmp)
            return (m["wem_id"], "ok")
        except Exception as e:  # noqa: BLE001
            return (m["wem_id"], f"ERR {e}")

    results = {}
    with cf.ThreadPoolExecutor(a.concurrency) as ex:
        for wid, status in ex.map(work, lines):
            results[wid] = status
            if status not in ("ok", "cached"):
                print(f"{wid}: {status}", flush=True)
    ok = sum(1 for s in results.values() if s in ("ok", "cached"))
    print(f"{a.model}: {ok}/{len(lines)} done, "
          f"{len(results) - ok} failed")


if __name__ == "__main__":
    main()

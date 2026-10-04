#!/usr/bin/env python3
"""Build the static bake-off comparison site (opens from file://, no server).

Usage: build_bakeoff.py --ids 542776923,...  --models minimax,chatterboxhd,f5,indextts2

Copies original + generated clips into site-bakeoff/audio/ and writes
site-bakeoff/index.html with inline CSS/JS, dark default + light toggle.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess

MODEL_LABELS = {
    "minimax": "MiniMax speech-2.8-hd",
    "chatterboxhd": "ChatterboxHD",
    "f5": "F5-TTS",
    "indextts2": "IndexTTS-2",
}


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True)
    ap.add_argument("--models", required=True)
    a = ap.parse_args()
    ids = [int(x) for x in a.ids.split(",")]
    models = a.models.split(",")

    manifest = {m["wem_id"]: m for m in json.load(open("work/manifest.json"))}
    os.makedirs("site-bakeoff/audio", exist_ok=True)

    rows = []
    for wid in ids:
        m = manifest[wid]
        orig_dst = f"audio/orig_{wid}.wav"
        shutil.copy(f"work/original_wav/{wid}.wav", f"site-bakeoff/{orig_dst}")
        cells = {"orig": {"src": orig_dst, "dur": m["duration_s"]}}
        for mod in models:
            src = f"work/gen/{mod}/{wid}.wav"
            if os.path.exists(src):
                dst = f"audio/{mod}_{wid}.wav"
                shutil.copy(src, f"site-bakeoff/{dst}")
                cells[mod] = {"src": dst, "dur": round(dur(src), 2)}
            else:
                cells[mod] = None
        rows.append({"wid": wid, "text": m.get("text_final") or m.get("transcript") or "",
                     "banks": ", ".join(b.replace("__core.bnk", "") for b in m["banks"]),
                     "cells": cells})

    def cell_html(c, orig_dur):
        if not c:
            return '<td class="miss">—</td>'
        delta = ""
        if orig_dur:
            pct = (c["dur"] / orig_dur - 1) * 100
            cls = "good" if abs(pct) <= 20 else "warn"
            delta = f'<span class="delta {cls}">{pct:+.0f}%</span>'
        return (f'<td><audio controls preload="none" src="{c["src"]}"></audio>'
                f'<div class="meta">{c["dur"]:.2f}s {delta}</div></td>')

    trs = []
    for r in rows:
        tds = [cell_html(r["cells"]["orig"], None)]
        tds[0] = tds[0].replace('<div class="meta">',
                                '<div class="meta">original · ')
        for mod in models:
            tds.append(cell_html(r["cells"][mod], r["cells"]["orig"]["dur"]))
        trs.append(
            f'<tr><td class="line"><div class="text">{html.escape(r["text"])}</div>'
            f'<div class="src">#{r["wid"]} · {html.escape(r["banks"])}</div></td>'
            + "".join(tds) + "</tr>")

    heads = "".join(f"<th>{html.escape(MODEL_LABELS.get(m, m))}</th>" for m in models)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nagash → Skeletor Voice Bake-off</title>
<style>
:root {{ --bg:#14151a; --panel:#1d1f26; --text:#e8e8ee; --dim:#9a9aa8;
  --line:#2c2e38; --accent:#8be28b; --warn:#f0b35f; }}
html[data-theme=light] {{ --bg:#f5f5f7; --panel:#fff; --text:#1c1c22;
  --dim:#67676f; --line:#dddde4; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font:15px/1.5 -apple-system,'Segoe UI',sans-serif; padding:2rem; }}
h1 {{ font-size:1.4rem; margin:0 0 .3rem; }}
.sub {{ color:var(--dim); margin-bottom:1.5rem; }}
button#theme {{ float:right; background:var(--panel); color:var(--text);
  border:1px solid var(--line); border-radius:8px; padding:.4rem .8rem; cursor:pointer; }}
.wrap {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; background:var(--panel);
  border:1px solid var(--line); border-radius:12px; }}
th,td {{ padding:.7rem .8rem; border-bottom:1px solid var(--line);
  text-align:left; vertical-align:top; }}
th {{ color:var(--dim); font-weight:600; font-size:.85rem;
  text-transform:uppercase; letter-spacing:.04em; }}
td.line {{ max-width:340px; }}
.text {{ margin-bottom:.3rem; }}
.src {{ color:var(--dim); font-size:.78rem; }}
audio {{ width:230px; height:32px; }}
.meta {{ color:var(--dim); font-size:.78rem; margin-top:.25rem; }}
.delta.good {{ color:var(--accent); }} .delta.warn {{ color:var(--warn); }}
.miss {{ color:var(--dim); text-align:center; }}
</style></head><body>
<button id="theme">light / dark</button>
<h1>Nagash → Skeletor voice bake-off</h1>
<div class="sub">Original line vs. each fal.ai cloning model. Duration delta vs. the
original is shown under each take; within ±20% is green.</div>
<div class="wrap"><table>
<tr><th>Line</th><th>Original (Nagash)</th>{heads}</tr>
{"".join(trs)}
</table></div>
<script>
const b=document.getElementById('theme'),r=document.documentElement;
b.onclick=()=>{{r.dataset.theme=r.dataset.theme==='light'?'':'light';}};
document.addEventListener('play',e=>{{document.querySelectorAll('audio').forEach(
a=>{{if(a!==e.target)a.pause();}});}},true);
</script></body></html>"""
    with open("site-bakeoff/index.html", "w") as f:
        f.write(page)
    print(f"site-bakeoff/index.html written: {len(rows)} lines x {len(models)} models")


if __name__ == "__main__":
    main()

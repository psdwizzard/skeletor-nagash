#!/usr/bin/env python3
"""Build the static Skeletor-reference pick site (file://, self-contained).

Rows = candidate clips (+ assembled reference_main), columns = raw vs
vocals-only (demucs). Playback copies are loudness-normalized to -18 LUFS so
Kenneth compares voice quality, not volume.
"""
from __future__ import annotations

import html
import json
import os
import subprocess

OUTDIR = "site-refpick"


def norm_copy(src, dst):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src,
                    "-af", "loudnorm=I=-18:TP=-1.5:LRA=11",
                    "-ar", "44100", "-ac", "1", dst], check=True)


def dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return float(out) if out else 0.0


def main():
    os.makedirs(f"{OUTDIR}/audio", exist_ok=True)
    cands = json.load(open("work/ref/candidates.json"))
    cands.append({
        "file": "reference_main.wav",
        "source_video": "",
        "transcript": open("work/ref/reference_main.txt").read().strip(),
        "music_level": "low",
        "notes": "Assembled 3-segment primary reference (current default).",
    })

    rows = []
    for c in cands:
        name = c["file"]
        raw_src = (f"work/ref/candidates/{name}"
                   if name != "reference_main.wav" else "work/ref/reference_main.wav")
        clean_src = f"work/ref/clean/{name}"
        raw_dst, clean_dst = f"audio/raw_{name}", f"audio/clean_{name}"
        norm_copy(raw_src, f"{OUTDIR}/{raw_dst}")
        has_clean = os.path.exists(clean_src)
        if has_clean:
            norm_copy(clean_src, f"{OUTDIR}/{clean_dst}")
        rows.append((c, raw_dst, clean_dst if has_clean else None,
                     dur(raw_src)))

    trs = []
    for c, raw, clean, d in rows:
        src_link = (f'<a href="{html.escape(c["source_video"])}">source</a> · '
                    if c.get("source_video") else "")
        clean_cell = (f'<td><audio controls preload="none" src="{clean}"></audio></td>'
                      if clean else '<td class="miss">—</td>')
        trs.append(
            f'<tr><td class="line"><div class="name">{html.escape(c["file"])}'
            f' <span class="dur">{d:.1f}s</span></div>'
            f'<div class="text">{html.escape(c.get("transcript", ""))}</div>'
            f'<div class="src">{src_link}music: {html.escape(c.get("music_level", "?"))}'
            f' · {html.escape(c.get("notes", ""))}</div></td>'
            f'<td><audio controls preload="none" src="{raw}"></audio></td>'
            f'{clean_cell}</tr>')

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skeletor Reference Pick</title>
<style>
:root {{ --bg:#14151a; --panel:#1d1f26; --text:#e8e8ee; --dim:#9a9aa8;
  --line:#2c2e38; }}
html[data-theme=light] {{ --bg:#f5f5f7; --panel:#fff; --text:#1c1c22;
  --dim:#67676f; --line:#dddde4; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font:15px/1.5 -apple-system,'Segoe UI',sans-serif; padding:2rem; }}
h1 {{ font-size:1.4rem; margin:0 0 .3rem; }}
.sub {{ color:var(--dim); margin-bottom:1.5rem; max-width:70ch; }}
button#theme {{ float:right; background:var(--panel); color:var(--text);
  border:1px solid var(--line); border-radius:8px; padding:.4rem .8rem; cursor:pointer; }}
.wrap {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; background:var(--panel);
  border:1px solid var(--line); border-radius:12px; }}
th,td {{ padding:.7rem .8rem; border-bottom:1px solid var(--line);
  text-align:left; vertical-align:top; }}
th {{ color:var(--dim); font-weight:600; font-size:.85rem;
  text-transform:uppercase; letter-spacing:.04em; }}
td.line {{ max-width:420px; }}
.name {{ font-weight:600; }} .dur {{ color:var(--dim); font-weight:400; }}
.text {{ margin:.25rem 0; font-size:.9rem; }}
.src {{ color:var(--dim); font-size:.78rem; }}
.src a {{ color:inherit; }}
audio {{ width:250px; height:32px; }}
.miss {{ color:var(--dim); text-align:center; }}
</style></head><body>
<button id="theme">light / dark</button>
<h1>Skeletor reference pick</h1>
<div class="sub">Candidate reference clips for the voice clone. "Vocals only" is the
demucs-isolated voice with music/SFX removed. All playback copies level-matched to
-18 LUFS. Pick the clip (and raw-vs-clean) that sounds most like the Skeletor you want.</div>
<div class="wrap"><table>
<tr><th>Clip</th><th>Raw</th><th>Vocals only (demucs)</th></tr>
{"".join(trs)}
</table></div>
<script>
const b=document.getElementById('theme'),r=document.documentElement;
b.onclick=()=>{{r.dataset.theme=r.dataset.theme==='light'?'':'light';}};
document.addEventListener('play',e=>{{document.querySelectorAll('audio').forEach(
a=>{{if(a!==e.target)a.pause();}});}},true);
</script></body></html>"""
    with open(f"{OUTDIR}/index.html", "w") as f:
        f.write(page)
    print(f"{OUTDIR}/index.html written: {len(rows)} clips")


if __name__ == "__main__":
    main()

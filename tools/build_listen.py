#!/usr/bin/env python3
"""Build the full listening site: all 330 lines, original vs Skeletor take.

Static, self-contained, opens from file://. Audio copied as mp3 (V2) to keep
the folder small. Flag takes in the UI; flags persist in localStorage and can
be exported as a wem-id list for regeneration.
"""
from __future__ import annotations

import html
import json
import os
import subprocess

OUT = "site-listen"

CAT = [
    ("frontend", "Frontend / select"),
    ("campaign_vo_conversational", "Campaign conversational"),
    ("campaign_vo", "Campaign"),
    ("battle_vo_orders", "Battle orders"),
    ("battle_vo_conversational", "Battle conversational"),
]


def category(banks):
    joined = " ".join(banks)
    for key, label in CAT:
        if key in joined:
            return label
    return "Other"


def to_mp3(src, dst):
    if not os.path.exists(dst):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src,
                        "-codec:a", "libmp3lame", "-q:a", "2", dst], check=True)


def main():
    os.makedirs(f"{OUT}/audio", exist_ok=True)
    manifest = json.load(open("work/manifest.json"))
    lines = [m for m in manifest if not m["status"].startswith("excluded")]
    lines.sort(key=lambda m: (category(m["banks"]), -(m["duration_s"] or 0)))

    has_echo = os.path.isdir("work/gen/minimax_echo")
    rows = []
    for m in lines:
        wid = m["wem_id"]
        o_dst, g_dst = f"audio/o_{wid}.mp3", f"audio/g_{wid}.mp3"
        to_mp3(f"work/original_wav/{wid}.wav", f"{OUT}/{o_dst}")
        to_mp3(f"work/gen/minimax_fit/{wid}.wav", f"{OUT}/{g_dst}")
        if has_echo and os.path.exists(f"work/gen/minimax_echo/{wid}.wav"):
            to_mp3(f"work/gen/minimax_echo/{wid}.wav", f"{OUT}/audio/e_{wid}.mp3")
        rows.append({
            "wid": wid,
            "cat": category(m["banks"]),
            "text": m.get("text_final") or m.get("transcript") or "",
            "od": m["duration_s"], "gd": m.get("gen_duration_s"),
            "slow": m.get("speed", 1.0) != 1.0,
        })

    cats = sorted({r["cat"] for r in rows})
    opts = "".join(f'<option>{html.escape(c)}</option>' for c in cats)
    trs = []
    for r in rows:
        slow = ' <span class="tag">slow 0.7</span>' if r["slow"] else ""
        trs.append(
            f'<tr data-cat="{html.escape(r["cat"])}" data-wid="{r["wid"]}">'
            f'<td class="line"><div class="text">{html.escape(r["text"])}</div>'
            f'<div class="src">#{r["wid"]} · {html.escape(r["cat"])}{slow}</div></td>'
            f'<td><audio controls preload="none" src="audio/o_{r["wid"]}.mp3"></audio>'
            f'<div class="meta">{r["od"]:.1f}s</div></td>'
            f'<td><audio controls preload="none" src="audio/g_{r["wid"]}.mp3"></audio>'
            f'<div class="meta">{(r["gd"] or 0):.1f}s</div></td>'
            + (f'<td><audio controls preload="none" src="audio/e_{r["wid"]}.mp3">'
               f'</audio></td>' if has_echo else "")
            + f'<td><button class="flag">flag</button></td></tr>')

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skeletor Nagash Listening Room</title>
<style>
:root {{ --bg:#14151a; --panel:#1d1f26; --text:#e8e8ee; --dim:#9a9aa8;
  --line:#2c2e38; --accent:#8be28b; --warn:#f0b35f; }}
html[data-theme=light] {{ --bg:#f5f5f7; --panel:#fff; --text:#1c1c22;
  --dim:#67676f; --line:#dddde4; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text);
  font:15px/1.5 -apple-system,'Segoe UI',sans-serif; padding:2rem; }}
h1 {{ font-size:1.4rem; margin:0 0 .3rem; }}
.sub {{ color:var(--dim); margin-bottom:1rem; max-width:75ch; }}
.bar {{ display:flex; gap:.6rem; margin-bottom:1rem; flex-wrap:wrap; align-items:center; }}
input,select,button {{ background:var(--panel); color:var(--text);
  border:1px solid var(--line); border-radius:8px; padding:.45rem .7rem; font:inherit; }}
input {{ width:min(380px,90vw); }}
button {{ cursor:pointer; }}
.wrap {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; background:var(--panel);
  border:1px solid var(--line); border-radius:12px; }}
th,td {{ padding:.6rem .7rem; border-bottom:1px solid var(--line);
  text-align:left; vertical-align:top; }}
th {{ color:var(--dim); font-weight:600; font-size:.85rem;
  text-transform:uppercase; letter-spacing:.04em; position:sticky; top:0;
  background:var(--panel); }}
td.line {{ max-width:380px; }}
.text {{ font-size:.92rem; }}
.src {{ color:var(--dim); font-size:.76rem; margin-top:.15rem; }}
.tag {{ color:var(--warn); }}
audio {{ width:220px; height:30px; }}
.meta {{ color:var(--dim); font-size:.76rem; margin-top:.2rem; }}
tr.flagged {{ outline:2px solid var(--warn); outline-offset:-2px; }}
tr.flagged .flag {{ background:var(--warn); color:#1c1c22; }}
#count {{ color:var(--dim); }}
</style></head><body>
<h1>Skeletor Nagash — listening room</h1>
<div class="sub">All 330 lines: original on the left, Skeletor take on the right.
Flag anything you want regenerated, then hit "copy flagged ids" and paste them to
Claude. Flags survive page reloads.</div>
<div class="bar">
  <input id="q" placeholder="search text…">
  <select id="cat"><option value="">all categories</option>{opts}</select>
  <label><input type="checkbox" id="onlyflag" style="width:auto"> flagged only</label>
  <button id="copy">copy flagged ids</button>
  <button id="theme">light / dark</button>
  <span id="count"></span>
</div>
<div class="wrap"><table>
<tr><th>Line</th><th>Original (Nagash)</th><th>Skeletor (dry)</th>{"<th>Skeletor (echo)</th>" if has_echo else ""}<th></th></tr>
{"".join(trs)}
</table></div>
<script>
const rows=[...document.querySelectorAll('tr[data-wid]')];
const KEY='skeletor_flags';
let flags=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'));
rows.forEach(tr=>{{
  if(flags.has(tr.dataset.wid))tr.classList.add('flagged');
  tr.querySelector('.flag').onclick=()=>{{
    const w=tr.dataset.wid;
    flags.has(w)?flags.delete(w):flags.add(w);
    tr.classList.toggle('flagged');
    localStorage.setItem(KEY,JSON.stringify([...flags]));
    update();
  }};
}});
const q=document.getElementById('q'),cat=document.getElementById('cat'),
  onlyflag=document.getElementById('onlyflag'),count=document.getElementById('count');
function update(){{
  const term=q.value.toLowerCase(),c=cat.value;
  let shown=0;
  rows.forEach(tr=>{{
    const ok=(!term||tr.textContent.toLowerCase().includes(term))
      &&(!c||tr.dataset.cat===c)
      &&(!onlyflag.checked||flags.has(tr.dataset.wid));
    tr.style.display=ok?'':'none'; if(ok)shown++;
  }});
  count.textContent=shown+' shown · '+flags.size+' flagged';
}}
q.oninput=cat.onchange=onlyflag.onchange=update; update();
document.getElementById('copy').onclick=async()=>{{
  await navigator.clipboard.writeText([...flags].join(','));
  document.getElementById('copy').textContent='copied '+flags.size+' ids';
}};
const b=document.getElementById('theme'),r=document.documentElement;
b.onclick=()=>{{r.dataset.theme=r.dataset.theme==='light'?'':'light';}};
document.addEventListener('play',e=>{{document.querySelectorAll('audio').forEach(
a=>{{if(a!==e.target)a.pause();}});}},true);
</script></body></html>"""
    with open(f"{OUT}/index.html", "w") as f:
        f.write(page)
    print(f"{OUT}/index.html: {len(rows)} lines")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the final mod pack from work/wem_new/*.wem.

Usage: build_pack.py [--out dist/skeletor_nagash.pack] [--type movie|mod]

Every wem id must exist in the vanilla audio_en.pack (we only override known
Nagash lines; refuses to pack unknown ids as a contamination guard).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from packfile import PackFile, write_pack, TYPE_MOD, TYPE_MOVIE  # noqa: E402

GAME_DATA = ("/Users/kenneth/Library/Application Support/Steam/steamapps/common/"
             "Total War WARHAMMER III/TotalWarhammer3Data/data")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/skeletor_nagash.pack")
    ap.add_argument("--type", default="movie", choices=["movie", "mod"])
    ap.add_argument("--indir", default="work/wem_new")
    a = ap.parse_args()

    manifest = {m["wem_id"] for m in json.load(open("work/manifest.json"))}
    vanilla = PackFile(f"{GAME_DATA}/audio_en.pack")

    files = {}
    skipped = []
    for path in sorted(glob.glob(os.path.join(a.indir, "*.wem"))):
        wid = int(os.path.basename(path).split(".")[0])
        internal = f"audio\\wwise\\english(uk)\\{wid}.wem"
        if wid not in manifest or internal not in vanilla.entries:
            skipped.append(wid)
            continue
        files[internal] = open(path, "rb").read()

    if skipped:
        print(f"REFUSED {len(skipped)} unknown ids: {skipped[:10]}")
    if not files:
        sys.exit("no files to pack")
    ptype = TYPE_MOVIE if a.type == "movie" else TYPE_MOD
    write_pack(a.out, files, ptype)
    chk = PackFile(a.out)
    chk.sanity_check()
    print(f"{a.out}: {len(chk.entries)} entries, "
          f"{os.path.getsize(a.out) / 1e6:.1f} MB, type={a.type}")


if __name__ == "__main__":
    main()

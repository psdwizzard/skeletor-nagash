#!/usr/bin/env python3
"""Batch-encode fitted WAVs to Wwise Vorbis .wem via WwiseConsole.

Usage: encode_wem.py --indir work/gen/<model>_fit [--outdir work/wem_new]

One-time setup (done automatically): creates a throwaway Wwise project under
work/wwise_proj and injects a Vorbis conversion shareset, then uses
"convert-external-source" with a generated .wsources list.

Requires Audiokinetic Wwise 2019.2.15.7667 (bank version 136). We auto-locate
WwiseConsole under /Applications/Audiokinetic/.
"""
from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import uuid

CONV_NAME = "VorbisHigh"
# Minimal Conversion modeled on the project's own Default Work Unit.wwu
# (SchemaVersion 97): just bind the Vorbis conversion plugin, defaults for the
# rest ("as input" channels/rate — our wavs are already 48 kHz mono).
CONV_XML = """\t\t\t\t<Conversion Name="{name}" ID="{{{conv_id}}}">
\t\t\t\t\t<ConversionPluginInfoList>
\t\t\t\t\t\t<ConversionPluginInfo Platform="Windows">
\t\t\t\t\t\t\t<ConversionPlugin Name="" ID="{{{plug_id}}}" PluginName="Vorbis" CompanyID="0" PluginID="4"/>
\t\t\t\t\t\t</ConversionPluginInfo>
\t\t\t\t\t</ConversionPluginInfoList>
\t\t\t\t</Conversion>
"""


def winpath(path):
    """Wwise authoring on macOS runs under CrossOver: Y:\\ maps to $HOME."""
    ap = os.path.abspath(path)
    home = os.path.expanduser("~")
    if not ap.startswith(home):
        raise ValueError(f"{ap} not under home; can't map to Y:")
    return "Y:" + ap[len(home):].replace("/", "\\")


def find_wwise_console():
    pats = [
        "/Applications/Audiokinetic/Wwise*/Wwise.app/Contents/Tools/WwiseConsole.sh",
        "/Applications/Audiokinetic/Wwise*/Tools/WwiseConsole.sh",
    ]
    hits = sorted(h for p in pats for h in glob.glob(p))
    if not hits:
        sys.exit("WwiseConsole not found under /Applications/Audiokinetic — "
                 "install Wwise 2019.2.15.7667 first.")
    pick = [h for h in hits if "2019.2" in h] or hits
    return pick[0]


def ensure_project(console):
    # NOTE: WwiseConsole (mac .sh wrapper) joins even absolute paths onto its
    # CWD, so every console call uses RELATIVE paths with cwd=repo root.
    proj = "work/wwise_proj/vo_encode/vo_encode.wproj"
    if not os.path.exists(proj):
        subprocess.run([console, "create-new-project", proj,
                        "--platform", "Windows"], check=True)
    wwu = os.path.join(os.path.dirname(proj), "Conversion Settings",
                       "Default Work Unit.wwu")
    content = open(wwu).read()
    if CONV_NAME not in content:
        block = CONV_XML.format(
            name=CONV_NAME,
            conv_id=str(uuid.uuid4()).upper(),
            plug_id=str(uuid.uuid4()).upper(),
        )
        content = content.replace("\t\t\t</ChildrenList>",
                                  block + "\t\t\t</ChildrenList>")
        with open(wwu, "w") as f:
            f.write(content)
    return proj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--outdir", default="work/wem_new")
    a = ap.parse_args()

    console = find_wwise_console()
    proj = ensure_project(console)
    os.makedirs(a.outdir, exist_ok=True)

    wavs = sorted(glob.glob(os.path.join(a.indir, "*.wav")))
    todo = [w for w in wavs
            if not os.path.exists(os.path.join(
                a.outdir, os.path.basename(w).replace(".wav", ".wem")))]
    if not todo:
        print("nothing to encode")
        return
    lines = [f'<Source Path="{os.path.basename(w)}" Conversion="{CONV_NAME}" '
             f'Destination="{os.path.basename(w).replace(".wav", ".wem")}"/>'
             for w in todo]
    wsources = "work/wwise_proj/batch.wsources"
    with open(wsources, "w") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<ExternalSourcesList SchemaVersion="1" Root="{winpath(a.indir)}">\n'
                + "\n".join(lines) + "\n</ExternalSourcesList>\n")

    outtmp = "work/wwise_proj/out"
    os.makedirs(outtmp, exist_ok=True)
    subprocess.run([console, "convert-external-source", proj,
                    "--platform", "Windows",
                    "--source-file", winpath(wsources),
                    "--output", winpath(outtmp)], check=True)
    moved = 0
    for wem in glob.glob(os.path.join(outtmp, "**", "*.wem"), recursive=True):
        shutil.move(wem, os.path.join(a.outdir, os.path.basename(wem)))
        moved += 1
    print(f"encoded {moved} wems -> {a.outdir}")
    # verify every wem decodes
    bad = []
    for w in glob.glob(os.path.join(a.outdir, "*.wem")):
        r = subprocess.run(["vgmstream-cli", "-m", w], capture_output=True)
        if r.returncode != 0:
            bad.append(os.path.basename(w))
    print(f"decode check: {len(bad)} failures {bad[:10]}")


if __name__ == "__main__":
    main()

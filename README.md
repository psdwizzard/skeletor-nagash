# Skeletor Nagash 💀

A fan mod for **Total War: WARHAMMER III** that replaces all 330 of Nagash's English
voice lines with an AI-generated impression of the classic 1980s cartoon Skeletor.
The Supreme Lord of Undeath now sounds like the Overlord of Evil. Myah.

## Install (Windows)

1. Download **[`dist/skeletor_nagash_mod.zip`](dist/skeletor_nagash_mod.zip)** and
   extract it.
2. Copy `skeletor_nagash.pack` into your game's `data` folder. Default Steam path:
   `C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data\`
   (Can't find it? Steam → right-click *Total War: WARHAMMER III* → Manage →
   Browse local files → open `data`.)
3. Launch the game. That's it — no mod manager needed; the pack loads automatically.

**Uninstall:** delete `skeletor_nagash.pack` from that folder. The original voice
comes back instantly — the mod never touches any game file.

**Requirements:** game updated to patch 9.0+ ("Lords of the End Times"), voice
language English. You'll hear Skeletor-Nagash whenever he speaks; playing *as* him
needs the Lords of the End Times DLC.

Mac (Steam/Feral): same file, drop it into
`~/Library/Application Support/Steam/steamapps/common/Total War WARHAMMER III/TotalWarhammer3Data/data/`.

Full install/rollback notes: [`dist/README.md`](dist/README.md).

## How it was made

The `tools/` pipeline (Python, macOS): parse the game's PFH5 packs and Wwise v136
soundbanks to find every wem belonging to Nagash's VO actor, verify speaker identity
with voice embeddings, transcribe with Whisper, clone a voice from a demucs-isolated
reference on [fal.ai](https://fal.ai) (MiniMax speech-2.8-hd), condition each take to
the original line's loudness, add a sepulchral echo, encode back to Wwise Vorbis with
WwiseConsole, and repack. Details in [`docs/devblog.md`](docs/devblog.md).

This repo contains **no game assets**: the shipped pack holds only AI-generated
audio, and the extraction working directory is deliberately not committed.

## Disclaimer

Unofficial, non-commercial fan project. Not affiliated with or endorsed by Creative
Assembly, SEGA, Games Workshop, or Mattel. The voice is an AI-generated impression of
a cartoon character. If a rights holder objects, it comes down.

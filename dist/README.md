# Skeletor Nagash — voice replacement mod (TWW3)

Replaces Nagash's English voice lines (330 clips) in Total War: WARHAMMER III with a
voice-cloned classic-80s Skeletor. Built against game Update 9.0 ("Lords of the End
Times"). Personal-use mod.

## What's in here
- `skeletor_nagash.pack` — the mod. Contains only replacement `.wem` audio files at
  vanilla paths (`audio/wwise/english(uk)/<id>.wem`). No game file is modified.

## Install — macOS (Steam / Feral port)
1. Copy `skeletor_nagash.pack` into:
   `~/Library/Application Support/Steam/steamapps/common/Total War WARHAMMER III/TotalWarhammer3Data/data/`
2. Launch the game. The pack is Movie-type, so it loads automatically — no mod
   manager step needed.

## Install — Windows
1. Download `skeletor_nagash_mod.zip` and extract it.
2. Copy `skeletor_nagash.pack` into your game's data folder — for a default Steam
   install that's:
   `C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data\`
   (If Steam is somewhere else: Steam → right-click the game → Manage → Browse local
   files → open the `data` folder.)
3. Launch the game normally. Movie-type packs load automatically — no mod manager or
   enabling step needed.

## Requirements
- Total War: WARHAMMER III updated to patch 9.0 or later (the "Lords of the End Times"
  era — that's when Nagash's voice files exist).
- Game voice language set to English (the mod replaces the English VO).
- To actually *play* Nagash you need the Lords of the End Times DLC; without it you'll
  still hear him when you meet him in campaign or play against him.

## Uninstall / rollback
Delete `skeletor_nagash.pack` from the data folder. That's it — the vanilla voice
returns. Originals are never touched by this mod. (Belt-and-braces: the project repo
keeps the extracted vanilla wems in `work/original_wem/`.)

## After game updates
Patches may ship new packs but won't remove this file. If a patch adds NEW Nagash
lines, those will play with his vanilla voice until the mod is regenerated. If audio
stops working after a major update, re-check that the file is still in `data/`.

## Known quirks
- Subtitles show the original line text; the spoken wording matches it, but pacing is
  snappier than the subtitle timing assumes.
- English VO only (other language audio untouched).

## Disclaimer
Unofficial, non-commercial fan mod. Not affiliated with or endorsed by Creative
Assembly, SEGA, Games Workshop, Mattel, or anyone who ever feared Skeletor. Contains
no game assets — only replacement audio generated with an AI voice model as an
impression of a cartoon villain. If a rights holder objects, it comes down.

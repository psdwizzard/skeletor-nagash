# Progress — Nagash → Skeletor voice mod

Plan: docs/plan.md. Status as of 2026-09-30 (evening).

## Done
- [x] Research (game layout, Wwise pipeline, fal models) — see plan context.
- [x] Phase 0 setup: brew vgmstream/yt-dlp/python@3.12; `.venv` with mlx-whisper +
      fal-client; `tools/falenv.sh` exports FAL_KEY from `~/.fal/.env.rtf` (verified
      against fal storage upload).
- [x] Phase 1 extract: `tools/packfile.py` (PFH5 read/write, round-trip verified),
      `tools/bnk_walk.py` (global object map across all 648 banks; dialogue-event
      decision-tree walk for actor hash 588314267). **358 unique wems**, 34.4 min audio,
      zero unresolved leaves, zero overlap with Neferata (contamination check).
      Originals archived in `work/original_wem/` + decoded `work/original_wav/`.
- [x] Phase 2 transcribe: mlx-whisper large-v3-turbo over all 358 lines → manifest.
- [x] Smoke-test pack built WITHOUT Wwise (stand-in: existing Neferata wem at Nagash's
      3 frontend wem IDs), Movie-type, installed at game `data/zz_smoketest_vo.pack`.
      **Awaiting manual in-game check.**
- [x] Pipeline scripts ready: `generate.py` (4 fal models, resume-safe, queue+threads),
      `postprocess.py` (duration fit/atempo/loudnorm/48k mono), `encode_wem.py`
      (WwiseConsole batch, auto project setup), `build_pack.py` (final pack with
      unknown-id guard), `build_bakeoff.py` (static file:// comparison site).

## Done (2026-10-01)
- [x] Skeletor reference: 4 YT videos, 8 candidates + assembled 19s `reference_main`.
      Agent's cuts were silent (ffmpeg bug) — re-cut from raw + silence gates added.
- [x] Demucs vocal isolation on fal (`fal-ai/demucs`, htdemucs_ft) → `work/ref/clean/`.
      Kenneth picked **reference_main — vocals only**, delivery: full cartoon Skeletor.
- [x] Lore-spelling pass (34 fixes). Speaker-embedding verification: **28 of 358 wems
      are unit barks, not Nagash** → status=excluded_other_voice; **330 lines ship**.
- [x] Bake-off (6 lines × minimax/chatterboxhd/f5/indextts2) → `site-bakeoff/`.
      Kenneth picked **MiniMax speech-2.8-hd**.
- [x] Full generation: 330/330 ok. Duration policy relaxed to 0.30–1.15× (clone reads
      faster than Nagash's glacial delivery; short clips are harmless — streamed wems).
      12 ultra-short lines regenerated at speed 0.7. All 330 pass.
- [x] Postprocess: per-line loudnorm to original LUFS, 48 kHz mono 16-bit →
      `work/gen/minimax_fit/` (330 files). dist/README.md written.

## Decisions (2026-10-03)
- Kenneth approved all 330 takes and chose the **echo** versions
  (`work/gen/minimax_echo/`, light preset) as the ship set. Dry set kept at
  `work/gen/minimax_fit/` for rollback.
- One text edit: wem 1003945860 → "I am limitless, and my minions are not." + laugh
  (original wording kept in manifest `text_orig`).
- **Smoke test waived by Kenneth** — final verification happens on the real pack.

## Done (2026-10-03, afternoon) — MOD BUILT AND INSTALLED
- [x] Wwise 2019.2.15.7667 installed by Kenneth. Gotchas found: the mac WwiseConsole
      runs under CrossOver — paths passed to it (and the wsources Root) must be
      Windows-style `Y:\…` (Y: = $HOME); `tools/encode_wem.py` handles this via
      `winpath()`. Vorbis conversion = minimal `<Conversion>` injected into the
      project's Conversion Settings wwu (name `VorbisHigh`).
- [x] All 330 echo takes encoded to Wwise Vorbis 48 kHz (vgmstream decode check: 0
      failures). `dist/skeletor_nagash.pack` built (Movie type, 330 entries, 7.9 MB)
      and installed into the game data dir. Smoke-test pack removed.
- [x] `dist/skeletor_nagash_mod.zip` (pack + README) ready for MOJOJO. sdGlobalSave
      was not mounted at build time — zip is local; copy when the share is up.

## Remaining
- [ ] Kenneth: launch the game and verify (lord select → campaign → battle).
- [ ] Any flagged lines → regenerate → re-encode just those → rebuild pack.
- [ ] Copy zip to MOJOJO when sdGlobalSave mounts; install per dist/README.md.

## Next
- [ ] Bake-off: 6 sample ids 542776923,119629737,494897770,48626123,206659570,998374533
      × 4 models → `site-bakeoff/` → Kenneth picks winner.
- [ ] Full generation (chosen model) → postprocess → encode → pack → install → verify.
- [ ] dist/ packaging + Windows (MOJOJO) install README.

## Key facts for a fresh session
- Game data: `~/Library/Application Support/Steam/steamapps/common/Total War WARHAMMER III/TotalWarhammer3Data/data`
- Replacement = same-ID wem override in own pack at `audio\wwise\english(uk)\<id>.wem`;
  originals never touched. Rollback = delete our pack.
- MiniMax cloned voice id lives in `work/gen/state.json`; expires after 7 idle days.

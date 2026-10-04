# Skeletor Nagash — TWW3 voice replacement mod

Replaces all 330 of Nagash's English voice lines in Total War: WARHAMMER III with an
AI-cloned classic-80s Skeletor (MiniMax speech-2.8-hd on fal.ai, cloned from a
demucs-isolated Filmation-era reference). Personal project; repo is public.

## State (2026-10-03)
- **Shipped.** `dist/skeletor_nagash.pack` (Movie type, 330 wems, 7.9 MB) is built and
  installed in the Mac game data dir. `dist/skeletor_nagash_mod.zip` is the Windows
  hand-off. Kenneth approved the **echo** takes; dry takes kept for rollback.
- `work/` and `site-*/` exist locally but are gitignored on purpose (extracted game
  audio, YouTube reference audio, transcripts, generated takes, review sites). A fresh
  clone has the tools but must re-extract to regenerate anything.

## The pipeline (tools/, run in order; .venv has fal-client + mlx-whisper)
1. `bnk_walk.py <audio_en_bnk.pack> <actor_key>` — finds a VO actor's wem ids
   (FNV-1-lowercase hash over dialogue-event decision trees; global cross-bank map).
2. `extract_wems.py work/nagash_wems.json` — pulls wems, decodes (vgmstream), manifest.
3. `transcribe.py` — mlx-whisper → manifest transcripts.
4. `destem.py` / `generate.py` — fal.ai: demucs vocal isolation; TTS generation
   (`source tools/falenv.sh` first — reads the key from `~/.fal/.env.rtf`).
5. `fit_loop.py`, `postprocess.py`, `add_echo.py` — duration policy, loudnorm to the
   original line's LUFS, 48 kHz mono, echo preset.
6. `encode_wem.py --indir work/gen/minimax_echo` — WwiseConsole batch → Vorbis wems.
7. `build_pack.py` — final pack (refuses wem ids not in the manifest).
8. Review sites: `build_listen.py` / `build_bakeoff.py` / `build_refpick.py` (static,
   file://, dark mode).

## Gotchas (hard-won — read before touching)
- **WwiseConsole on macOS runs under CrossOver**: all paths you pass it (and the
  `.wsources` Root) must be `Y:\…` form (`Y:` = `$HOME`). See `winpath()` in
  `encode_wem.py`. Wwise version must be **2019.2.15.7667** (bank v136).
- PFH5 index entry = `u32 size, u8 compressed, path\0`; audio entries uncompressed.
- CAkSound sourceID sits at payload offset **5** (after u32 pluginID + u8 streamType).
- 28 of the 358 hash-matched wems are unit barks by a different actor (speaker
  embeddings proved it) — `status: excluded_other_voice` in the manifest. Never ship
  them; `build_pack.py`'s guard only checks manifest membership, the exclusion happens
  because excluded lines were never generated.
- MiniMax on fal: `output_format:"url"`, `audio_setting` wants int sample rate and
  mp3/pcm/flac; cloned voice id (`work/gen/state.json`) expires after 7 idle days.
- Game data dir (Mac): `~/Library/Application Support/Steam/steamapps/common/Total War
  WARHAMMER III/TotalWarhammer3Data/data/`. Movie packs auto-load; uninstall = delete.
- Every review-site build runs a volumedetect silence gate — keep it (a subagent once
  shipped 8 perfectly silent clips).

## Docs
`docs/devblog.md` (history), `docs/plan.md` (original plan), `docs/progress.md`
(phase ledger). Update devblog + this file on every close-out.

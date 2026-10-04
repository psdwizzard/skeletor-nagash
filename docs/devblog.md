# Dev blog — Skeletor Nagash voice mod

## 2026-10-03 — Mod built, installed, published
- Kenneth approved all 330 takes, chose the **echo** set, waived the smoke test.
- One line punched up by request: "I am limitless, **and** my minions are not" + cackle
  (wem 1003945860; old wording kept in manifest `text_orig`).
- Wwise 2019.2.15.7667 installed → encoded all 330 echo takes to Wwise Vorbis 48 kHz
  (0 decode failures). **Gotcha for posterity:** the macOS WwiseConsole runs under
  CrossOver — every path you hand it (args AND the `.wsources` `Root`) must be
  Windows-style `Y:\…` where `Y:` = `$HOME`. `tools/encode_wem.py` → `winpath()`.
- `dist/skeletor_nagash.pack` (Movie type, 330 entries, 7.9 MB) built with the
  unknown-id guard, installed into the Mac game data dir; zip for Windows in `dist/`.
- Repo made public. `work/` and `site-*/` are deliberately NOT in the repo (extracted
  game audio, YouTube reference audio, transcripts) — the pack itself contains only
  AI-generated audio.

## 2026-10-01→03 — Generation pipeline
- Skeletor reference: yt-dlp from classic Filmation compilations; the subagent's cut
  step produced silent files (ffmpeg stream mapping) — re-cut from raw + added
  volumedetect gates to every site build. Demucs (`fal-ai/demucs`, htdemucs_ft) vocal
  isolation; Kenneth picked the assembled 19s `reference_main`, vocals-only.
- Bake-off: 6 lines × MiniMax / ChatterboxHD / F5-TTS / IndexTTS-2 → Kenneth picked
  **MiniMax speech-2.8-hd** (fal schema gotchas: `prompt` not `text` for IndexTTS-2,
  int sample_rate + mp3/pcm/flac only for MiniMax, output_format "url").
- Full run: 330/330. Key insight: the clone reads ~2.4× faster than Nagash's glacial
  delivery — that's fine (streamed wems carry their own length; game doesn't pad or
  truncate). Accept band 0.30–1.15×; 12 ultra-short lines regenerated at speed 0.7.
- Post: per-line loudnorm to the original's LUFS, 48 kHz mono. Echo pass: `aecho`
  66|132ms 0.32|0.16 + 0.45s tail pad, re-loudnormed (`tools/add_echo.py`).

## 2026-09-30 — Research & extraction
- Nagash is official (Lords of the End Times DLC, Update 9.0, 2026-09-24); Mac Feral
  port at full parity. VO = Wwise Vorbis wems in `audio_en.pack` at
  `audio\wwise\english(uk)\<id>.wem`; banks v136 in `audio_en_bnk.pack`.
- Wrote PFH5 reader/writer (`tools/packfile.py`) and bank walker
  (`tools/bnk_walk.py`): FNV-1-lowercase actor hash (Nagash = 588314267), dialogue
  events (HIRC 15) decision trees, global cross-bank object map, children-list
  heuristic. CAkSound sourceID at payload offset 5.
- 358 wems found; speaker-embedding verification (resemblyzer) proved 28 are unit
  barks by another actor → excluded; **330 confirmed Nagash lines**.
- Transcribed locally (mlx-whisper large-v3-turbo) + lore-spelling review pass.
- Replacement method: ship same-ID wems in own pack, no .bnk. Originals never touched.

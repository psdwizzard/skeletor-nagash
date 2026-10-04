# Nagash → Skeletor Voice Replacement Mod (TWW3)

## Context

Kenneth wants a Total War: WARHAMMER III mod that replaces Nagash's English voice lines with
a voice-cloned classic-80s Skeletor (Alan Oppenheimer era), generated via fal.ai. Scope: **all**
Nagash lines. Personal use on his Mac + Windows PC now, possibly published later. Originals must
be preserved for rollback, and clip-duration mismatches must be handled (edit text / time-stretch
if needed).

Research is done (3 agents, findings verified against the actual install):

- Nagash is official: "Lords of the End Times" DLC + Update 9.0 (Sept 24 2026). The Mac Feral
  port is at full 9.0 parity. Game data: `~/Library/Application Support/Steam/steamapps/common/
  Total War WARHAMMER III/TotalWarhammer3Data/data/` (268 PFH5 packs).
- English VO = Wwise Vorbis `.wem` (48 kHz, mono, streamed) inside `audio_en.pack` at internal
  path `audio/wwise/english(uk)/<id>.wem`. Soundbanks (Wwise v136 = Wwise 2019.2.x) in
  `audio_en_bnk.pack`. **Uncompressed entries** — raw bytes in the pack.
- Nagash's VO actor key `wh3_dlc29_vo_actor_Host_of_Nagash_Nagash` → FNV-1 32 lowercase hash
  **588314267**, found in 5 banks: `campaign_vo__core.bnk` (37), `campaign_vo_conversational__core.bnk`
  (34), `battle_vo_orders__core.bnk` (20), `battle_vo_conversational__core.bnk` (2),
  `frontend_vo__core.bnk` (1). Each dialogue-event leaf resolves via containers to Sound objects
  (HIRC type 2) whose `sourceID` = wem filename. **Gotcha: sourceID is at CAkSound payload offset 5,
  not 8.** Index object-IDs in one pass (O(n²) rescan times out on the 6.6 MB campaign bank).
- Replacement method (proven by Smart Throgg mod): ship a mod pack with same-ID `.wem` files at the
  identical internal path, **no .bnk needed**. Originals in `audio_en.pack` are never touched →
  rollback = delete our pack.
- Duration: banks don't embed clip length and VO is streamed → longer/shorter clips should just
  play. Unverified by any modder write-up → verify in smoke test. FMV narration has a timing table
  (`subtitle_timings_tables`) — we're not touching FMVs.
- WAV→wem encoding **requires Audiokinetic Wwise 2019.2.15.7667** (free non-commercial license,
  has a macOS authoring tool; drive `WwiseConsole` in batch). No credible Wwise-free encoder.
  Decode direction is easy: `vgmstream-cli` (brew).
- No RPFM on macOS. Pack building: hand-rolled PFH5 writer in Python (header + `u32 size, u8 0x00,
  path\0` index + concatenated data — layout confirmed against real packs), fallback
  `cargo install rpfm_cli --version 4.5.4`.
- fal models for the bake-off (researched Sept 2026): **MiniMax** `fal-ai/minimax/voice-clone`
  ($1.50 one-off) → `fal-ai/minimax/speech-2.8-hd` ($0.10/1k chars, ONLY model with speed 0.5–2.0;
  set `output_format:"url"`; cloned voice deleted if unused 7 days), **ChatterboxHD**
  `resemble-ai/chatterboxhd/text-to-speech` ($0.04/1k, one-shot ref URL, 48 kHz, `exaggeration`
  knob, watermark), **F5-TTS** `fal-ai/f5-tts` ($0.05/1k, optional `ref_text`), **IndexTTS-2**
  `fal-ai/index-tts-2/text-to-speech` ($0.002/s, separate emotion reference). Auth: `FAL_KEY` env;
  upload ref once via `fal_client.upload_file()`; use queue API for batches.
- fal key is in `~/.fal/.env.rtf` as `fal_api` — an **RTF file**: parse/strip RTF, export as
  `FAL_KEY`. Never print or commit it.
- Total fal cost estimate: ~$5–10 (clone fee + a few hundred short lines + bake-off).

## Project layout (`/Users/kenneth/Documents/projects/warcraft/`, currently empty)

```
.venv/                  # brew python 3.12+; fal-client, mlx-whisper
tools/                  # packfile.py (PFH5 read/write), bnk_walk.py, extract, generate, encode, build
work/original_wem/      # backup of vanilla Nagash wems   (rollback archive)
work/original_wav/      # decoded via vgmstream
work/ref/               # Skeletor reference audio + transcript
work/gen/<model>/       # generated candidates + final takes
work/manifest.json      # per line: wem id, bank, duration, transcript, edited text, status
site-bakeoff/           # static share site (file://, dark), NOT an artifact
dist/                   # skeletor_nagash.pack + README + install/restore scripts, zippable
docs/                   # plan.md, progress.md, devblog.md
```

git init; .gitignore the big audio dirs and anything key-related.

## Phases

**0. Setup** — `brew install vgmstream yt-dlp python@3.12`; venv with `fal-client`, `mlx-whisper`;
key loader script (RTF→`FAL_KEY`). Kenneth installs Wwise 2019.2.15.7667 via Audiokinetic launcher
(manual; can proceed in parallel — only Phase 6 needs it).

**1. Extract** — `packfile.py` + `bnk_walk.py`: walk the 5 banks for hash 588314267, resolve all
wem IDs; extract from `audio_en.pack` → `work/original_wem/`; decode to wav; record duration/samples
in manifest. Expect ~100–400 files.

**2. Transcribe** — mlx-whisper over `original_wav/` → manifest. Review pass for Warhammer proper
nouns (Nehekhara, vitae, etc.) — Claude fixes against lore spellings; subtitles in `local_en.pack`
`.loc` files can be cross-referenced where findable.

**3. Smoke test (BEFORE spending on generation)** — encode one placeholder wav (any TTS/ffmpeg
tone+speech), build a 1-file pack, test loading on the Feral port: try Mod-type in
`TotalWarhammer3Data/data/` (+ enable), fallback Movie-type (force-loads). Also test a clip
deliberately ~2× original length → confirms no truncation. **This is the highest-risk unknown
(Feral launcher accepting hand-placed packs); fail here = stop and reassess (e.g. build/test on
MOJOJO's Windows copy).** Requires Wwise installed.

**4. Skeletor reference** — `yt-dlp` audio from classic Filmation Skeletor clip compilations;
ffmpeg-slice clean, music-free segments; assemble 10–30 s mono reference + exact transcript
(for F5's `ref_text`). Open the candidate slices for Kenneth to sanity-hear if he's around.

**5. Bake-off** — pick ~6 representative lines (short bark / long campaign / battle shout).
Generate each with all 4 models. Build `site-bakeoff/` per share-site rules: self-contained folder,
double-click `index.html`, dark default + toggle, rows = lines, columns = original + each model,
audio players + duration deltas. Verify from `file://` with `open`. **Kenneth picks the winner →
pause for his choice.**

**6. Full generation** — chosen model via fal queue API over every manifest line.
Duration policy per line: if generated length is outside ~0.85–1.2× of original, first shorten/
tighten the line's text (meaning preserved) and regenerate; then fine-tune with `ffmpeg atempo`
(≤ ~15% stretch; MiniMax: use its native `speed` instead). Loudness-match each take to its original
(loudnorm to measured LUFS), resample 48 kHz mono 16-bit. Track per-line status in manifest; resume-safe.

**7. Encode + pack** — batch `WwiseConsole` (Vorbis Quality High, 48 kHz mono, conversion settings
set before import) → `.wem`; verify each decodes via vgmstream; `packfile.py` writes
`skeletor_nagash.pack` (Mod type unless smoke test said Movie) with paths
`audio/wwise/english(uk)/<id>.wem`.

**8. Install + verify + package** — install on Mac, in-game check (frontend select line is the
instant test; then campaign selection + battle orders). Build `dist/`: the pack, README with Mac
(`TotalWarhammer3Data/data/`) and Windows (`...\Total War WARHAMMER III\data\` + mod manager)
install steps, uninstall/rollback instructions (delete pack; originals never modified; archived
wems in `work/original_wem/` as belt-and-braces). Zip for MOJOJO. Update docs/ per close-out routine.

## Verification

- Smoke test (Phase 3) proves: pack loads on Feral, replacement plays, over-length clip doesn't truncate.
- Bake-off site opened via `file://` before handing over.
- Final: launch game, hear Skeletor on lord select / campaign clicks / battle orders; spot-check
  ~10 random lines vs manifest; subtitles still appear (minor text drift acceptable on edited lines).
- Rollback test: remove pack → vanilla Nagash returns.

## Risks / notes

- **Feral launcher may reject or wipe hand-placed packs** — mitigated by early smoke test + keeping
  dist copy outside the game dir; Feral updates can auto-disable mods (re-enable after patches).
- Whisper will garble lore names — manual review pass planned.
- ChatterboxHD watermarks output (fine personal, relevant if published).
- "Maybe publish later": distributing a clone of a real actor's voice (Alan Oppenheimer) as a
  trademarked character is legally murky — flag again at publish time; keep pipeline clean so a
  different voice could be swapped in.
- MiniMax cloned voice expires if unused for 7 days — do the full run within a week of bake-off,
  or re-clone ($1.50).
- fal uploads are public-by-default URLs — use lifecycle expiry on the reference upload.

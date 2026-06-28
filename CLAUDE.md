# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

Interactive tool that assigns AI-generated face images to Football Manager newgens based on nationality/ethnicity. It reads `config.xml` directly from the user's FM faces folder, assigns faces to new players, backs up the original, and writes the updated config in place.

## How It Works

1. The script opens two native file picker dialogs:
   - Select the `config.xml` file from the FM faces folder
   - Select the `new_gen.rtf` export file from FM
2. It reads the existing config, parses the player export, determines an ethnicity pool for each unassigned player using weighted nationality probabilities, and randomly picks an unused face from that pool.
3. It creates a timestamped backup of `config.xml` in the script's folder, then overwrites the original with the merged result.
4. `faces_list.txt` is always read from the script's own directory (not the FM folder).

## Running

```
python generate_newgan_config.py
```

No command-line arguments — the script uses file picker dialogs for input. Requires tkinter (included in standard Windows Python installs).

## Key Files

- `generate_newgan_config.py` — main script (uses tkinter file picker dialogs)
- `country_ethnicity_probabilities.py` — single dict `COUNTRY_ETHNICITY_PROB` mapping FM 3-letter country codes to weighted ethnicity pools
- `faces_list.txt` — static inventory of all available face PNGs, read from script directory
- `generate_newgan_config_cli_backup.py` — backup of the previous CLI-based version

## Ethnicity Pools

Face images are organized into subdirectories by pool name. Pool names in `COUNTRY_ETHNICITY_PROB` must match folder names listed in `faces_list.txt`:

African, Asian, Caucasian, Central European, EECA, Italmed, MENA, MESA, SAMed, Scandinavian, Seasian, South American, SpanMed, YugoGreek

## Important Details

- Dual-nationality players blend both nationalities at 60/40 weighting (primary/secondary).
- If no faces remain unused in a pool, the script recycles (allows duplicates within that pool).
- If a player's resolved pool has no folder, it falls back to "Caucasian".
- `faces_list.txt` is typically UTF-16 encoded; the script tries multiple encodings via `read_text_auto()`.
- The script only assigns faces to players not already in `config.xml` (idempotent across runs).
- New records are inserted just before the closing `</list>` tag in the XML.
- Country codes follow FM conventions (e.g., `CRO` not `HRV`, `RSA` not `ZAF`).
- A timestamped backup (`config_backup_YYYYMMDD_HHMMSS.xml`) is created in the script's directory before each write.

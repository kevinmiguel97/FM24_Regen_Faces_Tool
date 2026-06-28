# Football Manager Newgen Face Assignment Tool

Automatically assigns AI-generated face images to Football Manager newgens (newly generated players) based on their nationality and ethnicity.

## Requirements

- Python 3.6+ (with tkinter, included in standard Windows Python installs)
- `faces_list.txt` in the same folder as the script (directory listing of all face PNGs)
- An FMNEWGAN-style faces folder containing:
  - `config.xml` (FM resource config)
  - Face image subdirectories organized by ethnicity pool

## Usage

### 1. Export newgens from Football Manager

Create a custom view in FM's player search with the following columns:

| UID | Nat | 2nd Nat | Name |
|-----|-----|---------|------|

Export the view and save the file (e.g. `new_gen.rtf`).

### 2. Run the script

```
python generate_newgan_config.py
```

Two file picker dialogs will open in sequence:

1. **Select your `config.xml`** -- navigate to your FM faces folder (e.g. `FMNEWGANv3`) and select the `config.xml` file
2. **Select your `new_gen.rtf`** -- navigate to wherever you saved the FM export file

The script will then:
1. Load available face pools from `faces_list.txt`
2. Read existing face assignments from `config.xml`
3. Parse the exported player list
4. Assign faces to new players
5. Create a timestamped backup of `config.xml` in the tool's folder (e.g. `config_backup_20260628_143022.xml`)
6. Write the updated `config.xml` directly in place

### 3. Reload skin in Football Manager

Go to Preferences > Interface > Reload Skin to see the new faces.

## Re-running Each Season

Each time you advance seasons and new newgens appear:

1. Export the updated player list from FM.
2. Run `python generate_newgan_config.py` and select the files via the dialogs.
3. Reload skin in FM.

Previously assigned players are skipped automatically — only new players get faces.

## How It Works

- Each player's nationality is mapped to ethnicity pools with weighted probabilities (defined in `country_ethnicity_probabilities.py`).
- Dual-nationality players blend both nationalities at a 60/40 ratio (primary/secondary).
- A face is randomly selected from the resolved pool, preferring unused faces to avoid duplicates.
- If a pool runs out of unused faces, it recycles from the full pool.
- If a nationality maps to a pool with no available folder, it falls back to "Caucasian".

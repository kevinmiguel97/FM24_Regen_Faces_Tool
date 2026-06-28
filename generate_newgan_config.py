import re
import sys
import random
import shutil
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from FM24_Regen_Faces_Tool.country_ethnicity_probabilities import COUNTRY_ETHNICITY_PROB

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILENAME = "config.xml"
FACES_LIST_FILENAME = "faces_list.txt"


def read_text_auto(file_path):
    for enc in ["utf-8", "utf-16", "utf-16-le", "latin1"]:
        try:
            return Path(file_path).read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode file: {file_path}")


def combined_ethnicity(n1, n2):
    p1 = COUNTRY_ETHNICITY_PROB.get(n1, {"Caucasian": 100})
    p2 = COUNTRY_ETHNICITY_PROB.get(n2, {})

    weights = defaultdict(float)
    for k, v in p1.items():
        weights[k] += v * 0.6
    for k, v in p2.items():
        weights[k] += v * 0.4

    pools = list(weights.keys())
    probs = list(weights.values())
    return random.choices(pools, weights=probs)[0]


def prompt_config_file(root):
    path = filedialog.askopenfilename(
        parent=root,
        title="Select config.xml in your FM Faces Folder",
        filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
    )
    if not path:
        print("  Cancelled.")
        sys.exit(0)

    path = Path(path)
    print(f"  Selected: {path}")
    return path


def prompt_export_file(root):
    path = filedialog.askopenfilename(
        parent=root,
        title="Select new_gen.rtf Export File",
        filetypes=[("RTF files", "*.rtf"), ("All files", "*.*")]
    )
    if not path:
        print("  Cancelled.")
        sys.exit(0)

    path = Path(path)
    print(f"  Selected: {path}")
    print(f"  [OK] Found {path.name}")
    return path


def load_face_pools():
    faces_text = read_text_auto(SCRIPT_DIR / FACES_LIST_FILENAME)
    faces_by_pool = defaultdict(list)

    for line in faces_text.splitlines():
        line = line.strip().replace("\\", "/")
        if "/" in line and line.endswith(".png"):
            pool, file = line.split("/")
            face = file.replace(".png", "")
            faces_by_pool[pool].append(face)

    total = sum(len(v) for v in faces_by_pool.values())
    print(f"  {len(faces_by_pool)} pools, {total:,} total faces")
    return faces_by_pool


def read_existing_config(config_path):
    config_text = read_text_auto(config_path)
    existing_players = set(re.findall(r"r-(\d+)", config_text))
    used_faces = set(re.findall(r'from="([^"]+)"', config_text))
    print(f"  {len(existing_players):,} existing players with faces")
    print(f"  {len(used_faces):,} faces already used")
    return config_text, existing_players, used_faces


def parse_export(export_path):
    rtf = read_text_auto(export_path)
    players = []

    for line in rtf.splitlines():
        if "|" not in line:
            continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 4:
            continue
        uid = cols[1]
        nat1 = cols[2]
        nat2 = cols[3]
        if uid.isdigit():
            players.append((uid, nat1, nat2))

    print(f"  {len(players):,} players detected in export")
    return players


def assign_faces(players, existing_players, used_faces, faces_by_pool):
    new_records = []
    missing_players = 0

    for uid, n1, n2 in players:
        if uid in existing_players:
            continue

        missing_players += 1
        pool = combined_ethnicity(n1, n2)

        if pool not in faces_by_pool:
            pool = "Caucasian"

        available = [
            f"{pool}/{f}"
            for f in faces_by_pool[pool]
            if f"{pool}/{f}" not in used_faces
        ]

        if not available:
            available = [
                f"{pool}/{f}"
                for f in faces_by_pool[pool]
            ]

        face = random.choice(available)
        used_faces.add(face)

        record = f'\t<record from="{face}" to="graphics/pictures/person/r-{uid}/portrait"/>'
        new_records.append(record)

    print(f"  {missing_players:,} players needing faces")
    print(f"  {len(new_records):,} faces assigned")
    return new_records


def backup_config(config_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"config_backup_{timestamp}.xml"
    backup_path = SCRIPT_DIR / backup_name
    shutil.copy2(config_path, backup_path)
    print(f"  Backed up config.xml -> {backup_name}")
    return backup_path


def write_config(config_text, new_records, config_path):
    insert_point = config_text.rfind("</list>")
    new_config = (
        config_text[:insert_point]
        + "\n".join(new_records)
        + "\n"
        + config_text[insert_point:]
    )
    config_path.write_text(new_config, encoding="utf-8")
    print(f"  Updated config.xml written ({len(new_records):,} new records)")


def main():
    print("\n=== Football Manager Newgen Face Assignment Tool ===\n")

    root = tk.Tk()
    root.withdraw()

    config_path = prompt_config_file(root)
    export_path = prompt_export_file(root)

    root.destroy()

    print("\nLoading face pools...")
    faces_by_pool = load_face_pools()

    print("\nReading existing config...")
    config_text, existing_players, used_faces = read_existing_config(config_path)

    print("\nParsing export file...")
    players = parse_export(export_path)

    print("\nAssigning faces...")
    new_records = assign_faces(players, existing_players, used_faces, faces_by_pool)

    if not new_records:
        print("\nNo new faces to assign. All exported players already have faces.")
        return

    print()
    backup_config(config_path)
    write_config(config_text, new_records, config_path)

    print("\nDone! Reload skin in Football Manager to see the new faces.")


if __name__ == "__main__":
    main()

import re
import sys
import random
import shutil
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


def prompt_faces_folder():
    print("Enter the FM faces folder path")
    print("  (folder containing config.xml and face image subfolders)")
    print("  (or 'q' to quit)")

    while True:
        raw = input("> ").strip().strip('"').strip("'")

        if raw.lower() == "q":
            sys.exit(0)

        folder = Path(raw)

        if not folder.is_dir():
            print(f"  Error: Directory not found: {folder}\n")
            continue

        if (folder / CONFIG_FILENAME).is_file():
            print(f"  [OK] Found {CONFIG_FILENAME}")
        else:
            print(f"  Error: {CONFIG_FILENAME} not found in {folder}\n")
            continue

        return folder


def prompt_export_file():
    print("\nEnter the path to the new_gen.rtf export file")
    print("  (or 'q' to quit)")

    while True:
        raw = input("> ").strip().strip('"').strip("'")

        if raw.lower() == "q":
            sys.exit(0)

        path = Path(raw)

        if not path.is_file():
            print(f"  Error: File not found: {path}\n")
            continue

        if path.suffix.lower() != ".rtf":
            print(f"  Warning: Expected .rtf file, got {path.suffix}. Continuing anyway...")

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

    faces_folder = prompt_faces_folder()
    export_path = prompt_export_file()

    config_path = faces_folder / CONFIG_FILENAME

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

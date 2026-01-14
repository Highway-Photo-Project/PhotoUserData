import os
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(BASE_DIR, "list_files", "TBKS1.list")
SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")


def load_systems():
    """
    Load all _systems/*.csv files.
    Keyed by (region, display_name)
    """
    systems = {}

    for filename in os.listdir(SYSTEMS_DIR):
        if not filename.endswith(".csv"):
            continue

        path = os.path.join(SYSTEMS_DIR, filename)
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if len(row) < 3:
                    continue

                route_code = row[0].strip()      # I10
                region = row[1].strip()          # AL
                display = row[2].strip()         # I-10

                systems[(region, display)] = {
                    "file": filename,
                    "code": route_code
                }

    return systems

def parse_list_file():
    """
    Parse TBKS1.list
    Returns list of (region, route)
    """
    entries = []

    with open(LIST_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                region, route = line.split(maxsplit=1)
                entries.append((region, route))
            except ValueError:
                print(f"⚠️ Invalid line format: {line}")

    return entries


def validate():
    systems = load_systems()
    entries = parse_list_file()

    missing = []

    for region, route in entries:
        if (region, route) not in systems:
            missing.append(f"{region} {route}")

    print(f"Checked {len(entries)} routes")

    if missing:
        print("\n❌ Missing routes:")
        for m in missing:
            print(" ", m)
        exit(1)
    else:
        print("✅ All routes found in _systems")


if __name__ == "__main__":
    validate()

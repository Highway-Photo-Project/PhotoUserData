import os
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(BASE_DIR, "list_files", "TBKS1.list")
SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")


def load_systems():
    """
    Loads all _systems CSV files.


    Returns:
      systems: (region, display_name) -> { file, code }
      system_totals: system_file -> total routes in that system
    """
    systems = {}
    system_totals = {}

    for filename in os.listdir(SYSTEMS_DIR):
        if not filename.endswith(".csv"):
            continue

        path = os.path.join(SYSTEMS_DIR, filename)
        system_totals[filename] = 0

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")

            next(reader, None)

            for row in reader:
                if len(row) < 3:
                    continue

                route_code = row[0].strip()
                region = row[1].strip()
                display = row[2].strip()




                systems[(region, display)] = {
                    "file": filename,
                    "code": route_code
                }

                system_totals[filename] += 1

    return systems, system_totals

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
    systems, system_totals = load_systems()
    entries = parse_list_file()

    total_list_routes = len(entries)

    matched_by_system = {}
    missing = []

    for region, route in entries:
        key = (region, route)

        if key not in systems:
            missing.append(f"{region} {route}")
            continue

        system_file = systems[key]["file"]
        matched_by_system.setdefault(system_file, set()).add(
            f"{region} {route}"
        )

    print(f"\nTotal routes in list: {total_list_routes}")

    # ---- TABLE OUTPUT (this replaces the old print loop) ----
    rows = []

    for system_file in sorted(system_totals):
        matched = len(matched_by_system.get(system_file, set()))
        total = system_totals[system_file]
        coverage = (matched / total * 100) if total else 0.0

        rows.append([
            system_file,
            matched,
            total,
            f"{coverage:.2f}%"
        ])

    print("\nSystem coverage:")
    print(tabulate(
        rows,
        headers=["System", "Matched", "Total", "Coverage"],
        tablefmt="github"
    ))
    # ---- END TABLE OUTPUT ----

    if missing:
        print("\n❌ Missing routes:")
        for m in sorted(missing):
            print(" ", m)
    else:
        print("\n✅ All routes found in systems")


if __name__ == "__main__":
    validate()

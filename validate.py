import os
import csv
from tabulate import tabulate

# -------------------------
# Paths
# -------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_FILE = os.path.join(BASE_DIR, "list_files", "TBKS1.list")
SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")
SYSTEMS_INDEX = os.path.join(BASE_DIR, "..", "PhotoData", "systems.csv")

HTML_OUT = os.path.join(BASE_DIR, "coverage.html")

# -------------------------
# Load system route files
# -------------------------

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
            next(reader, None)  # header

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

# -------------------------
# Load user .list file
# -------------------------

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

# -------------------------
# Load system name index
# -------------------------

def load_system_name_map():
    """
    Loads systems.csv
    Returns:
      { system_code -> full system name }
    """
    name_map = {}

    with open(SYSTEMS_INDEX, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)  # header

        for row in reader:
            if len(row) < 3:
                continue

            system_code = row[0].strip()
            full_name = row[2].strip()

            name_map[system_code] = full_name

    return name_map

# -------------------------
# Validation + Reporting
# -------------------------

def validate():
    systems, system_totals = load_systems()
    system_names = load_system_name_map()
    entries = parse_list_file()

    total_list_routes = len(entries)

    matched_by_system = {}
    missing = []
    route_rows = []

    # ---- Route-level validation ----
    for region, route in entries:
        key = (region, route)

        if key not in systems:
            missing.append(f"{region} {route}")
            route_rows.append((region, route, "UNKNOWN", "Missing"))
            continue

        system_file = systems[key]["file"]
        system_code = system_file.replace(".csv", "")
        system_name = system_names.get(system_code, system_code)

        matched_by_system.setdefault(system_file, set()).add(
            f"{region} {route}"
        )

        route_rows.append((region, route, system_name, "Matched"))

    print(f"\nTotal routes in list: {total_list_routes}")

    # ---- System summary table ----
    rows = []

    for system_file in sorted(system_totals):
        matched = len(matched_by_system.get(system_file, set()))
        total = system_totals[system_file]
        coverage = (matched / total * 100) if total else 0.0

        system_code = system_file.replace(".csv", "")
        system_name = system_names.get(system_code, system_code)

        rows.append([
            system_name,
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

    # ---- HTML export ----
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Route Coverage</title>
<style>
body { font-family: Arial, sans-serif; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 4px 8px; }
th { background: #eee; }
.matched { background-color: #d4edda; }
.missing { background-color: #f8d7da; }
</style>
</head>
<body>
<h1>Route Coverage</h1>
<table>
<tr>
  <th>Region</th>
  <th>Route</th>
  <th>System</th>
  <th>Status</th>
</tr>
""")

        for region, route, system, status in route_rows:
            css_class = "matched" if status == "Matched" else "missing"
            f.write(
                f"<tr class='{css_class}'>"
                f"<td>{region}</td>"
                f"<td>{route}</td>"
                f"<td>{system}</td>"
                f"<td>{status}</td>"
                f"</tr>\n"
            )

        f.write("""
</table>
</body>
</html>
""")

    if missing:
        print(f"\n❌ Missing routes: {len(missing)}")
    else:
        print("\n✅ All routes found in systems")

    print(f"\n📄 HTML report written to: {HTML_OUT}")

# -------------------------
# Entry point
# -------------------------

if __name__ == "__main__":
    validate()

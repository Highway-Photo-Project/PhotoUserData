import os
import csv
from tabulate import tabulate

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_FILE = os.path.join(BASE_DIR, "list_files", "TBKS1.list")
SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")
SYSTEMS_INDEX = os.path.join(BASE_DIR, "..", "PhotoData", "systems.csv")

HTML_OUT = os.path.join(BASE_DIR, "system_coverage.html")

# --------------------------------------------------
# Load system route definitions
# --------------------------------------------------

def load_systems():
    """
    Returns:
      systems:
        (region, display) -> {
            "file": system_file,
            "route_code": route_code
        }

      system_routes:
        system_file -> set(route_code)
        (deduplicated by route code ONLY)
    """
    systems = {}
    system_routes = {}

    for filename in os.listdir(SYSTEMS_DIR):
        if not filename.endswith(".csv"):
            continue

        path = os.path.join(SYSTEMS_DIR, filename)
        system_routes[filename] = set()

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
                    "route_code": route_code
                }

                # FINAL RULE:
                # Count each route designation only once per system
                system_routes[filename].add(route_code)

    return systems, system_routes

# --------------------------------------------------
# Parse .list file
# --------------------------------------------------

def parse_list_file():
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
                pass

    return entries

# --------------------------------------------------
# Load system display names
# --------------------------------------------------

def load_system_name_map():
    """
    systems.csv:
      System;Country;Name;Tier
    """
    name_map = {}

    with open(SYSTEMS_INDEX, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)

        for row in reader:
            if len(row) < 3:
                continue

            system_code = row[0].strip()
            full_name = row[2].strip()
            name_map[system_code] = full_name

    return name_map

# --------------------------------------------------
# Travel Mapping–style HSL coloring
# --------------------------------------------------

def completion_to_hsl(percent):
    """
    Replicates Travel Mapping table coloring.

    0%   -> red
    100% -> green

    TM-style parameters:
      hue: 0–150
      saturation: 70%
      lightness: 80%
    """
    max_hue = 150.0
    hue = percent * max_hue / 100.0
    return f"hsl({hue:.6f}, 70%, 80%)"

# --------------------------------------------------
# Main validation
# --------------------------------------------------

def validate():
    systems, system_routes = load_systems()
    system_names = load_system_name_map()
    entries = parse_list_file()

    matched_routes = {}

    # Track matched route codes (deduped)
    for region, route in entries:
        key = (region, route)
        if key not in systems:
            continue

        info = systems[key]
        system_file = info["file"]
        route_code = info["route_code"]

        matched_routes.setdefault(system_file, set()).add(route_code)

    # Build system summary
    summary = []

    for system_file, route_codes in system_routes.items():
        total = len(route_codes)
        matched = len(matched_routes.get(system_file, set()))
        pct = (matched / total * 100) if total else 0.0

        system_code = system_file.replace(".csv", "")
        system_name = system_names.get(system_code, system_code)

        summary.append((system_name, matched, total, pct))

    # Sort like Travel Mapping (highest completion first)
    summary.sort(key=lambda r: r[3], reverse=True)

    # --------------------------------------------------
    # Console output
    # --------------------------------------------------

    print("\nSystem coverage:")
    print(tabulate(
        [(s, m, t, f"{p:.2f}%") for s, m, t, p in summary],
        headers=["System", "Matched", "Total", "Completion"],
        tablefmt="github"
    ))

    # --------------------------------------------------
    # HTML output (TM-style)
    # --------------------------------------------------

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Highway System Completion</title>
<style>
body {
  font-family: Arial, sans-serif;
}
table {
  border-collapse: collapse;
  width: 100%;
}
th, td {
  border: 1px solid #ccc;
  padding: 6px 8px;
}
th {
  background: #eee;
}
td.num {
  text-align: right;
}
</style>
</head>
<body>

<h1>Highway System Completion</h1>

<table>
<tr>
  <th>System</th>
  <th>Matched</th>
  <th>Total</th>
  <th>Completion</th>
</tr>
""")

        for system, matched, total, pct in summary:
            color = completion_to_hsl(pct)
            f.write(
                "<tr>"
                f"<td>{system}</td>"
                f"<td class='num'>{matched}</td>"
                f"<td class='num'>{total}</td>"
                f"<td class='num' style='background-color: {color};' "
                f"data-sort='{pct:.2f}'>{pct:.2f}%</td>"
                "</tr>\n"
            )

        f.write("""
</table>
</body>
</html>
""")

    print(f"\n📄 HTML report written to: {HTML_OUT}")

# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    validate()

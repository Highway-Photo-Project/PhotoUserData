import os
import csv
from tabulate import tabulate

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_DIR = os.path.join(BASE_DIR, "list_files")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")
SYSTEMS_INDEX = os.path.join(BASE_DIR, "..", "PhotoData", "systems.csv")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# Load system route definitions
# --------------------------------------------------

def load_systems():
    """
    Returns:
      systems:
        (region, route_name) -> {
            "file": system_file,
            "route_code": route_name
        }

      system_routes:
        system_file -> set(route_name)
        (deduplicated by route designation ONLY)
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

                region = row[1].strip()
                route_name = row[2].strip()

                systems[(region, route_name)] = {
                    "file": filename,
                    "route_code": route_name
                }

                # FINAL RULE:
                # Count each route designation once per system
                system_routes[filename].add(route_name)

    return systems, system_routes

# --------------------------------------------------
# Parse a .list file
# --------------------------------------------------

def parse_list_file(path):
    entries = []

    with open(path, encoding="utf-8") as f:
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
    Completion-based color scale:
      0%   -> hsl(0,   70%, 80%)
      100% -> hsl(240, 70%, 80%)
    """
    max_hue = 240.0
    hue = percent * max_hue / 100.0
    return f"hsl({hue:.6f}, 70%, 80%)"

# --------------------------------------------------
# HTML report writer
# --------------------------------------------------

def write_html_report(user_id, summary, html_out):
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{user_id} – Highway System Completion</title>
<style>
body {{
  font-family: Arial, sans-serif;
}}
table {{
  border-collapse: collapse;
  width: 100%;
}}
th, td {{
  border: 1px solid #ccc;
  padding: 6px 8px;
}}
th {{
  background: #eee;
}}
td.num {{
  text-align: right;
}}
</style>
</head>
<body>

<h1>{user_id} – Highway System Completion</h1>

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

# --------------------------------------------------
# Main multi-user validation
# --------------------------------------------------

def validate_all():
    systems, system_routes = load_systems()
    system_names = load_system_name_map()

    for filename in sorted(os.listdir(LIST_DIR)):
        if not filename.endswith(".list"):
            continue

        user_id = os.path.splitext(filename)[0]
        list_path = os.path.join(LIST_DIR, filename)
        html_out = os.path.join(OUTPUT_DIR, f"{user_id}.html")

        entries = parse_list_file(list_path)
        matched_routes = {}

        for region, route in entries:
            key = (region, route)
            if key not in systems:
                continue

            info = systems[key]
            system_file = info["file"]
            route_code = info["route_code"]

            matched_routes.setdefault(system_file, set()).add(route_code)

        summary = []

        for system_file, route_codes in system_routes.items():
            total = len(route_codes)
            matched = len(matched_routes.get(system_file, set()))
            pct = (matched / total * 100) if total else 0.0

            system_code = system_file.replace(".csv", "")
            system_name = system_names.get(system_code, system_code)

            summary.append((system_name, matched, total, pct))

        summary.sort(key=lambda r: r[3], reverse=True)

        # Console output (per user)
        print(f"\nUser: {user_id}")
        print(tabulate(
            [(s, m, t, f"{p:.2f}%") for s, m, t, p in summary],
            headers=["System", "Matched", "Total", "Completion"],
            tablefmt="github"
        ))

        write_html_report(user_id, summary, html_out)
        print(f"📄 HTML report written to: {html_out}")

# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    validate_all()

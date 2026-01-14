import os
import csv
from tabulate import tabulate

# -------------------------
# Paths (adjust as needed)
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

def load_system_name_map():
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

# -------------------------
# Color scale helper
# -------------------------

def coverage_class(coverage_pct):
    """
    Chooses a CSS class based on coverage %.
    High = green, medium = yellow/orange, low = red.
    """
    if coverage_pct >= 90:
        return "cov-90"
    if coverage_pct >= 75:
        return "cov-75"
    if coverage_pct >= 50:
        return "cov-50"
    if coverage_pct >= 25:
        return "cov-25"
    return "cov-0"

def validate():
    systems, system_totals = load_systems()
    system_names = load_system_name_map()
    entries = parse_list_file()

    total_list_routes = len(entries)
    matched_by_system = {}
    route_rows = []

    for region, route in entries:
        key = (region, route)
        if key not in systems:
            route_rows.append((region, route, "UNKNOWN"))
            continue
        system_file = systems[key]["file"]
        matched_by_system.setdefault(system_file, set()).add(f"{region} {route}")
        system_code = system_file.replace(".csv", "")
        system_name = system_names.get(system_code, system_code)
        route_rows.append((region, route, system_name))

    # Compute system coverage
    system_coverage = {}
    for system_file in system_totals:
        matched = len(matched_by_system.get(system_file, set()))
        total = system_totals[system_file]
        coverage_pct = (matched / total * 100) if total else 0.0

        system_code = system_file.replace(".csv", "")
        system_name = system_names.get(system_code, system_code)
        system_coverage[system_name] = coverage_pct

    # ---- Console summary ----
    rows = []
    for system_file in sorted(system_totals):
        matched = len(matched_by_system.get(system_file, set()))
        total = system_totals[system_file]
        coverage_pct = (matched / total * 100) if total else 0.0
        system_code = system_file.replace(".csv", "")
        system_name = system_names.get(system_code, system_code)
        rows.append([
            system_name,
            matched,
            total,
            f"{coverage_pct:.2f}%"
        ])

    print("\nSystem coverage:")
    print(tabulate(rows, headers=["System", "Matched", "Total", "Coverage"], tablefmt="github"))

    # ---- Write HTML ----
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Route Coverage</title>
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
    padding: 6px;
}}
th {{
    background: #f2f2f2;
}}

/* color scale similar to TravelMapping completion style */
.cov-90 {{ background: #4CAF50; color: white; }}   /* ~90–100% */
.cov-75 {{ background: #8BC34A; }}                 /* ~75–89% */
.cov-50 {{ background: #FFEB3B; }}                 /* ~50–74% */
.cov-25 {{ background: #FF9800; }}                 /* ~25–49% */
.cov-0  {{ background: #F44336; color: white; }}   /* 0–24% */
</style>
</head>
<body>

<h1>Route Coverage Report</h1>

<h2>Legend</h2>
<ul>
<li class='cov-90'>90–100% complete</li>
<li class='cov-75'>75–89% complete</li>
<li class='cov-50'>50–74% complete</li>
<li class='cov-25'>25–49% complete</li>
<li class='cov-0'>0–24% complete</li>
</ul>

<table>
<tr>
  <th>Region</th>
  <th>Route</th>
  <th>System</th>
  <th>System Completion</th>
</tr>
""")

        for region, route, system in route_rows:
            cov_pct = system_coverage.get(system, 0)
            css_class = coverage_class(cov_pct)
            f.write(
                f"<tr class='{css_class}'>"
                f"<td>{region}</td>"
                f"<td>{route}</td>"
                f"<td>{system}</td>"
                f"<td>{cov_pct:.1f}%</td>"
                f"</tr>\n"
            )

        f.write("""
</table>
</body>
</html>
""")

    print(f"\nHTML report written to: {HTML_OUT}")

if __name__ == "__main__":
    validate()

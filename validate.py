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

HTML_OUT = os.path.join(BASE_DIR, "system_coverage.html")

# -------------------------
# Load systems
# -------------------------

def load_systems():
    systems = {}
    system_totals = {}

    for filename in os.listdir(SYSTEMS_DIR):
        if not filename.endswith(".csv"):
            continue

        system_totals[filename] = 0
        path = os.path.join(SYSTEMS_DIR, filename)

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)

            for row in reader:
                if len(row) < 3:
                    continue

                region = row[1].strip()
                display = row[2].strip()

                systems[(region, display)] = filename
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
            name_map[row[0].strip()] = row[2].strip()
    return name_map

# -------------------------
# HSL color calculation
# -------------------------

def completion_to_hsl(percent):
    """
    Replicates Travel Mapping style coloring.
    0% = red, 100% = green.
    """
    max_hue = 150.0
    hue = percent * max_hue / 100.0
    return f"hsl({hue:.2f}, 70%, 80%)"

# -------------------------
# Main validation
# -------------------------

def validate():
    systems, system_totals = load_systems()
    system_names = load_system_name_map()
    entries = parse_list_file()

    matched_by_system = {}

    for region, route in entries:
        key = (region, route)
        if key not in systems:
            continue
        system_file = systems[key]
        matched_by_system.setdefault(system_file, set()).add(key)

    # Build system summary
    summary = []

    for system_file, total in system_totals.items():
        matched = len(matched_by_system.get(system_file, set()))
        pct = (matched / total * 100) if total else 0.0

        system_code = system_file.replace(".csv", "")
        system_name = system_names.get(system_code, system_code)

        summary.append((system_name, matched, total, pct))

    # Sort by completion (like TM often does)
    summary.sort(key=lambda r: r[3], reverse=True)

    # Console table
    print("\nSystem coverage:")
    print(tabulate(
        [(s, m, t, f"{p:.2f}%") for s, m, t, p in summary],
        headers=["System", "Matched", "Total", "Completion"],
        tablefmt="github"
    ))

    # HTML output
    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>System Coverage</title>
<style>
body { font-family: Arial, sans-serif; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px; }
th { background: #eee; }
td.num { text-align: right; }
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

# -------------------------
# Entry point
# -------------------------

if __name__ == "__main__":
    validate()

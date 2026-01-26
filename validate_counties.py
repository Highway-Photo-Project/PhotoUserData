import csv
import os
import glob
from collections import defaultdict

# ---------------- CONFIG ---------------- #

LISTS_DIR = "lists"
COUNTY_DATA_DIR = "../PhotoData/_counties"
OUTPUT_DIR = "outputs/counties"
FONT_PATH = "ModeNine.ttf"  # put the font file next to the HTML output

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------- #


def hsl_for_percentage(pct):
    """
    0%   -> hsl(0, 80%, 80%)
    100% -> hsl(240, 80%, 80%)
    """
    hue = (pct / 100) * 240
    return f"hsl({hue:.2f}, 80%, 80%)"


def load_user_completed_pairs(list_path):
    """
    Reads ONE .list file and returns a set of (region, route) pairs
    """
    completed = set()

    with open(list_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "." not in line:
                continue

            system, route = line.split(".", 1)

            region = system[-2:].upper()
            route = route.upper()

            completed.add((region, route))

    return completed


def load_state_counties(csv_path):
    """
    Expected CSV format (with or without header):
      Region;Route;County
    """
    county_routes = defaultdict(set)
    region_code = None

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")

        for row in reader:
            # skip empty rows
            if not row or len(row) < 3:
                continue

            # skip header row if present
            if row[0].lower() in ("region", "state"):
                continue

            region = row[0].strip().upper()
            route = row[1].strip().upper()
            county = row[2].strip()

            region_code = region
            county_routes[county].add(route)

    return region_code, county_routes


def write_state_html(state, rows):
    out_path = os.path.join(OUTPUT_DIR, f"{state}_counties.html")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{state} County Completion</title>
<style>
@font-face {{
  font-family: "ModeNine";
  src: url("ModeNine.ttf") format("truetype");
}}

body {{
  font-family: ModeNine, sans-serif;
}}

table {{
  border-collapse: collapse;
  margin-left: 0;
  width: 700px;
}}

th, td {{
  border: 1px solid #444;
  padding: 6px 10px;
}}

th {{
  background-color: #ddd;
}}

td.right {{
  text-align: right;
}}
</style>
</head>
<body>

<h2>{state} County Completion</h2>

<table>
<tr>
  <th>County</th>
  <th>Total Routes</th>
  <th>Completed</th>
  <th>Percent</th>
</tr>
""")

        for county, total, matched, pct in rows:
            color = hsl_for_percentage(pct)
            f.write(f"""
<tr>
  <td>{county}</td>
  <td class="right">{total}</td>
  <td class="right">{matched}</td>
  <td class="right" style="background-color: {color};" data-sort="{pct:.2f}">
    {pct:.2f}%
  </td>
</tr>
""")

        f.write("""
</table>
</body>
</html>
""")


def validate_counties():
    list_files = glob.glob(os.path.join(LISTS_DIR, "*.list"))

    # load all user completions separately
    user_completed = [
        load_user_completed_pairs(path)
        for path in list_files
    ]

    for csv_path in glob.glob(os.path.join(COUNTY_DATA_DIR, "*_counties.csv")):
        region, county_routes = load_state_counties(csv_path)

        rows = []

        for county, routes in sorted(county_routes.items()):
            total = len(routes)
            matched = 0

            for route in routes:
                if any((region, route) in user for user in user_completed):
                    matched += 1

            pct = (matched / total * 100) if total else 0
            rows.append((county, total, matched, pct))

        write_state_html(region, rows)


if __name__ == "__main__":
    validate_counties()

import os
import csv

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_DIR = os.path.join(BASE_DIR, "list_files")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "counties")
COUNTIES_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_counties")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# Utilities
# --------------------------------------------------

def completion_to_hsl(percent):
    percent = max(0.0, min(100.0, percent))
    hue = percent * 240.0 / 100.0
    return f"hsl({hue:.6f}, 80%, 80%)"

# --------------------------------------------------
# Parse .list files (ALL users combined)
# --------------------------------------------------

def load_all_list_routes():
    """
    Returns:
      region -> set(route)
    """
    routes_by_region = {}

    for filename in os.listdir(LIST_DIR):
        if not filename.endswith(".list"):
            continue

        path = os.path.join(LIST_DIR, filename)

        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                try:
                    region, route = line.split(maxsplit=1)
                except ValueError:
                    continue

                routes_by_region.setdefault(region, set()).add(route)

    return routes_by_region

# --------------------------------------------------
# Load county inventory for one state
# --------------------------------------------------

def load_state_counties(path):
    """
    CSV format:
      Region;Route;County

    Returns:
      region_code
      county_routes:
        county_name -> set(route)
    """
    county_routes = {}
    region_code = None

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        # Normalize headers (case-insensitive)
        headers = {h.lower(): h for h in reader.fieldnames}

        region_col = headers.get("region")
        route_col = headers.get("route")
        county_col = headers.get("county")

        if not region_col or not route_col or not county_col:
            raise RuntimeError(
                f"{os.path.basename(path)} has unexpected headers: {reader.fieldnames}"
            )

        for row in reader:
            region = row[region_col].strip()
            route = row[route_col].strip()
            county = row[county_col].strip()

            region_code = region
            county_routes.setdefault(county, set()).add(route)

    return region_code, county_routes

# --------------------------------------------------
# HTML writer
# --------------------------------------------------

def write_county_html(state, county_summary, html_out):
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{state} – County Completion</title>

<style>
body {{
  font-family: Arial, sans-serif;
}}

.table-container {{
  max-width: 1000px;
  margin: 0 auto;
}}

table {{
  border-collapse: collapse;
  width: auto;
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
  white-space: nowrap;
}}
</style>
</head>
<body>

<h1>{state} – County Completion</h1>

<div class="table-container">
<table>
<tr>
  <th>County</th>
  <th>Matched</th>
  <th>Total</th>
  <th>Completion</th>
</tr>
""")

        for county, matched, total, pct in county_summary:
            color = completion_to_hsl(pct)
            f.write(
                "<tr>"
                f"<td>{county}</td>"
                f"<td class='num'>{matched}</td>"
                f"<td class='num'>{total}</td>"
                f"<td class='num' style='background-color: {color};'>{pct:.2f}%</td>"
                "</tr>\n"
            )

        f.write("""
</table>
</div>
</body>
</html>
""")

# --------------------------------------------------
# Main
# --------------------------------------------------

def validate_counties():
    user_routes = load_all_list_routes()

    for filename in sorted(os.listdir(COUNTIES_DIR)):
        if not filename.endswith("_counties.csv"):
            continue

        state = filename.replace("_counties.csv", "")
        path = os.path.join(COUNTIES_DIR, filename)

        region_code, county_routes = load_state_counties(path)
        user_state_routes = user_routes.get(region_code, set())

        county_summary = []

        for county, routes in county_routes.items():
            total = len(routes)
            matched = len(routes & user_state_routes)
            pct = (matched / total * 100) if total else 0.0
            county_summary.append((county, matched, total, pct))

        county_summary.sort(key=lambda r: r[3], reverse=True)

        html_out = os.path.join(OUTPUT_DIR, f"{state}_counties.html")
        write_county_html(state, county_summary, html_out)

        print(f"📄 {html_out}")

# --------------------------------------------------

if __name__ == "__main__":
    validate_counties()

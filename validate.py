import os
import csv
from tabulate import tabulate


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_DIR = os.path.join(BASE_DIR, "list_files")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")
REGIONS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_regions")
SYSTEMS_INDEX = os.path.join(BASE_DIR, "..", "PhotoData", "systems.csv")
REGIONS_INDEX = os.path.join(BASE_DIR, "..", "PhotoData", "regions.csv")
STATE_BASE_URL = "https://tbks1.neocities.org/TBKS1/states"


os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_systems():
    """
    Returns:
      systems:
        (region, route_name) -> system_file
      system_routes:
        system_file -> set(route_name)
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
            next(reader, None)

            for row in reader:
                if len(row) < 3:
                    continue

                region = row[1].strip()
                route_name = row[2].strip()

                systems[(region, route_name)] = filename
                system_routes[filename].add(route_name)

    return systems, system_routes


def load_regions():
    """
    Returns:
      region_routes:
        region_code -> set(route_name)
    """
    region_routes = {}

    for filename in os.listdir(REGIONS_DIR):
        if not filename.endswith(".csv"):
            continue

        region = os.path.splitext(filename)[0]
        path = os.path.join(REGIONS_DIR, filename)

        region_routes[region] = set()

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)  # header

            for row in reader:
                # Expecting at least: system / region / route
                if len(row) < 3:
                    continue

                route_name = row[2].strip()

                # Deduplicate by route designation ONLY
                region_routes[region].add(route_name)

    return region_routes

def load_region_name_map():
    """
    Loads region abbreviation -> full name mapping from regions.csv
    Header names are auto-detected to avoid KeyError.
    """
    name_map = {}

    with open(REGIONS_INDEX, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        # Normalize header names
        fieldnames = {h.lower(): h for h in reader.fieldnames}

        # Detect columns safely
        code_col = fieldnames.get("region") or fieldnames.get("code") or fieldnames.get("abbrev")
        name_col = fieldnames.get("name") or fieldnames.get("state")

        if not code_col or not name_col:
            raise RuntimeError(
                f"regions.csv must contain columns for region code and name. "
                f"Found headers: {reader.fieldnames}"
            )

        for row in reader:
            region_code = row[code_col].strip()
            full_name = row[name_col].strip()
            name_map[region_code] = full_name

    return name_map
    

def parse_list_file(path):
    entries = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(maxsplit=2)
            if len(parts) < 2:
                continue

            region = parts[0]
            route = parts[1]
            url = parts[2] if len(parts) > 2 else None

            entries.append((region, route, url))

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


def completion_to_hsl(percent):
    percent = max(0.0, min(100.0, percent))
    hue = percent * 240.0 / 100.0
    return f"hsl({hue:.6f}, 80%, 80%)"


def write_html_report(title, label, summary, html_out, link_map=None):
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>

<style>
@font-face {{
  font-family: "ModeNine";
  src: url("../fonts/ModeNine-Regular.woff2") format("woff2"),
       url("../fonts/ModeNine-Regular.woff") format("woff");
}}

body {{
  font-family: "ModeNine", Arial, sans-serif;
}}

table {{
  border-collapse: collapse;
  width: 50%;
}}

table, tr, td {{
  position: relative;
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
  font-variant-numeric: tabular-nums;
}}

td a {{
  display: block;
  width: 100%;
  height: 100%;
  color: inherit;
  text-decoration: underline;
  pointer-events: auto;
  cursor: pointer;
}}
</style>
</head>
<body>

<h1>{title}</h1>

<table>
<tr>
  <th>{label}</th>
  <th>Caught</th>
  <th>Total</th>
  <th>Completion</th>
</tr>
""")

        for name, matched, total, pct in summary:
            color = completion_to_hsl(pct)

            if link_map and name in link_map:
                name_cell = f"<a href='{link_map[name]}'>{name}</a>"
            else:
                name_cell = name

            f.write(
                "<tr>"
                f"<td>{name_cell}</td>"
                f"<td class='num'>{matched}</td>"
                f"<td class='num'>{total}</td>"
                f"<td class='num' style='background-color: {color};'>{pct:.2f}%</td>"
                "</tr>\n"
            )

        f.write("""
</table>
</body>
</html>
""")

        for name, matched, total, pct in summary:
            color = completion_to_hsl(pct)

            if link_map and name in link_map:
                name_cell = f"<a href='{link_map[name]}'>{name}</a>"
            else:
                name_cell = name

            f.write(
                "<tr>"
                f"<td>{name_cell}</td>"
                f"<td class='num'>{matched}</td>"
                f"<td class='num'>{total}</td>"
                f"<td class='num' style='background-color: {color};'>{pct:.2f}%</td>"
                "</tr>\n"
            )

        f.write("""
</table>
</body>
</html>
""")



def validate_all():
    systems, system_routes = load_systems()
    region_routes = load_regions()
    system_names = load_system_name_map()
    region_names = load_region_name_map()
    region_link_map = {
    full_name: f"{STATE_BASE_URL}/{code}"
    for code, full_name in region_names.items()
}

    for filename in sorted(os.listdir(LIST_DIR)):
        if not filename.endswith(".list"):
            continue

        user_id = os.path.splitext(filename)[0]
        list_path = os.path.join(LIST_DIR, filename)

        entries = parse_list_file(list_path)


        matched_by_system = {}

        for region, route, _ in entries:
            key = (region, route)
            if key not in systems:
                continue

            system_file = systems[key]
            matched_by_system.setdefault(system_file, set()).add(route)

        system_summary = []

        for system_file, routes in system_routes.items():
            total = len(routes)
            matched = len(matched_by_system.get(system_file, set()))
            pct = (matched / total * 100) if total else 0.0

            system_code = system_file.replace(".csv", "")
            system_name = system_names.get(system_code, system_code)

            system_summary.append((system_name, matched, total, pct))

        system_summary.sort(key=lambda r: r[3], reverse=True)


        matched_by_region = {}

        for region, route, _ in entries:
            if region not in region_routes:
                continue

            if route in region_routes[region]:
                matched_by_region.setdefault(region, set()).add(route)

        region_summary = []

        for region, routes in region_routes.items():
            total = len(routes)
            matched = len(matched_by_region.get(region, set()))
            pct = (matched / total * 100) if total else 0.0

            display_name = region_names.get(region, region)

            region_summary.append((display_name, matched, total, pct))

        region_summary.sort(key=lambda r: r[3], reverse=True)


        systems_html = os.path.join(OUTPUT_DIR, f"{user_id}_systems.html")
        regions_html = os.path.join(OUTPUT_DIR, f"{user_id}_regions.html")

        write_html_report(
            title=f"{user_id} – Highway System Completion",
            label="System",
            summary=system_summary,
            html_out=systems_html
        )

        write_html_report(
            title=f"{user_id} – State Completion",
            label="State",
            summary=region_summary,
            html_out=regions_html,
            link_map=region_link_map
        )

        # Console summary
        print(f"\nUser: {user_id}")
        print("Systems:")
        print(tabulate(
            [(s, m, t, f"{p:.2f}%") for s, m, t, p in system_summary],
            headers=["System", "Matched", "Total", "Completion"],
            tablefmt="github"
        ))
        print("Regions:")
        print(tabulate(
            [(r, m, t, f"{p:.2f}%") for r, m, t, p in region_summary],
            headers=["State", "Matched", "Total", "Completion"],
            tablefmt="github"
        ))

        print(f"📄 {systems_html}")
        print(f"📄 {regions_html}")


if __name__ == "__main__":
    validate_all()

import os
import csv
import re

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
# Helpers
# --------------------------------------------------

def natural_key(text):
    """
    Human-friendly sorting:
    I-2 < I-10 < I-100
    """
    return [
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", text)
    ]

# --------------------------------------------------
# Parse .list file
# --------------------------------------------------

def parse_list_file(path):
    """
    Returns:
      (region, route) -> url | None
    """
    entries = {}

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

            entries[(region, route)] = url

    return entries

# --------------------------------------------------
# Load routes from a system CSV
# --------------------------------------------------

def load_system_routes(system_csv, system_tier):
    """
    Returns:
      list of (tier, region, route)
    """
    routes = []

    with open(system_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)

        for row in reader:
            if len(row) < 3:
                continue

            region = row[1].strip()
            route = row[2].strip()
            routes.append((system_tier, region, route))

    return routes
    
def load_routes_by_state(system_csv):
    """
    Returns:
      region -> set(route)
    """
    routes = {}

    with open(system_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)

        for row in reader:
            if len(row) < 3:
                continue

            region = row[1].strip()
            route = row[2].strip()
            routes.setdefault(region, set()).add(route)

    return routes

def load_system_tiers():
    """
    Returns:
      system_code -> tier (int)
    """
    tiers = {}

    with open(SYSTEMS_INDEX, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)

        for row in reader:
            if len(row) < 4:
                continue

            system_code = row[0].strip()
            try:
                tier = int(row[3])
            except ValueError:
                tier = 999  # fallback

            tiers[system_code] = tier

    return tiers
    
# --------------------------------------------------
# HTML writers
# --------------------------------------------------

BASE_STYLE = """
<style>
@font-face {
  font-family: "ModeNine";
  src: url("../fonts/ModeNine-Regular.woff2") format("woff2"),
       url("../fonts/ModeNine-Regular.woff") format("woff");
}

body {
  font-family: "ModeNine", Arial, sans-serif;
}

table {
  border-collapse: collapse;
  width: 50%;
  table-layout: fixed;
}

th, td {
  border: 1px solid #ccc;
  padding: 6px 8px;
}

th {
  background: #eee;
}

tr.yes {
  background-color: #97ff79;
}

tr.no {
  background-color: #ff5555;
}

td.status {
  text-align: center;
  font-weight: bold;
}
</style>
"""

def write_system_page(user, system_name, routes, listed_routes, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{user} – {system_name}</title>
{BASE_STYLE}
</head>
<body>

<h1>{system_name}</h1>
<h3>User: {user}</h3>

<table>
<tr>
  <th>Route</th>
  <th>Status</th>
  <th>Proof</th>
</tr>
""")

        for tier, region, route in sorted(
            routes,
            key=lambda r: (r[0], r[1], natural_key(r[2]))
        ):
            key = (region, route)
            url = listed_routes.get(key)

            if key in listed_routes:
                row_class = "yes"
                status = "YES"
                proof = f"<a href='{url}'>link</a>" if url else ""
            else:
                row_class = "no"
                status = "NO"
                proof = ""

            f.write(
                f"<tr class='{row_class}'>"
                f"<td>{region} {route}</td>"
                f"<td class='status'>{status}</td>"
                f"<td>{proof}</td>"
                "</tr>\n"
            )

        f.write("""
</table>
</body>
</html>
""")

def write_state_page(user, state, routes, listed_routes, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{user} – {state}</title>
{BASE_STYLE}
</head>
<body>

<h1>{state}</h1>
<h3>User: {user}</h3>

<table>
<tr>
  <th>Route</th>
  <th>Status</th>
  <th>Proof</th>
</tr>
""")

        for route in sorted(routes, key=natural_key):
            key = (state, route)
            url = listed_routes.get(key)

            if key in listed_routes:
                row_class = "yes"
                status = "YES"
                proof = f"<a href='{url}'>link</a>" if url else ""
            else:
                row_class = "no"
                status = "NO"
                proof = ""

            f.write(
                f"<tr class='{row_class}'>"
                f"<td>{route}</td>"
                f"<td class='status'>{status}</td>"
                f"<td>{proof}</td>"
                "</tr>\n"
            )

        f.write("""
</table>
</body>
</html>
""")

# --------------------------------------------------
# Main generator
# --------------------------------------------------

def generate_pages():
    for list_file in sorted(os.listdir(LIST_DIR)):
        if not list_file.endswith(".list"):
            continue

        system_tiers = load_system_tiers()

        user = os.path.splitext(list_file)[0]
        list_path = os.path.join(LIST_DIR, list_file)
        listed_routes = parse_list_file(list_path)

        user_out = os.path.join(OUTPUT_DIR, user)
        systems_out = os.path.join(user_out, "systems")
        states_out = os.path.join(user_out, "states")

        os.makedirs(systems_out, exist_ok=True)
        os.makedirs(states_out, exist_ok=True)

        # ---------------- Systems ----------------

        state_aggregate = {}

        for system_csv in sorted(os.listdir(SYSTEMS_DIR)):
            if not system_csv.endswith(".csv"):
                continue

            system_name = system_csv.replace(".csv", "")
            system_path = os.path.join(SYSTEMS_DIR, system_csv)

            system_code = system_csv.replace(".csv", "")
            tier = system_tiers.get(system_code, 999)

            routes = load_system_routes(system_path, tier)
            out_html = os.path.join(systems_out, f"{system_name}.html")

            write_system_page(
                user=user,
                system_name=system_name,
                routes=routes,
                listed_routes=listed_routes,
                out_path=out_html
            )

            print(f"📄 {out_html}")

            # Aggregate by state
            by_state = load_routes_by_state(system_path)
            for state, rts in by_state.items():
                state_aggregate.setdefault(state, set()).update(rts)

        # ---------------- States ----------------

        for state, routes in sorted(state_aggregate.items()):
            out_html = os.path.join(states_out, f"{state}.html")
            write_state_page(
                user=user,
                state=state,
                routes=routes,
                listed_routes=listed_routes,
                out_path=out_html
            )

            print(f"📄 {out_html}")

# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    generate_pages()

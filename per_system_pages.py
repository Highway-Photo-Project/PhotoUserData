import os
import csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_DIR = os.path.join(BASE_DIR, "list_files")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------
# Parse list file with optional URL
# --------------------------------------------------

def parse_list_file(path):
    entries = {}

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split(maxsplit=2)
            if len(parts) < 2:
                continue

            region, route = parts[0], parts[1]
            url = parts[2] if len(parts) > 2 else None

            entries[(region, route)] = url

    return entries

# --------------------------------------------------
# Load routes for a single system
# --------------------------------------------------

def load_system_routes(system_csv):
    routes = []

    with open(system_csv, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader, None)

        for row in reader:
            if len(row) < 3:
                continue

            region = row[1].strip()
            route = row[2].strip()
            routes.append((region, route))

    return routes

# --------------------------------------------------
# HTML writer
# --------------------------------------------------

def write_system_page(user, system_name, routes, listed_routes, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{user} – {system_name}</title>

<style>
body {{
  font-family: Arial, sans-serif;
}}

table {{
  border-collapse: collapse;
  width: 100%;
  table-layout: fixed;
}}

th, td {{
  border: 1px solid #ccc;
  padding: 6px 8px;
}}

th {{
  background: #eee;
}}

.status {{
  text-align: center;
  font-weight: bold;
}}

.yes {{
  color: #0a0;
}}

.no {{
  color: #a00;
}}
</style>
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

        for region, route in sorted(routes):
            key = (region, route)
            url = listed_routes.get(key)

            if key in listed_routes:
                status = "<span class='status yes'>🟩</span>"
                proof = f"<a href='{url}'>link</a>" if url else ""
            else:
                status = "<span class='status no'>🟥</span>"
                proof = ""

            f.write(
                "<tr>"
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

# --------------------------------------------------
# Main generator
# --------------------------------------------------

def generate_per_system_pages():
    for list_file in os.listdir(LIST_DIR):
        if not list_file.endswith(".list"):
            continue

        user = os.path.splitext(list_file)[0]
        list_path = os.path.join(LIST_DIR, list_file)
        listed_routes = parse_list_file(list_path)

        user_out = os.path.join(OUTPUT_DIR, user)
        os.makedirs(user_out, exist_ok=True)

        for system_csv in os.listdir(SYSTEMS_DIR):
            if not system_csv.endswith(".csv"):
                continue

            system_name = system_csv.replace(".csv", "")
            system_path = os.path.join(SYSTEMS_DIR, system_csv)

            routes = load_system_routes(system_path)

            out_html = os.path.join(user_out, f"{system_name}.html")
            write_system_page(user, system_name, routes, listed_routes, out_html)

            print(f"📄 {out_html}")

if __name__ == "__main__":
    generate_per_system_pages()

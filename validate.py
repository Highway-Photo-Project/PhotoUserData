import os
import csv
from tabulate import tabulate

# ----------------------------
# Paths
# ----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_DIR = os.path.join(BASE_DIR, "list_files")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
USERS_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "users")

SYSTEMS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_systems")
REGIONS_DIR = os.path.join(BASE_DIR, "..", "PhotoData", "_regions")
SYSTEMS_INDEX = os.path.join(BASE_DIR, "..", "PhotoData", "systems.csv")
REGIONS_INDEX = os.path.join(BASE_DIR, "..", "PhotoData", "regions.csv")

os.makedirs(USERS_OUTPUT_DIR, exist_ok=True)

# ----------------------------
# Loaders
# ----------------------------

def load_systems():
    systems = {}
    system_routes = {}

    for fn in os.listdir(SYSTEMS_DIR):
        if not fn.endswith(".csv"):
            continue

        system_routes[fn] = set()
        with open(os.path.join(SYSTEMS_DIR, fn), encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)
            for row in reader:
                if len(row) < 3:
                    continue
                region, route = row[1].strip(), row[2].strip()
                systems[(region, route)] = fn
                system_routes[fn].add(route)

    return systems, system_routes


def load_regions():
    region_routes = {}
    for fn in os.listdir(REGIONS_DIR):
        if not fn.endswith(".csv"):
            continue

        region = os.path.splitext(fn)[0]
        region_routes[region] = set()

        with open(os.path.join(REGIONS_DIR, fn), encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)
            for row in reader:
                if len(row) >= 3:
                    region_routes[region].add(row[2].strip())

    return region_routes


def load_name_map(path, code_keys, name_keys):
    out = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        headers = {h.lower(): h for h in reader.fieldnames}

        code_col = next((headers[k] for k in code_keys if k in headers), None)
        name_col = next((headers[k] for k in name_keys if k in headers), None)

        if not code_col or not name_col:
            raise RuntimeError(f"Bad headers in {path}")

        for row in reader:
            out[row[code_col].strip()] = row[name_col].strip()

    return out


def parse_list_file(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=2)
            if len(parts) >= 2:
                entries.append((parts[0], parts[1]))
    return entries


# ----------------------------
# HTML helpers
# ----------------------------

def completion_color(pct):
    pct = max(0, min(100, pct))
    hue = pct * 240 / 100
    return f"hsl({hue:.1f}, 80%, 80%)"


def write_page_start(f, title):
    f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: Arial, sans-serif; }}
table {{
  border-collapse: collapse;
  margin: 0 auto;
  width: 60%;
}}
th, td {{
  border: 1px solid #ccc;
  padding: 6px 8px;
}}
th {{ background: #eee; }}
td.num {{ text-align: right; }}
</style>
</head>
<body>
<h1 style="text-align:center;">{title}</h1>
""")


def write_table(f, heading, rows, link_map=None):
    f.write(f"<h2 style='text-align:center;'>{heading}</h2>\n")
    f.write("<table><tr><th>Name</th><th>Caught</th><th>Total</th><th>%</th></tr>\n")

    for name, m, t, pct in rows:
        color = completion_color(pct)
        cell = f"<a href='{link_map[name]}'>{name}</a>" if link_map and name in link_map else name
        f.write(
            f"<tr><td>{cell}</td>"
            f"<td class='num'>{m}</td>"
            f"<td class='num'>{t}</td>"
            f"<td class='num' style='background:{color}'>{pct:.2f}%</td></tr>\n"
        )

    f.write("</table>\n")


def write_page_end(f):
    f.write("</body></html>")


# ----------------------------
# Main logic
# ----------------------------

def validate_all():
    systems, system_routes = load_systems()
    region_routes = load_regions()
    system_names = load_name_map(SYSTEMS_INDEX, ["system", "code"], ["name"])
    region_names = load_name_map(REGIONS_INDEX, ["region", "code"], ["name", "state"])

    leaderboard = []

    for fn in sorted(os.listdir(LIST_DIR)):
        if not fn.endswith(".list"):
            continue

        user = os.path.splitext(fn)[0]
        entries = parse_list_file(os.path.join(LIST_DIR, fn))

        # ---- system stats ----
        matched_sys = {}
        for r, route in entries:
            key = (r, route)
            if key in systems:
                matched_sys.setdefault(systems[key], set()).add(route)

        system_summary = []
        for sysfile, routes in system_routes.items():
            total = len(routes)
            matched = len(matched_sys.get(sysfile, set()))
            pct = matched / total * 100 if total else 0
            name = system_names.get(sysfile.replace(".csv", ""), sysfile)
            system_summary.append((name, matched, total, pct))

        system_summary.sort(key=lambda x: x[3], reverse=True)

        # ---- region stats ----
        matched_reg = {}
        for r, route in entries:
            if r in region_routes and route in region_routes[r]:
                matched_reg.setdefault(r, set()).add(route)

        region_summary = []
        for r, routes in region_routes.items():
            total = len(routes)
            matched = len(matched_reg.get(r, set()))
            pct = matched / total * 100 if total else 0
            region_summary.append((region_names.get(r, r), matched, total, pct))

        region_summary.sort(key=lambda x: x[3], reverse=True)

        # ---- output ----
        user_dir = os.path.join(USERS_OUTPUT_DIR, user)
        os.makedirs(user_dir, exist_ok=True)

        with open(os.path.join(user_dir, "regions.html"), "w", encoding="utf-8") as f:
            write_page_start(f, f"{user} – State Completion")
            write_table(f, "States", region_summary)
            write_table(f, "System Breakdown", system_summary)
            write_page_end(f)

        with open(os.path.join(user_dir, "systems.html"), "w", encoding="utf-8") as f:
            write_page_start(f, f"{user} – System Completion")
            write_table(f, "Systems", system_summary)
            write_page_end(f)

        total_m = sum(m for _, m, _, _ in system_summary)
        total_t = sum(t for _, _, t, _ in system_summary)
        pct = total_m / total_t * 100 if total_t else 0
        leaderboard.append((user, total_m, total_t, pct))

        print(tabulate(system_summary, headers=["System", "M", "T", "%"]))

    # ---- leaderboard ----
    leaderboard.sort(key=lambda x: x[3], reverse=True)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        write_page_start(f, "Leaderboard")
        write_table(
            f,
            "Overall Completion",
            leaderboard,
            link_map={u: f"./users/{u}/regions.html" for u, *_ in leaderboard}
        )
        write_page_end(f)


if __name__ == "__main__":
    validate_all()

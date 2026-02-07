import os
import csv
import re

BASE = "PhotoData/_counties"

route_re = re.compile(r"(\d+)")

def extract_route_number(route_code):
    """
    Extract numeric route number from strings like:
    AK1, AK11, AK98 -> 1, 11, 98
    """
    match = route_re.search(route_code)
    return int(match.group(1)) if match else None

def analyze_counties(base_folder):
    results = {}

    for state in os.listdir(base_folder):
        state_path = os.path.join(base_folder, state)
        if not os.path.isdir(state_path):
            continue

        for csv_file in os.listdir(state_path):
            if not csv_file.lower().endswith(".csv"):
                continue

            csv_path = os.path.join(state_path, csv_file)

            with open(csv_path, encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=";")
                for row in reader:
                    if len(row) < 3:
                        continue

                    state_code = row[0].strip()
                    route_code = row[1].strip()
                    county_name = row[2].strip()

                    route_num = extract_route_number(route_code)
                    if route_num is None:
                        continue

                    key = f"{state_code}/{county_name}"

                    if key not in results:
                        results[key] = {
                            "lowest": route_num,
                            "highest": route_num
                        }
                    else:
                        results[key]["lowest"] = min(results[key]["lowest"], route_num)
                        results[key]["highest"] = max(results[key]["highest"], route_num)

    return results

if __name__ == "__main__":
    summary = analyze_counties(BASE)

    for county, data in sorted(summary.items()):
        print(f"{county}: Lowest = {data['lowest']}, Highest = {data['highest']}")

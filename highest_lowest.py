import os
import csv

# Path to the cloned repo on your machine
BASE = "PhotoData/_counties"  # adjust this if your local path differs

def get_route_numbers_from_csv(csv_path):
    """Return list of route numbers from the CSV file."""
    nums = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # adjust 'route' below if your CSV uses a different column name
        for row in reader:
            route = row.get("route") or row.get("Route") or row.get("RouteNumber")
            if route:
                try:
                    nums.append(int(route))
                except ValueError:
                    pass
    return nums

def analyze_counties(base_folder):
    results = {}
    for county in os.listdir(base_folder):
        county_folder = os.path.join(base_folder, county)
        if not os.path.isdir(county_folder):
            continue

        all_routes = []
        for file in os.listdir(county_folder):
            if file.lower().endswith(".csv"):
                full_path = os.path.join(county_folder, file)
                all_routes.extend(get_route_numbers_from_csv(full_path))

        if all_routes:
            results[county] = {
                "lowest": min(all_routes),
                "highest": max(all_routes)
            }

    return results

if __name__ == "__main__":
    summary = analyze_counties(BASE)
    for county, data in summary.items():
        print(f"{county} - Lowest: {data['lowest']}, Highest: {data['highest']}")

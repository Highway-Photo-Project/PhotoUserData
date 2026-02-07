import os
import re

# path to your cloned repo
BASE_PATH = "PhotoData/_counties"

# regex to find numbers in file names
number_pattern = re.compile(r"\d+")

def find_route_numbers(file_name):
    # find all numbers, convert to int
    return [int(x) for x in number_pattern.findall(file_name)]

def process_counties():
    # dict: county -> list of route numbers
    county_routes = {}

    for county in os.listdir(BASE_PATH):
        county_path = os.path.join(BASE_PATH, county)
        if os.path.isdir(county_path):
            all_numbers = []
            for fname in os.listdir(county_path):
                nums = find_route_numbers(fname)
                all_numbers.extend(nums)
            if all_numbers:
                county_routes[county] = {
                    "min": min(all_numbers),
                    "max": max(all_numbers)
                }

    return county_routes

if __name__ == "__main__":
    results = process_counties()
    for county, info in results.items():
        print(f"{county}: lowest = {info['min']}, highest = {info['max']}")

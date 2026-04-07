import csv
import io
import json
import sys
import zipfile
from pathlib import Path


def extract_nodes(zip_path: Path, target_file: str, save_to: Path, remake: bool):
    data = []
    try:
        with zipfile.ZipFile(zip_path, "r") as csv_list:
            if target_file + ".csv" not in csv_list.namelist():
                print(f"Error: {target_file} not found in {zip_path}, incorrect filename or not in the zip file.")
                sys.exit(1)
            elif (save_to / (target_file + ".json")).is_file() and not remake:
                print(f"Error: {target_file} already extracted.")
                sys.exit(1)
            else:
                with csv_list.open(target_file + ".csv", "r") as csv_file:
                    wrapped_text = io.TextIOWrapper(csv_file, encoding="utf-8")
                    reader = csv.DictReader(wrapped_text)

                    for row in reader:
                        data.append(row)
                with open(save_to / (target_file + ".json"), "w", encoding="utf-8") as json_file:
                    json.dump(data, json_file, indent=4)
                print(f"Success: {target_file}.json saved to ./{save_to}")

    except FileNotFoundError:
        print(f"Error: The file {zip_path} does not exist.")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python extract.py <zip_file_path> <csv_filename> <output_directory> <remake_flag>\n")
        sys.exit(1)

    zip_file_path = Path(sys.argv[1])
    csv_filename = sys.argv[2]
    output_directory = Path(sys.argv[3])
    remake_flag = sys.argv[4] == "True"

    extract_nodes(zip_file_path, csv_filename, output_directory, remake_flag)

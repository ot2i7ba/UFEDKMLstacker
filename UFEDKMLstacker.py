# UFEDKMLstacker.py
# Copyright (c) 2024 ot2i7ba
# https://github.com/ot2i7ba/
# This code is licensed under the MIT License (see LICENSE for details).

"""
Stack (merge) multiple KML files to generate a combined interactive map using Plotly.
"""

# Standard Libraries
import hashlib
import logging
from logging.handlers import RotatingFileHandler
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

# Third-party Libraries
import pandas as pd
import plotly.express as px
from lxml import etree
import arrow

# Determine the base path based on whether the script is frozen (compiled) or running as a script
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Global Constants
LOG_FILE = os.path.join(base_path, 'UFEDKMLstacker.log')
MERGED_KML_FILE = os.path.join(base_path, 'Merged_Colored.kml')
MAP_HEIGHT = 1080
MAP_WIDTH = 1920
MAX_KML_FILES = 10  # Maximum number of KML files that can be merged

def configure_logging():
    """
    Configure logging to log to both the console and a file with rotation.
    The console will only show WARNING level and above, while the log file will capture DEBUG level and above.
    """
    log_file_path = os.path.join(base_path, 'UFEDKMLstacker.log')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Show only WARNING level and above in console

    file_handler = RotatingFileHandler(log_file_path, maxBytes=15*1024*1024, backupCount=3)
    file_handler.setLevel(logging.DEBUG)  # Log DEBUG level and above to file

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
    logging.info("Logging configured successfully with rotation.")

def clear_screen():
    """Clears the terminal screen based on the operating system."""
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)

def print_blank_line():
    """Prints a blank line for formatting purposes."""
    print("\n")

def print_header():
    """Prints the script header for the main menu display."""
    print(" UFEDKMLstacker v0.0.2 by ot2i7ba ")
    print("==================================")
    print_blank_line()

def display_countdown(seconds):
    """
    Displays a countdown timer in the console.

    Args:
        seconds (int): The number of seconds to count down from.
    """
    print_blank_line()
    for remaining in range(seconds, 0, -1):
        print(f"\rReturning to main menu in {remaining} seconds...", end="")
        time.sleep(1)
    print("\rReturning to main menu...                     ")

def clean_html_tags(text):
    """
    Removes HTML tags from a string.

    Args:
        text (str): The string from which to remove HTML tags.

    Returns:
        str: The cleaned string without HTML tags.
    """
    if text is None:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def validate_file_path(file_path):
    """
    Validates that the given file path is within the allowed directory
    and is not a symbolic link.

    Args:
        file_path (str): The file path to validate.

    Returns:
        bool: True if the file path is valid, False otherwise.
    """
    base_dir = os.path.abspath(base_path)
    full_path = os.path.abspath(file_path)

    # Check if the path is a symbolic link
    if os.path.islink(full_path):
        logging.warning(f"Symbolic link detected: {full_path}")
        return False

    # Check if the path is within the allowed directory
    if os.path.commonpath([base_dir, full_path]) == base_dir:
        return True
    else:
        logging.warning(f"Unauthorized file path: {full_path}")
        return False

def validate_selection(selection, kml_files):
    """
    Validates user selection for merging KML files using regex.

    Args:
        selection (str): The user input selection string.
        kml_files (list): List of available KML files.

    Returns:
        list or None: List of selected files if valid, None otherwise.
    """
    if not re.match(r'^[\d,\s]+$', selection):
        print("Invalid format. Please enter numbers separated by commas.")
        return None

    try:
        selected_files = []
        for i in selection.split(','):
            num = int(i.strip())
            if num < 1 or num > len(kml_files):
                print(f"Number {num} is out of the valid range.")
                return None
            selected_files.append(kml_files[num - 1])

        if len(selected_files) > MAX_KML_FILES:
            print(f"Only up to {MAX_KML_FILES} KML files can be selected. You have selected {len(selected_files)}.")
            logging.warning("More than the allowed number of files selected.")
            return None

        if len(selected_files) < 2:
            print("At least two KML files must be selected.")
            logging.info("Not enough files selected for merging.")
            display_countdown(3)
            return None
        return selected_files
    except ValueError as e:
        print("Invalid input, please try again.")
        logging.error(f"ValueError in validate_selection: {e}")
        return None

def kml_file_info(file_path):
    """
    Returns the number of Placemarks in a KML file.

    Args:
        file_path (str): Path to the KML file.

    Returns:
        int: Number of Placemarks found in the KML file.
    """
    try:
        tree = etree.parse(file_path)
        placemarks = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
        return len(placemarks)
    except (etree.XMLSyntaxError, OSError) as e:
        logging.error(f"Error reading {file_path}: {e}")
        return 0

def list_kml_files():
    """
    Lists all KML files in the current directory with basic info,
    excluding the merged KML file.

    Returns:
        list: List of available KML file names.
    """
    clear_screen()
    print_header()

    merged_kml_path = os.path.abspath(MERGED_KML_FILE)

    kml_files = [
        f for f in os.listdir(base_path) 
        if f.endswith('.kml') and os.path.abspath(os.path.join(base_path, f)) != merged_kml_path
    ]

    if not kml_files:
        logging.info("No KML files found in the current directory.")
        print("No KML files found in the current directory.")
        exit(0)
    
    print("Available KML files:")
    unique_files = set()
    for idx, kml in enumerate(kml_files, 1):
        if kml not in unique_files:
            placemark_count = kml_file_info(os.path.join(base_path, kml))
            print(f"{idx}. {kml:<30}\tPlacemarks: {placemark_count}")
            unique_files.add(kml)
    print("e. Exit")
    print_blank_line()
    
    return kml_files

def select_kml_files(kml_files):
    """
    Prompts the user to select KML files for merging with additional validation.

    Args:
        kml_files (list): List of available KML file names.

    Returns:
        list: List of selected KML files for merging.
    """
    while True:
        selections = input("Enter file numbers to merge (e.g., 1, 2, 5) or 'e' to exit: ").strip().lower()
        if selections == 'e':
            print("Exiting the script. Goodbye!")
            logging.info("User chose to exit the script.")
            sys.exit(0)
        if not selections:
            logging.info("No specific files selected, automatically selecting up to 10 files.")
            # Automatically select the first 10 files if more are available
            if len(kml_files) > MAX_KML_FILES:
                print(f"Only the first {MAX_KML_FILES} files will be used for merging.")
                kml_files = kml_files[:MAX_KML_FILES]
            return kml_files
        selected_files = validate_selection(selections, kml_files)
        if selected_files:
            valid_files = [file for file in selected_files if os.path.exists(os.path.join(base_path, file)) and validate_file_path(file)]
            if len(valid_files) < len(selected_files):
                print("One or more selected files are invalid or do not exist. Please try again.")
                logging.warning("Invalid file paths detected in user selection.")
                continue
            logging.info(f"{len(valid_files)} valid files selected for merging.")
            return valid_files

def check_existing_merged_file():
    """
    Checks if the merged KML file already exists and prompts the user for action.

    Returns:
        bool: True if the user wants to overwrite the existing file, False otherwise.
    """
    if os.path.exists(MERGED_KML_FILE):
        print_blank_line()
        print(f"The file '{MERGED_KML_FILE}' already exists.")
        choice = input("Do you want to overwrite it? (Enter for yes / n for no): ").strip().lower()
        if choice == 'n':
            print("File will not be overwritten.")
            logging.info("User chose not to overwrite the existing merged KML file.")
            display_countdown(3)
            return False
        else:
            logging.info("User chose to overwrite the existing merged KML file.")
            return True
    return True

def assign_colors_to_files(files):
    """
    Assigns colors to selected files and writes the mapping to a text file.

    Args:
        files (list): List of selected KML file names.

    Returns:
        dict: Dictionary mapping file names to color codes.
    """
    COLORS = {
        "red": "#FF0000", "blue": "#0000FF", "yellow": "#FFFF00", 
        "green": "#00FF00", "orange": "#FFA500", "violet": "#EE82EE", 
        "pink": "#FFC0CB", "purple": "#800080", "turquoise": "#40E0D0", "cyan": "#00FFFF"
    }
    color_map = {files[i]: list(COLORS.values())[i] for i in range(len(files))}
    color_name_map = {v: k for k, v in COLORS.items()}
    
    color_mapping_file = os.path.join(base_path, "color_mapping.txt")
    with open(color_mapping_file, 'w') as f:
        for file, color in color_map.items():
            color_name = color_name_map.get(color, "Unknown")
            f.write(f"{file} = {color} ({color_name})\n")
    
    logging.info(f"Color mapping created at {color_mapping_file}.")
    return color_map

def get_remarks(files):
    """
    Prompts the user to enter a remark for each file. A remark must be defined.

    Args:
        files (list): List of selected KML file names.

    Returns:
        dict: Dictionary mapping file names to user remarks.
    """
    remarks = {}
    print_blank_line()
    for file in files:
        while True:
            remark = input(f"Enter a remark for the file {file}: ").strip()
            if remark:
                remarks[file] = remark
                break
            else:
                print("Remark cannot be empty. Please enter a valid remark.")
                logging.warning(f"Empty remark entered for file {file}. Prompting again.")
    logging.info(f"Remarks for files: {remarks}")
    return remarks

def define_styles(document, color_map):
    """
    Defines styles in the KML document based on the assigned colors.

    Args:
        document (etree.Element): The KML Document element to append styles to.
        color_map (dict): Dictionary mapping file names to color codes.
    """
    for file, color in color_map.items():
        style = etree.SubElement(document, 'Style', id=file)
        icon_style = etree.SubElement(style, 'IconStyle')
        color_element = etree.SubElement(icon_style, 'color')
        color_element.text = color.replace("#", "ff")
        icon = etree.SubElement(icon_style, 'Icon')
        href = etree.SubElement(icon, 'href')
        href.text = "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png"

def parse_timestamp(timestamp_str):
    """
    Parses a timestamp string into a datetime object using arrow and fallback regex.

    Args:
        timestamp_str (str): The timestamp string in various formats.

    Returns:
        datetime or None: The parsed datetime object or None if parsing fails.
    """
    if not timestamp_str:
        logging.debug("Timestamp string is empty or None.")
        return None

    try:
        dt = arrow.get(timestamp_str).datetime
        logging.debug(f"Parsed timestamp using arrow: {dt}")
        return dt
    except (arrow.parser.ParserError, ValueError) as e:
        logging.error(f"Arrow failed to parse {timestamp_str}: {e}")

    regex_patterns = [
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}\+\d{2}:\d{2}$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+\d{2}:\d{2}$',
        r'^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}:\d{2}\(UTC\+\d{1,2}\)$',
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3,6}\+\d{2}:\d{2}$'
    ]

    for pattern in regex_patterns:
        match = re.match(pattern, timestamp_str)
        if match:
            try:
                dt = datetime.fromisoformat(timestamp_str)
                logging.debug(f"Parsed timestamp using custom regex pattern {pattern}: {dt}")
                return dt
            except ValueError as e:
                logging.error(f"Failed to parse {timestamp_str} with pattern {pattern}: {e}")

    logging.error(f"Failed to parse timestamp: {timestamp_str} - No matching pattern found.")
    return None

def extract_file_metadata(file_path):
    """
    Extracts metadata such as file creation and modification times.

    Args:
        file_path (str): Path to the file.

    Returns:
        dict: A dictionary containing metadata about the file.
    """
    try:
        metadata = {
            "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "file_size": os.path.getsize(file_path),
            "sha256": calculate_file_hash(file_path)
        }
        logging.info(f"Metadata for {file_path}: {metadata}")
        return metadata
    except OSError as e:
        logging.error(f"Error retrieving metadata for {file_path}: {e}")
        return {}

def calculate_file_hash(file_path):
    """
    Calculates the SHA-256 hash of the given file.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: The SHA-256 hash of the file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_file_integrity(file_path: str, expected_hash: str) -> bool:
    """
    Verifies the integrity of a file by comparing its hash with the expected hash.

    Args:
        file_path (str): Path to the file.
        expected_hash (str): The expected SHA-256 hash of the file.

    Returns:
        bool: True if the file integrity is verified, False otherwise.
    """
    calculated_hash = calculate_file_hash(file_path)
    if calculated_hash == expected_hash:
        logging.info(f"File integrity verified for {file_path}.")
        return True
    else:
        logging.warning(f"File integrity check failed for {file_path}. Expected {expected_hash}, got {calculated_hash}.")
        return False

def process_kml_file(file_path, remark):
    """
    Processes a KML file, extracting geopoints, timestamps, and additional metadata.

    Args:
        file_path (str): Path to the KML file.
        remark (str): User-defined remark for the file.

    Returns:
        tuple: Total points, points with timestamps, and a list of valid points.
    """
    total_points = 0
    points_with_timestamps = 0
    valid_points = []

    try:
        for event, elem in etree.iterparse(file_path, events=('end',), tag='{http://www.opengis.net/kml/2.2}Placemark'):
            name = elem.findtext('{http://www.opengis.net/kml/2.2}name', default='')
            name = f"({remark}) - {name}"

            description = elem.findtext('{http://www.opengis.net/kml/2.2}description', default='')
            description_text = clean_html_tags(description)

            timestamp_elem = elem.find('{http://www.opengis.net/kml/2.2}TimeStamp')
            timestamp = None
            timestamp_source = None

            if timestamp_elem is not None:
                when = timestamp_elem.findtext('{http://www.opengis.net/kml/2.2}when')
                if when:
                    timestamp = parse_timestamp(when)
                    timestamp_source = "<TimeStamp>"

            if not timestamp:
                if 'UTC' in name:
                    timestamp = parse_timestamp(name)
                    timestamp_source = "<name>"
                elif 'UTC' in description_text:
                    timestamp = parse_timestamp(description_text)
                    timestamp_source = "<description>"

            if timestamp:
                points_with_timestamps += 1

            coordinates_elem = elem.find('.//{http://www.opengis.net/kml/2.2}coordinates')
            if coordinates_elem is not None:
                coords = coordinates_elem.text.strip().split(',')
                if len(coords) >= 2:
                    lon, lat = float(coords[0]), float(coords[1])
                    valid_points.append({
                        "lon": lon, "lat": lat, "timestamp": timestamp,
                        "name": name, "description": description_text
                    })
                    total_points += 1

            elem.clear()

            if timestamp_source:
                logging.info(f"Geopoint processed: Name='{name}', Timestamp='{timestamp}', Source='{timestamp_source}', Coordinates={coords}")
            else:
                logging.info(f"Geopoint processed: Name='{name}', No valid timestamp found, Coordinates={coords}")

    except etree.XMLSyntaxError as e:
        logging.error(f"XML Syntax Error in file {file_path}: {e}")
    except OSError as e:
        logging.error(f"OS Error in file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unhandled error in file {file_path}: {e}")

    logging.info(f"File {file_path} processed: {total_points} points found, {points_with_timestamps} with timestamps.")
    return total_points, points_with_timestamps, valid_points

def merge_kml_files(files, color_map, remarks, statistics):
    """
    Merges the colored KML files into one KML file and gathers statistics.

    Args:
        files (list): List of selected KML file names.
        color_map (dict): Dictionary mapping file names to color codes.
        remarks (dict): Dictionary mapping file names to user remarks.
        statistics (list): List to store statistics for each file.

    Returns:
        tuple: Merged KML file name and total valid points.
    """
    merged_root = etree.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = etree.SubElement(merged_root, 'Document')

    define_styles(document, color_map)

    total_valid_points = 0

    file_metadata = {file: extract_file_metadata(os.path.join(base_path, file)) for file in files}

    for file in files:
        total_points, points_with_timestamps, valid_points = process_kml_file(os.path.join(base_path, file), remarks[file])
        if validate_file_path(file):
            remark = remarks[file]
            color = color_map[file]
            total_valid_points += len(valid_points)

            statistics.append({
                "file": file,
                "total_points": total_points,
                "points_with_timestamps": points_with_timestamps,
                "valid_points": len(valid_points),
                "mapped_points": len(valid_points),
                "remark": remark,
                "color": color,
                **file_metadata[file]
            })

            for point in valid_points:
                placemark = etree.Element('Placemark')
                style_url = etree.SubElement(placemark, 'styleUrl')
                style_url.text = f"#{file}"
                point_elem = etree.SubElement(placemark, 'Point')
                coords_elem = etree.SubElement(point_elem, 'coordinates')
                coords_elem.text = f"{point['lon']},{point['lat']}"
                description = etree.SubElement(placemark, 'description')
                description.text = point["description"]
                timestamp_elem = etree.SubElement(placemark, 'TimeStamp')
                when_elem = etree.SubElement(timestamp_elem, 'when')
                if point["timestamp"]:
                    when_elem.text = point["timestamp"].isoformat()
                name_elem = etree.SubElement(placemark, 'name')
                name_elem.text = point["name"]
                document.append(placemark)

    with open(MERGED_KML_FILE, 'wb') as f:
        f.write(etree.tostring(merged_root, pretty_print=True))
    
    logging.info(f"Merged KML saved as {MERGED_KML_FILE}.")

    total_mapped_points = sum(stat["valid_points"] for stat in statistics)
    logging.info(f"Total points across all files: {sum(stat['total_points'] for stat in statistics)}")
    logging.info(f"Total valid points across all files: {total_valid_points}")
    logging.info(f"Total valid geopoints processed for visualization: {total_mapped_points}")

    return MERGED_KML_FILE, total_valid_points

def create_interactive_map(merged_kml, color_map, remarks):
    """
    Creates an interactive map with colored placemarks and remarks.

    Args:
        merged_kml (str): Name of the merged KML file.
        color_map (dict): Dictionary mapping file names to color codes.
        remarks (dict): Dictionary mapping file names to user remarks.
    """
    df = []
    tree = etree.parse(merged_kml)
    for placemark in tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        coord = placemark.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.strip()
        coord_parts = coord.split(',')
        lon, lat = map(float, coord_parts[:2])
        name = placemark.find('.//{http://www.opengis.net/kml/2.2}name').text
        description = placemark.find('.//{http://www.opengis.net/kml/2.2}description').text
        style_url = placemark.find('.//{http://www.opengis.net/kml/2.2}styleUrl').text.strip('#')
        color = color_map.get(style_url, 'gray')
        remark = remarks.get(style_url, 'No remark')
        df.append({
            "lat": lat, "lon": lon, "name": name, "color": color,
            "remark": remark, "description": description
        })
    
    fig = px.scatter_mapbox(
        df, lat="lat", lon="lon", hover_name="name", hover_data=["description", "remark"],
        color="remark", color_discrete_map={v: color_map[k] for k, v in remarks.items()},
        zoom=3, height=MAP_HEIGHT, width=MAP_WIDTH
    )
    fig.update_layout(mapbox_style="open-street-map")
    interactive_map_file = os.path.join(base_path, "interactive_map.html")
    fig.write_html(interactive_map_file)
    logging.info(f"Interactive map saved as {interactive_map_file}.")

def save_statistics_to_excel(statistics, total_valid_points, total_mapped_points):
    """
    Saves the gathered statistics to an Excel file.

    Args:
        statistics (list): List of statistics dictionaries for each KML file.
        total_valid_points (int): Total number of valid points processed.
        total_mapped_points (int): Total number of mapped points processed.
    """
    color_name_map = {
        "#FF0000": "Red", "#0000FF": "Blue", "#FFFF00": "Yellow",
        "#00FF00": "Green", "#FFA500": "Orange", "#EE82EE": "Violet",
        "#FFC0CB": "Pink", "#800080": "Purple", "#40E0D0": "Turquoise", "#00FFFF": "Cyan"
    }
    
    for stat in statistics:
        stat['color_name'] = color_name_map.get(stat['color'], "Unknown")

    df = pd.DataFrame(statistics)

    columns_order = ['file', 'total_points', 'points_with_timestamps', 'valid_points', 
                     'mapped_points', 'remark', 'color', 'color_name', 'creation_time', 
                     'modification_time', 'file_size', 'sha256']
    df = df[columns_order]
    
    excel_file = os.path.join(base_path, 'KML_Statistics.xlsx')
    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer, sheet_name='Summary', index=False)
        summary_data = {
            "Total Valid Points": [total_valid_points],
            "Total Mapped Points": [total_mapped_points]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Total Summary', index=False)
    
    logging.info(f"Statistics saved in {excel_file}.")
    print_blank_line()
    print(f"Statistics saved in {excel_file}.")

def save_statistics_to_csv(statistics: List[Dict[str, any]], filename: str = 'KML_Statistics.csv') -> None:
    """
    Saves the gathered statistics to a CSV file.

    Args:
        statistics (list): List of statistics dictionaries for each KML file.
        filename (str): The name of the CSV file to save the statistics to.
    """
    csv_file = os.path.join(base_path, filename)
    df = pd.DataFrame(statistics)
    df.to_csv(csv_file, index=False)
    logging.info(f"Statistics saved in {csv_file}.")
    print(f"Statistics saved in {csv_file}.")

def main_menu():
    """
    Displays the main menu and handles user selection.
    This function provides a user interface for selecting and merging KML files.
    """
    try:
        while True:
            clear_screen()
            print_header()

            kml_files = list_kml_files()
            selected_files = select_kml_files(kml_files)

            if not check_existing_merged_file():
                continue

            file_metadata = {file: extract_file_metadata(os.path.join(base_path, file)) for file in selected_files}

            for file in selected_files:
                expected_hash = file_metadata[file]["sha256"]
                if not verify_file_integrity(os.path.join(base_path, file), expected_hash):
                    print(f"File integrity check failed for {file}. Processing aborted.")
                    logging.error(f"File integrity check failed for {file}. Aborting.")
                    sys.exit(1)

            color_map = assign_colors_to_files(selected_files)
            remarks = get_remarks(selected_files)
            statistics = []
            merged_kml, total_valid_points = merge_kml_files(selected_files, color_map, remarks, statistics)

            total_mapped_points = sum(stat["valid_points"] for stat in statistics)

            create_interactive_map(merged_kml, color_map, remarks)
            
            save_statistics_to_excel(statistics, total_valid_points, total_mapped_points)
            save_statistics_to_csv(statistics)

            print_blank_line()
            print("Process completed successfully. Details are available in the log, Excel file, and CSV file.")
            display_countdown(3)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting gracefully...")
        logging.info("Process interrupted by user with CTRL+C. Exiting gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    configure_logging()
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting gracefully...")
        logging.info("Process interrupted by user with CTRL+C at main entry point. Exiting gracefully.")
        sys.exit(0)

# Copyright (c) 2024 ot2i7ba
# https://github.com/ot2i7ba/
# This code is licensed under the MIT License (see LICENSE for details).

"""
Merges multiple KML files to generate a combined interactive map using Plotly.
"""

# Standard Libraries
import os
import sys
import time
import logging
import re
import asyncio
import aiofiles
import hashlib
from datetime import datetime
from lxml import etree
from concurrent.futures import ThreadPoolExecutor

# Third-party Libraries
import pandas as pd
import plotly.express as px

# Global Constants
LOG_FILE = 'UFEDKMLstacker.log'
MAP_HEIGHT = 1080
MAP_WIDTH = 1920
MERGED_KML_FILE = 'Merged_Colored.kml'

# Configure logging
def configure_logging():
    """Configure logging to log to both console and file."""
    if not os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'w') as f:
                f.write("")
            print(f"Log file created: {LOG_FILE}")
        except IOError as e:
            print(f"Failed to create log file: {e}")
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only log INFO level and above to console
    
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)  # Log DEBUG level and above to file
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
    logging.info("Logging configured successfully")

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_blank_line():
    """Prints a blank line."""
    print("\n")

def print_header():
    """Prints the script header."""
    print(" UFEDKMLstacker v0.0.1 by ot2i7ba ")
    print("==================================")
    print_blank_line()

def display_countdown(seconds):
    """Displays a countdown timer."""
    print_blank_line()
    for remaining in range(seconds, 0, -1):
        print(f"\rReturning to main menu in {remaining} seconds...", end="")
        time.sleep(1)
    print("\rReturning to main menu...                     ")

def clean_html_tags(text):
    """Removes HTML tags from a string."""
    if text is None:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def validate_file_path(file_path):
    """Validates that the given file path is within the allowed directory."""
    base_dir = os.path.abspath('.')
    full_path = os.path.abspath(file_path)
    if os.path.commonpath([base_dir, full_path]) == base_dir:
        return True
    else:
        logging.warning(f"Unauthorized file path: {full_path}")
        return False

def validate_selection(selection, kml_files):
    """Validates user selection for merging KML files using regex."""
    if not re.match(r'^[\d,\s]+$', selection):
        print("Invalid selection format. Please enter numbers separated by commas.")
        return None
    
    try:
        selected_files = [kml_files[int(i.strip()) - 1] for i in selection.split(',')]
        if len(selected_files) < 2:
            print("At least two KML files are required to perform a merge. Please select more files.")
            logging.info("Not enough files selected for merging.")
            display_countdown(3)
            clear_screen()
            print_header()
            list_kml_files()
            return None
        return selected_files
    except (IndexError, ValueError):
        print("Invalid selection, please try again.")
        return None

def kml_file_info(file_path):
    """Returns the number of Placemarks in a KML file."""
    try:
        tree = etree.parse(file_path)
        placemarks = tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark')
        return len(placemarks)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
        return 0

def list_kml_files():
    """Lists all KML files in the current directory with basic info, excluding Merged_Colored.kml."""
    kml_files = [f for f in os.listdir('.') if f.endswith('.kml') and f != MERGED_KML_FILE]
    if not kml_files:
        logging.info("No KML files found in the current directory.")
        print("No KML files found in the current directory.")
        exit(0)
    
    print("Available KML files:")
    for idx, kml in enumerate(kml_files, 1):
        placemark_count = kml_file_info(kml)
        print(f"{idx}. {kml:<30}\tPlacemarks: {placemark_count}")
    print("e. Exit")
    print_blank_line()
    
    return kml_files

def select_kml_files(kml_files):
    """Prompts the user to select KML files for merging."""
    while True:
        selections = input("Enter file numbers to merge (e.g., 1, 2, 5) or 'e' to exit: ").strip().lower()
        if selections == 'e':
            print("Exiting the script. Goodbye!")
            logging.info("User chose to exit the script.")
            sys.exit(0)  # Use sys.exit instead of exit
        if not selections:
            logging.info("No specific files selected, merging all.")
            return kml_files
        selected_files = validate_selection(selections, kml_files)
        if selected_files:
            logging.info(f"{len(selected_files)} files selected for merging.")
            return selected_files

def check_existing_merged_file():
    """Checks if the merged KML file already exists and prompts the user for action."""
    if os.path.exists(MERGED_KML_FILE):
        print_blank_line()
        print(f"The file '{MERGED_KML_FILE}' already exists.")
        choice = input("Do you want to overwrite it? (Enter for yes / n for no): ").strip().lower()
        if choice == 'n':
            print("File will not be overwritten.")
            logging.info("User chose not to overwrite the existing merged KML file.")
            display_countdown(3)
            clear_screen()
            return False
        else:
            logging.info("User chose to overwrite the existing merged KML file.")
            return True
    return True

def assign_colors_to_files(files):
    """Assigns colors to selected files and writes the mapping to a text file."""
    COLORS = {
        "red": "#FF0000", "blue": "#0000FF", "yellow": "#FFFF00", 
        "green": "#00FF00", "orange": "#FFA500", "violet": "#EE82EE", 
        "pink": "#FFC0CB", "purple": "#800080", "turquoise": "#40E0D0", "cyan": "#00FFFF"
    }
    color_map = {files[i]: list(COLORS.values())[i] for i in range(len(files))}
    color_name_map = {v: k for k, v in COLORS.items()}  # Mapping from hex to color names
    
    with open("color_mapping.txt", 'w') as f:
        for file, color in color_map.items():
            color_name = color_name_map.get(color, "Unknown")  # Get the color name
            f.write(f"{file} = {color} ({color_name})\n")  # Write both hex and color name
    
    logging.info("Color mapping created.")
    return color_map

def get_remarks(files):
    """Prompts the user to enter a remark for each file."""
    remarks = {}
    print_blank_line()
    for file in files:
        remark = input(f"Enter a remark for the file {file}: ")
        remarks[file] = remark
    logging.info(f"Remarks for files: {remarks}")
    return remarks

def define_styles(document, color_map):
    """Defines styles in the KML document based on the assigned colors."""
    for file, color in color_map.items():
        style = etree.SubElement(document, 'Style', id=file)
        icon_style = etree.SubElement(style, 'IconStyle')
        color_element = etree.SubElement(icon_style, 'color')
        color_element.text = color.replace("#", "ff")  # Convert hex color to ARGB
        icon = etree.SubElement(icon_style, 'Icon')
        href = etree.SubElement(icon, 'href')
        href.text = "http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png"

def parse_timestamp(timestamp_str):
    """
    Parses a timestamp string into a datetime object.

    Args:
        timestamp_str (str): The timestamp string in ISO 8601 format.

    Returns:
        datetime or None: The parsed datetime object or None if parsing fails.
    """
    if timestamp_str is None:
        return None
    
    try:
        if "." in timestamp_str:
            # Handling millisecond precision in timestamps
            timestamp_str = timestamp_str.rstrip("Z")
            base_time, fractional = timestamp_str.split(".")
            fractional = fractional.ljust(6, '0')  # Pad to microseconds
            timestamp_str = f"{base_time}.{fractional}+00:00"
            return datetime.fromisoformat(timestamp_str)
        else:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError as e:
        logging.error(f"Invalid time format: {timestamp_str}, Error: {e}")
        return None

def extract_file_metadata(file_path):
    """Extracts metadata such as file creation and modification times."""
    try:
        metadata = {
            "creation_time": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
            "modification_time": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
            "file_size": os.path.getsize(file_path),
            "sha256": calculate_file_hash(file_path)  # Add hash value to metadata
        }
        logging.info(f"Metadata for {file_path}: {metadata}")
        return metadata
    except OSError as e:
        logging.error(f"Error retrieving metadata for {file_path}: {e}")
        return {}

def calculate_file_hash(file_path):
    """Calculates the SHA-256 hash of the given file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

async def process_kml_file_async(file_path, remark):
    """Asynchronously processes a KML file, extracting geopoints, timestamps, and additional metadata."""
    total_points = 0
    points_with_timestamps = 0
    valid_points = []

    try:
        tree = etree.parse(file_path)  # Parse the entire file
        for elem in tree.iterfind('.//{http://www.opengis.net/kml/2.2}Placemark'):
            name = elem.findtext('{http://www.opengis.net/kml/2.2}name', default='')
            name = f"({remark}) - {name}"

            description = elem.findtext('{http://www.opengis.net/kml/2.2}description', default='')
            description_text = clean_html_tags(description)

            timestamp_elem = elem.find('{http://www.opengis.net/kml/2.2}TimeStamp')
            timestamp = None
            if timestamp_elem is not None:
                when = timestamp_elem.findtext('{http://www.opengis.net/kml/2.2}when')
                timestamp = parse_timestamp(when)
                if timestamp:
                    points_with_timestamps += 1

            coordinates_elem = elem.find('.//{http://www.opengis.net/kml/2.2}coordinates')
            if coordinates_elem is not None:
                coords = coordinates_elem.text.strip().split(',')
                if len(coords) >= 2:  # At least lon and lat
                    lon, lat = float(coords[0]), float(coords[1])
                    valid_points.append({
                        "lon": lon, "lat": lat, "timestamp": timestamp,
                        "name": name, "description": description_text
                    })
                    total_points += 1
            elem.clear()  # Free memory by clearing the processed element
            logging.debug(f"Processed element with name: {name}, timestamp: {timestamp}, coordinates: {coords}")

    except etree.XMLSyntaxError as e:
        logging.error(f"XML Syntax Error in file {file_path}: {e}")
    except OSError as e:
        logging.error(f"OS Error in file {file_path}: {e}")
    except Exception as e:
        logging.error(f"Unhandled error in file {file_path}: {e}")

    logging.info(f"File {file_path} processed: {total_points} points found, {points_with_timestamps} with timestamps.")
    return total_points, points_with_timestamps, valid_points

async def process_kml_files_in_parallel(files, remarks):
    """Processes multiple KML files in parallel using asyncio and process_kml_file_async."""
    tasks = [process_kml_file_async(file, remarks[file]) for file in files]
    return await asyncio.gather(*tasks)

async def merge_kml_files(files, color_map, remarks, statistics):
    """Merges the colored KML files into one KML file and gathers statistics."""
    merged_root = etree.Element('kml', xmlns='http://www.opengis.net/kml/2.2')
    document = etree.SubElement(merged_root, 'Document')

    define_styles(document, color_map)

    total_valid_points = 0

    file_metadata = {file: extract_file_metadata(file) for file in files}

    processing_results = await process_kml_files_in_parallel(files, remarks)
    
    for file, (total_points, points_with_timestamps, valid_points) in zip(files, processing_results):
        if validate_file_path(file):
            remark = remarks[file]
            color = color_map[file]
            total_valid_points += len(valid_points)

            statistics.append({
                "file": file,
                "total_points": total_points,
                "points_with_timestamps": points_with_timestamps,
                "valid_points": len(valid_points),
                "remark": remark,
                "color": color,
                **file_metadata[file]  # Include file metadata
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

    async with aiofiles.open(MERGED_KML_FILE, 'wb') as f:
        await f.write(etree.tostring(merged_root, pretty_print=True))
    logging.info(f"Merged KML saved as {MERGED_KML_FILE}.")
    return MERGED_KML_FILE, total_valid_points

def create_interactive_map(merged_kml, color_map, remarks):
    """Creates an interactive map with colored placemarks and remarks."""
    df = []
    tree = etree.parse(merged_kml)
    for placemark in tree.findall('.//{http://www.opengis.net/kml/2.2}Placemark'):
        coord = placemark.find('.//{http://www.opengis.net/kml/2.2}coordinates').text.strip()
        coord_parts = coord.split(',')
        lon, lat = map(float, coord_parts[:2])  # Use only longitude and latitude
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
    fig.write_html("interactive_map.html")
    logging.info("Interactive map saved as interactive_map.html.")

def save_statistics_to_excel(statistics, total_valid_points):
    """Saves the gathered statistics to an Excel file."""
    color_name_map = {
        "#FF0000": "Red", "#0000FF": "Blue", "#FFFF00": "Yellow",
        "#00FF00": "Green", "#FFA500": "Orange", "#EE82EE": "Violet",
        "#FFC0CB": "Pink", "#800080": "Purple", "#40E0D0": "Turquoise", "#00FFFF": "Cyan"
    }
    
    for stat in statistics:
        stat['color_name'] = color_name_map.get(stat['color'], "Unknown")

    # Create the DataFrame
    df = pd.DataFrame(statistics)

    # Reorder the columns to have 'color_name' directly after 'color'
    columns_order = ['file', 'total_points', 'points_with_timestamps', 'valid_points', 
                     'remark', 'color', 'color_name', 'creation_time', 
                     'modification_time', 'file_size', 'sha256']
    df = df[columns_order]
    
    excel_file = 'KML_Statistics.xlsx'
    with pd.ExcelWriter(excel_file) as writer:
        df.to_excel(writer, sheet_name='Summary', index=False)
        summary_data = {
            "Total Valid Points": [total_valid_points],
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Total Summary', index=False)
    
    logging.info(f"Statistics saved in {excel_file}.")
    print(f"Statistics saved in {excel_file}.")

async def main_menu():
    """Displays the main menu and handles user selection."""
    try:
        while True:
            configure_logging()
            clear_screen()
            print_header()

            kml_files = list_kml_files()
            selected_files = select_kml_files(kml_files)

            if not check_existing_merged_file():
                continue  # If the user chose not to overwrite, go back to the main menu

            color_map = assign_colors_to_files(selected_files)
            remarks = get_remarks(selected_files)
            statistics = []
            merged_kml, total_valid_points = await merge_kml_files(selected_files, color_map, remarks, statistics)
            create_interactive_map(merged_kml, color_map, remarks)
            save_statistics_to_excel(statistics, total_valid_points)

            print("Process completed successfully. Details are available in the log and Excel file.")
            display_countdown(3)
            clear_screen()

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting gracefully...")
        logging.info("Process interrupted by user with CTRL+C. Exiting gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting gracefully...")
        logging.info("Process interrupted by user with CTRL+C at main entry point. Exiting gracefully.")
        sys.exit(0)

# UFEDKMLstacker
UFEDKMLstacker is a Python script designed to merge and visualize KML files exported from Cellebrite UFED [^1] using Plotly [^2]. This tool allows the stacking of multiple KML files to demonstrate overlapping locations of different data sources, each represented by a distinct color. By integrating this functionality, UFEDKMLstacker aids in forensic analysis and visualization, offering valuable insights into spatial relationships between different entities. Inspired by [UFEDMapper](https://github.com/ot2i7ba/UFEDMapper) and [UFEDKMLmerge](https://github.com/ot2i7ba/UFEDKMLmerge), this script has been customized to meet specific forensic needs, enabling professionals to streamline their workflow. Sharing this tool aims to benefit others in the forensic community.

> [!NOTE]
> This script is specifically tailored for KML files exported from Cellebrite UFED. Its compatibility or performance with KML files from other sources has not been tested.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
   - [Usage](#usage)
   - [PyInstaller](#pyinstaller)
   - [Releases](#releases)
- [Example](#example)
   - [Screenshots](#screenshots)
- [Changes](#changes)
- [License](#license)

# Features
- Asynchronous processing for handling multiple KML files efficiently.
- Merging of up to 10 KML files into a single visualization.
- Each KML file is represented in a unique color for easy differentiation.
- Logging: Logs activities both to a file and the console.
- Metadata extraction: File creation, modification time, and SHA-256 hash for integrity verification.
- Saves analysis results and maps in various formats (Excel, HTML).
- Enhanced user interaction and error handling.

# Requirements
- Python 3.7 or higher
   - The following Python packages:
   - pandas>=1.3.0,<1.4.0
   - lxml>=4.6.3,<5.0.0
   - aiofiles>=0.7.0,<0.8.0
   - plotly>=5.3.0,<6.0.0

# Installation
1. **Clone the repository**

   ```sh
   git clone https://github.com/yourusername/UFEDKMLstacker.git
   cd UFEDKMLstacker
   ```

2. **To install the required dependencies, use the following command**
   ```sh
   pip install -r requirements.txt
   ```

## Usage
1. **Place your KML files in the same directory as the script**

2. **Run the script**
   ```sh
   python UFEDKMLstacker.py
   ```

## Follow the Prompts
- **KML File Selection**<br>The script will search the directory for KML files and present a numbered list for selection.
- **Remark for Each File**<br>Enter a remark for each selected file to identify it in the visualization.
- **Color Assignment**<br>Colors are automatically assigned to each file for differentiation in the visualization.

## Interactive Map
The resulting map visualizes the data points from each KML file in distinct colors. The user can interact with the map, hover over points to see details, and filter based on the provided remarks.

## PyInstaller
To compile the UFEDKMLmerge script into a standalone executable, you can use PyInstaller. Follow the steps below:

1. Install PyInstaller (if not already installed):
   ```bash
   pip install pyinstaller
   ```

2. Compile the script using the following command:
   ```bash
   pyinstaller --onefile --name UFEDKMLstacker --icon=ufedkmlstacker.ico UFEDKMLstacker.py
   ```

- `--onefile`: Create a single executable file.
- `--name UFEDKMLmerge`: Name the executable UFEDMapper.
- `--icon=ufedkmlstacker.ico`: Use ufedkmlmerge.ico as the icon for the executable.

**Running the executable**: After compilation, you can run the executable found in the dist directory.

## Releases
A compiled and 7zip-packed version of UFEDKMLstacker for Windows is available as a release. You can download it from the **[Releases](https://github.com/ot2i7ba/UFEDKMLstacker/releases)** section on GitHub. This version includes all necessary dependencies and can be run without requiring Python to be installed on your system.

> [!IMPORTANT]
> An internet connection is required to display the maps in the generated HTML files. This is because the maps are rendered using Plotly, which relies on online resources to load the map tiles and other visualization components. Rest assured, no information from your local system is sent to Plotly during this process. The map data is sourced from OpenStreetMap [^3], ensuring compliance with GDPR regulations.

# Example

## The script lists available KML files and prompts for selection**
   ```sh
   Available KML files:
   1. Example1.kml
   2. Example2.kml
   3. Example3.kml
   e. Exit
   Enter the numbers of the desired KML files to merge (e.g., 1,2,3) or 'e' to exit:
   ```

## After selecting files, the script prompts for remarks
   ```sh
   Enter a remark for the file Example1.kml:
   Enter a remark for the file Example2.kml:
   Enter a remark for the file Example3.kml:
   ```

## The interactive map is then generated and saved
   ```sh
   Process completed successfully. Details are available in the log and Excel file.
   ```

___

# Changes

## Changes in 0.0.1
- Initial release.

___

# License
This project is licensed under the **[MIT license](https://github.com/ot2i7ba/UFEDKMLstacker/blob/main/LICENSE)**, providing users with flexibility and freedom to use and modify the software according to their needs.

# Contributing
Contributions are welcome! Please fork the repository and submit a pull request for review.

# Disclaimer
This project is provided without warranties. Users are advised to review the accompanying license for more information on the terms of use and limitations of liability.

# Conclusion
This script has been tailored to fit my specific professional needs, and while it may seem like a small tool, it has a significant impact on my workflow. This script is designed to aid forensic professionals in visualizing and analyzing location data extracted from multiple sources. By automating the merging and visualization process, UFEDKMLstacker enhances efficiency, allowing users to focus on critical analysis. Greetings to my dear colleagues [^4] who avoid scripts like the plague and think that consoles and Bash are some sort of dark magic – the [compiled](https://github.com/ot2i7ba/UFEDKMLstacker/releases) version will spare you the console kung-fu and hopefully be a helpful tool for you as well. 😉

[^1]: [Cellebrite UFED](https://cellebrite.com/) (Universal Forensic Extraction Device) is a forensic tool to extract and analyze data from mobile devices.
[^2]: Thanks to the [Plotly](https://plotly.com/python/) team for their excellent visualization library, which made creating interactive maps a breeze.
[^3]: [OpenStreetMap](https://www.openstreetmap.org/) is a collaborative mapping project that provides freely accessible map data.
[^4]: Greetings to PPHA-IuK.

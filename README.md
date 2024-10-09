# Kindle Highlights Parser

This project provides a Python-based parser for Kindle highlights and notes. It processes the "My Clippings.txt" file exported from Kindle devices and organizes the highlights and notes into a structured JSON format.

## Features

- Parses Kindle highlights and notes from "My Clippings.txt"
- Organizes data by book, including highlights and notes
- Matches notes to their corresponding highlights when possible
- Tracks processing progress to avoid duplicate entries
- Provides error handling and reporting for problematic entries

## Requirements

- Python 3.7+
- dataclasses-json library

## Installation

1. Clone the repository:
git clone https://github.com/yourusername/kindle-parser.git
cd kindle-parser

2. Create and activate a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate

3. Install the required dependencies:
pip install -r requirements.txt

## Usage

1. Place your "My Clippings.txt" file in the project root directory.

2. Run the parser:
python -m kindle_parser.parser

3. The parsed data will be saved in `output.json`, and processing information will be stored in `processed_entries.json`.

## Project Structure

- `kindle_parser/parser.py`: Contains the main parsing logic
- `tests/test_parser.py`: Contains unit tests for the parser
- `requirements.txt`: Lists the project dependencies
- `output.json`: The parsed highlights and notes in JSON format
- `processed_entries.json`: Tracks which entries have been processed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Todo
- Verify that notes are getting attached to the correct highlights
- Add chapter indexing to notes and highlights

## License

This project is licensed under the MIT License - see the LICENSE file for details.

import os
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import List, Optional, Dict
import json
from datetime import datetime
import hashlib
import re

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_dataclass(obj):
            return asdict(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@dataclass
class Location:
    start: int
    end: Optional[int] = None

@dataclass
class Note:
    content: str
    date_added: datetime
    page: int
    location: Optional[Location] = None

@dataclass
class Highlight:
    content: str
    date_added: datetime
    page: int
    note: Optional[Note] = None
    location: Optional[Location] = None

@dataclass
class Book:
    title: str
    authors: List[str]
    highlights: List[Highlight] = field(default_factory=list)
    notes: List[Note] = field(default_factory=list)
    bookmarks: List[Dict] = field(default_factory=list)

@dataclass
class Error:
    line_number: int
    error_message: str

class KindleParser:
    def __init__(self):
        self.books: Dict[str, Book] = {}
        self.errors: List[Error] = []
        self.processed_entries: set[str] = set()
        self.last_processed_timestamp: Optional[datetime] = None

    def read_clippings_file(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            return file.read()

    def write_json_output(self, output_path: str) -> None:
        output = {
            "books": {title: book.__dict__ for title, book in self.books.items()},
            "errors": [error.__dict__ for error in self.errors],
            "processedEntries": list(self.processed_entries),
            "lastProcessedTimestamp": self.last_processed_timestamp.isoformat() if self.last_processed_timestamp else None
        }
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(output, file, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)


    def read_processed_entries(self, output_path: str) -> None:
        try:
            with open(output_path, 'r') as file:
                data = json.load(file)
                self.processed_entries = set(data.get("processedEntries", []))
                self.last_processed_timestamp = datetime.fromisoformat(data.get("lastProcessedTimestamp", "")) if data.get("lastProcessedTimestamp") else None
        except FileNotFoundError:
            pass  # It's okay if the file doesn't exist yet

    def clean_text(self, text: str) -> str:
        # Remove non-ASCII characters and replace them with a space
        return ''.join(char if ord(char) < 128 else ' ' for char in text)

    def parse_clippings(self, content: str) -> None:
        # Clean the entire content before splitting
        cleaned_content = self.clean_text(content)
        entries = cleaned_content.split("==========")
        for i, entry in enumerate(entries):
            entry = entry.strip()
            if entry:
                try:
                    self.parse_entry(entry, i)
                except Exception as e:
                    self.errors.append(Error(i, str(e)))

    def parse_entry(self, entry: str, line_number: int) -> None:
        lines = entry.split('\n')
        if len(lines) < 2:
            raise ValueError(f"Invalid entry format at line {line_number}")

        book_info = lines[0].strip()
        metadata = lines[1].strip()
        
        book_title, authors = self.parse_book_info(book_info)
        entry_type, page, location, date_added = self.parse_metadata(metadata)

        content = '\n'.join(lines[2:]).strip() if len(lines) > 2 else ""

        if entry_type == "Highlight":
            self.add_highlight(book_title, authors, content, location, date_added, page)
        elif entry_type == "Note":
            self.add_note(book_title, authors, content, date_added, location, page)
        elif entry_type == "Bookmark":
            self.add_bookmark(book_title, authors, location, date_added, page)

    def parse_book_info(self, book_info: str) -> tuple[str, List[str]]:
        parts = book_info.split('(')
        title = parts[0].strip()
        authors = [author.strip() for author in parts[-1].rstrip(')').split(',')]
        return title, authors

    def parse_metadata(self, metadata: str) -> tuple[str, Optional[int], Optional[Location], datetime]:
        entry_type_match = re.search(r'Your (\w+)', metadata)
        page_match = re.search(r'page (\d+)', metadata)
        location_match = re.search(r'Location (\d+)(?:-(\d+))?', metadata)
        date_match = re.search(r'Added on (.+)$', metadata)

        if not entry_type_match or not date_match:
            raise ValueError(f"Invalid metadata format: {metadata}")

        entry_type = entry_type_match.group(1)
        page = int(page_match.group(1)) if page_match else None
        
        if location_match:
            start = int(location_match.group(1))
            end = int(location_match.group(2)) if location_match.group(2) else None
            location = Location(start, end)
        else:
            location = None  # Set location to None if not found

        date_added = datetime.strptime(date_match.group(1), '%A, %B %d, %Y %I:%M:%S %p')

        return entry_type, page, location, date_added

    def add_highlight(self, book_title: str, authors: List[str], content: str, location: Location, date_added: datetime, page: Optional[int]) -> None:
        book = self.get_or_create_book(book_title, authors)
        highlight = Highlight(content=content, date_added=date_added, page=page, location=location)
        book.highlights.append(highlight)

    def add_note(self, book_title: str, authors: List[str], content: str, date_added: datetime, location: Location, page: Optional[int]) -> None:
        book = self.get_or_create_book(book_title, authors)
        note = Note(content=content, date_added=date_added, page=page, location=location)
        
        # Try to match the note with a highlight
        matching_highlight = next((h for h in reversed(book.highlights) if h.location.start == note.location.start), None)
        
        if matching_highlight:
            matching_highlight.note = note
        else:
            book.notes.append(note)

    def add_bookmark(self, book_title: str, authors: List[str], location: Location, date_added: datetime, page: Optional[int]) -> None:
        book = self.get_or_create_book(book_title, authors)
        bookmark = {"location": location, "date_added": date_added, "page": page}
        book.bookmarks.append(bookmark)

    def get_or_create_book(self, title: str, authors: List[str]) -> Book:
        if title not in self.books:
            self.books[title] = Book(title, authors)
        return self.books[title]

    def generate_entry_id(self, entry: str) -> str:
        return hashlib.md5(entry.encode()).hexdigest()

    def is_processed(self, entry_id: str) -> bool:
        return entry_id in self.processed_entries

    def mark_as_processed(self, entry_id: str) -> None:
        self.processed_entries.add(entry_id)
        self.last_processed_timestamp = datetime.now()

    def process_clippings_file(self, input_path: str, output_path: str) -> None:
        current_dir = os.path.dirname(__file__)
        full_output_path = os.path.join(current_dir, output_path)
        self.read_processed_entries(full_output_path)
        content = self.read_clippings_file(input_path)
        self.parse_clippings(content)
        self.write_json_output(full_output_path)

# Usage
parser = KindleParser()
parser.process_clippings_file('./My Clippings.txt', 'output.json')
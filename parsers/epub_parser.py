from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup  # For parsing HTML in description

from .base_parser import EbookParser


class EpubParser(EbookParser):
    def parse_metadata(self, file_path: Path) -> Dict[str, Any]:
        metadata = {}
        try:
            book = epub.read_epub(str(file_path))

            # Title
            titles = book.get_metadata("DC", "title")
            if titles:
                metadata["title"] = titles[0][0]

            # Authors (Creators)
            creators = book.get_metadata("DC", "creator")
            if creators:
                metadata["authors"] = [
                    {"name": c[0]} for c in creators
                ]  # Simple name extraction

            # Language
            languages = book.get_metadata("DC", "language")
            if languages:
                metadata["language"] = languages[0][0]

            # Identifiers (e.g., ISBN)
            identifiers_meta = book.get_metadata("DC", "identifier")
            identifiers = []
            for id_meta in identifiers_meta:
                value = id_meta[0]
                scheme = (
                    id_meta[1].get("scheme", "UNKNOWN").upper()
                    if len(id_meta) > 1 and isinstance(id_meta[1], dict)
                    else "UNKNOWN"
                )
                if "ISBN" in scheme:
                    # Basic ISBN cleaning, could be more robust
                    cleaned_isbn = "".join(filter(str.isalnum, value))
                    if len(cleaned_isbn) == 10:
                        identifiers.append({"type": "ISBN_10", "value": cleaned_isbn})
                    elif len(cleaned_isbn) == 13:
                        identifiers.append({"type": "ISBN_13", "value": cleaned_isbn})
                    else:
                        identifiers.append({"type": scheme, "value": value})
                else:
                    identifiers.append({"type": scheme, "value": value})
            if identifiers:
                metadata["identifiers"] = identifiers

            # Publisher
            publishers = book.get_metadata("DC", "publisher")
            if publishers:
                metadata["publisher"] = publishers[0][0]

            # Publication Date
            dates = book.get_metadata("DC", "date")
            if dates:
                metadata["publication_date"] = dates[0][
                    0
                ]  # This might need further parsing/normalization

            # Description
            descriptions = book.get_metadata("DC", "description")
            if descriptions:
                # Description might be HTML, try to get text content
                soup = BeautifulSoup(descriptions[0][0], "html.parser")
                metadata["description"] = soup.get_text()

            # Subjects/Tags
            subjects = book.get_metadata("DC", "subject")
            if subjects:
                metadata["tags"] = [s[0] for s in subjects]

            metadata["format"] = "EPUB"

        except Exception as e:
            print(f"Error parsing EPUB metadata for {file_path}: {e}")
            # Optionally, re-raise or return partial metadata with an error flag
            metadata["parsing_error"] = str(e)

        return metadata

    def extract_cover_image_data(self, file_path: Path) -> Optional[Tuple[bytes, str]]:
        try:
            book = epub.read_epub(str(file_path))
            cover_item = None

            # Method 1: Check manifest for item with cover-image property
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_IMAGE:
                    if "cover-image" in (item.properties or []):  # EPUB 3
                        cover_item = item
                        break
            # Method 2: Check <meta name="cover" content="id" />
            if not cover_item:
                for meta_info in book.get_metadata(
                    "OPF", "meta"
                ):  # Sometimes it's 'OPF', sometimes it might be None
                    if (
                        isinstance(meta_info, tuple) and len(meta_info) > 1
                    ):  # meta_info can be complex
                        attributes = meta_info[1]
                        if (
                            isinstance(attributes, dict)
                            and attributes.get("name") == "cover"
                        ):
                            cover_id = attributes.get("content")
                            if cover_id:
                                cover_item = book.get_item_with_id(cover_id)
                                break
            # Method 3: Heuristic - find first image in spine or guide (less reliable)
            if not cover_item:
                # Look for common cover image names if not explicitly defined
                common_cover_names = ["cover.jpg", "cover.jpeg", "cover.png"]
                for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
                    if (
                        item.get_name().lower() in common_cover_names
                        or "cover" in item.get_name().lower()
                    ):
                        cover_item = item
                        break

            if cover_item:
                return cover_item.get_content(), cover_item.get_media_type()
        except Exception as e:
            print(f"Error extracting EPUB cover for {file_path}: {e}")
        return None

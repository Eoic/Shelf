from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import fitz  # PyMuPDF

from .base_parser import BookParser
from core.logger import logger


class PdfParser(BookParser):
    def parse_metadata(self, file_path: Path) -> Dict[str, Any]:
        metadata_dict = {}
        try:
            doc = fitz.open(str(file_path))
            meta = doc.metadata  # This is a dict

            if meta:
                metadata_dict["title"] = meta.get("title")
                metadata_dict["authors"] = [
                    {"name": author}
                    for author in meta.get("author", "").split(";")
                    if author.strip()
                ]
                metadata_dict["publisher"] = meta.get(
                    "producer"
                )  # PDF producer often isn't the book publisher
                # 'creationDate' and 'modDate' are D:YYYYMMDDHHMMSSZ' format
                pub_date = meta.get("creationDate")
                if pub_date and pub_date.startswith("D:"):
                    try:
                        # Attempt to parse to YYYY-MM-DD
                        metadata_dict["publication_date"] = (
                            f"{pub_date[2:6]}-{pub_date[6:8]}-{pub_date[8:10]}"
                        )
                    except:
                        pass  # Or store raw
                metadata_dict["tags"] = [
                    tag.strip()
                    for tag in meta.get("keywords", "").split(",")
                    if tag.strip()
                ]
                # PDF metadata is often less structured for things like ISBN.

            metadata_dict["format"] = "PDF"
            # metadata_dict['page_count'] = doc.page_count # Easy to get for PDF
            doc.close()
        except Exception as e:
            logger.error(f"Error parsing PDF metadata for {file_path}: {e}")
            metadata_dict["parsing_error"] = str(e)
        return metadata_dict

    def extract_cover_image_data(self, file_path: Path) -> Optional[Tuple[bytes, str]]:
        try:
            doc = fitz.open(str(file_path))
            if doc.page_count > 0:
                page = doc.load_page(0)  # Get the first page
                # Heuristic: Get the largest image on the first page, or the whole page as an image
                # For simplicity, let's render the first page as an image
                pix = page.get_pixmap(dpi=150)  # Render at 150 DPI
                img_bytes = pix.tobytes("png")  # Or "jpeg"
                doc.close()
                return img_bytes, "image/png"
            doc.close()
        except Exception as e:
            logger.error(f"Error extracting PDF cover for {file_path}: {e}")
        return None

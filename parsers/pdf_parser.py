from pathlib import Path
from typing import Any

import fitz

from core.logger import logger

from .base_parser import BookParser


class PdfParser(BookParser):
    def parse_metadata(self, file_path: Path) -> dict[str, Any]:
        metadata_dict = {}
        try:
            doc = fitz.open(str(file_path))
            meta = doc.metadata

            if meta:
                metadata_dict["title"] = meta.get("title")
                metadata_dict["authors"] = [
                    {"name": author}
                    for author in meta.get("author", "").split(";")
                    if author.strip()
                ]

                metadata_dict["publisher"] = meta.get("producer")
                pub_date = meta.get("creationDate")

                if pub_date and pub_date.startswith("D:"):
                    from contextlib import suppress

                    with suppress(Exception):
                        metadata_dict["publication_date"] = (
                            f"{pub_date[2:6]}-{pub_date[6:8]}-{pub_date[8:10]}"
                        )

                metadata_dict["tags"] = [
                    tag.strip()
                    for tag in meta.get("keywords", "").split(",")
                    if tag.strip()
                ]

            metadata_dict["format"] = "PDF"
            metadata_dict["page_count"] = doc.page_count
            doc.close()
        except Exception as e:
            logger.error(f"Error parsing PDF metadata for {file_path}: {e}")
            metadata_dict["parsing_error"] = str(e)

        return metadata_dict

    def extract_cover_image_data(self, file_path: Path) -> tuple[bytes, str] | None:
        try:
            doc = fitz.open(str(file_path))

            if doc.page_count > 0:
                page = doc.load_page(0)
                pix = page.get_pixmap(dpi=150, alpha=False)
                img_bytes = pix.tobytes("png")
                doc.close()

                return img_bytes, "image/png"

            doc.close()
        except Exception as e:
            logger.error(f"Error extracting PDF cover for {file_path}: {e}")

        return None

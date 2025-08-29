from pathlib import Path
from typing import Any

import fitz

from core.logger import logger

from .base_parser import BookParser


class PdfParser(BookParser):
    def parse_metadata(self, file_path: Path) -> dict[str, Any]:
        metadata = {}

        try:
            doc = fitz.open(str(file_path))
            meta = doc.metadata

            if meta:
                metadata["title"] = meta.get("title")

                metadata["authors"] = [
                    {"name": author} for author in meta.get("author", "").split(";") if author.strip()
                ]

                metadata["publisher"] = meta.get("producer")
                pub_date = meta.get("creationDate")

                if pub_date and pub_date.startswith("D:"):
                    from contextlib import suppress

                    with suppress(Exception):
                        metadata["publication_date"] = f"{pub_date[2:6]}-{pub_date[6:8]}-{pub_date[8:10]}"

                metadata["tags"] = [tag.strip() for tag in meta.get("keywords", "").split(",") if tag.strip()]

            metadata["format"] = "PDF"
            metadata["page_count"] = doc.page_count
            doc.close()
        except Exception as error:
            logger.error(f"Error parsing PDF metadata for {file_path}: {error}")
            metadata["parsing_error"] = str(error)

        return metadata

    def extract_cover_image_data(self, file_path: Path) -> tuple[bytes, str] | None:
        try:
            document = fitz.open(str(file_path))

            if document.page_count > 0:
                page = document.load_page(0)
                pixels = page.get_pixmap(dpi=150, alpha=False)  # type: ignore
                img_bytes = pixels.tobytes("png")
                document.close()

                return img_bytes, "image/png"

            document.close()
        except Exception as error:
            logger.error(f"Error extracting PDF cover for {file_path}: {error}")

        return None

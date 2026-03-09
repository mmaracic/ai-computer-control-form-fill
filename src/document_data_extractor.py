"""Module responsible for extracting data from documents in the data subfolder."""

from pathlib import Path

from docling.document_converter import DocumentConverter


class DocumentDataExtractor:
    """Class responsible for extracting data from documents in the data subfolder."""

    def __init__(self, data_folder: Path):
        """Initialize the extractor with the path to the data folder."""
        self.data_folder = data_folder

    def extract_data(self) -> dict[str, str]:
        """Extract data from documents in the data folder and return it as a dictionary."""
        extracted_data: dict[str, str] = {}
        converter = DocumentConverter()
        for file_path in self.data_folder.glob("*.pdf"):
            docling_document = converter.convert(file_path).document
            extracted_data[file_path.name] = docling_document.export_to_text()
        return extracted_data

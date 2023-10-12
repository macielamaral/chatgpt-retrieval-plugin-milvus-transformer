## Process Data to JSON

process_data_to_json.py

This script is a versatile tool for converting various types of academic documents, like PDF and LaTeX files, into a structured JSON format. It is designed to be integrated with Milvus for similarity search and other advanced retrieval functionalities.

Key Features:

    Multiple Input Types: Supports PDF, LaTeX, plain text, and email files, either from a local path or a URL.

    GROBID Integration: For PDFs, the script leverages GROBID for extracting and structuring academic metadata like titles, authors, abstracts, and references.

    LaTeX Parsing: For LaTeX files, it extracts the title, authors, date, and abstract directly from the LaTeX markup.

    Error Handling: Includes try-catch blocks and custom exceptions to handle unsupported file types and other errors gracefully.

    Temporary File Management: Creates and removes temporary files as needed to make the processing seamless.

    Batch Processing: Although designed for single-file operations, it can be easily integrated into batch processing systems.


## Usage

How to Run:

The script accepts a single argument that specifies the path or URL of the document to be processed. Use the following command to run the script:

```
python process_data_to_json.py "your_path_or_url_here"

```

## Dependencies:

    Python 3.x
    Requests
    GROBID
    GrobidClient
    argparse
    shutil
    re
    json
## Process a JSON File
process_xml_to_json.py

This script serves as a utility for transforming XML documents into JSON format, particularly focusing on XML structured according to the Text Encoding Initiative (TEI) guidelines.
Key Features:

    TEI Compliant: Designed to work with XML documents adhering to TEI guidelines, which are a standard format for digital text representation.

    Rich Data Extraction: Extracts metadata such as title, authors, date, abstract, and keywords, as well as the main body and LaTeX equations from the XML string.

    Directory Traversal: Automatically traverses directories to find and process .tei.xml files, allowing for batch processing.

    Sanitization and Formatting: Utilizes custom functions for sanitizing and formatting extracted data, making it suitable for filenames or URL slugs.

    LaTeX Support: The extracted content is transformed into LaTeX syntax, offering a rich-text representation suitable for academic documents.

    Error Handling: Provides error messages for missing or problematic data, allowing for fault tolerance.

## Usage

The script accepts command-line arguments to specify the source and destination directories. Use the following command to run the script:

```
python process_xml_to_json.py --dir_source_path YOUR_SOURCE_DIR_PATH --dir_destination_path YOUR_DESTINATION_DIR_PATH

```
## Dependencies:

    xml.etree.ElementTree for XML parsing
    os and json for file and directory operations
    argparse for command-line argument parsing
    re for regular expressions used in string sanitization
    langchain for text loading
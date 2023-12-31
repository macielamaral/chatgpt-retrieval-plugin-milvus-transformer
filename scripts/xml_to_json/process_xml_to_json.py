# scripts/process_xml_to_json.py

from langchain.document_loaders import TextLoader
import os
import re
import json
import xml.etree.ElementTree as ET
import argparse

def recursive_text_extraction(element):
    """ 
    Description:
        This function extracts all text content from a given XML element, including any nested child elements. 
        It traverses the XML hierarchy recursively, ensuring even the deepest nested texts are captured.

    Parameters:
        element: The XML element from which to extract text.

    Returns:
        A concatenated string of all text found within the provided XML element and its descendants.
    """
    text = element.text or ""
    for child in element:
        text += recursive_text_extraction(child)
        if child.tail:
            text += child.tail
    return text

def extract_information_from_tei(tei_string):
    """ 
    Description:
        This function processes an XML string structured per the Text Encoding Initiative (TEI) guidelines, 
        a standard format for digital text representation. It extracts metadata like title, authors, date, abstract, and keywords, 
        as well as the content from the XML string. The content includes the main body of the document and its LaTeX equations. 
        The extracted information is then formatted to LaTeX syntax and returned as a dictionary.

    Parameters:

        tei_string: The XML string formatted according to the TEI guidelines.

    Returns:

        A dictionary containing:
            title: Document title.
            authors: List of authors.
            date: Publication date.
            abstract: Abstract of the document.
            keywords: List of keywords.
            latex_doc: LaTeX-formatted content of the document.
    """
    # Parse the XML string
    root = ET.fromstring(tei_string)

    # XML namespaces
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}

    # LaTeX document
    latex_doc = []
    
    # Details dictionary
    details = {}

    # Extract the title - only proceed if we have a title
    title = root.find('.//tei:titleStmt/tei:title', ns)
    if title is None or title.text is None:
        raise ValueError("Missing title in document")
        
    # Extract the title
    title = root.find('.//tei:titleStmt/tei:title', ns)
    if title is not None and title.text is not None:
        details['title'] = title.text[:1000] # restricting according Milvus  FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1000), 
        latex_doc.append('\\title{' + title.text + '}')

    # Extract the date
    date = root.find('.//tei:publicationStmt/tei:date', ns)
    if date is not None and date.text is not None:
        details['date'] = date.text
        latex_doc.append('\\date{' + date.text + '}')
        
    # Extract the authors from the main document only
    authors = []
    for author in root.findall('.//tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:biblStruct/tei:analytic/tei:author', ns):
        forename = author.find('tei:persName/tei:forename', ns)
        surname = author.find('tei:persName/tei:surname', ns)
        if forename is not None and surname is not None:
            authors.append(forename.text + ' ' + surname.text)
            latex_doc.append('\\author{' + forename.text + ' ' + surname.text + '}')
    details['authors'] = authors

    # Extract the abstract
    abstract = root.find('.//tei:abstract', ns)
    if abstract is not None:
        details['abstract'] = ' '.join([p.text for p in abstract.findall('.//tei:p', ns)])
        latex_doc.append('\\begin{abstract}')
        for p in abstract.findall('.//tei:p', ns):
            latex_doc.append(p.text)
        latex_doc.append('\\end{abstract}')

    # Extract the keywords
    keywords = root.find('.//tei:keywords', ns)
    if keywords is not None:
        details['keywords'] = [term.text for term in keywords.findall('tei:term', ns)]
        latex_doc.append('\\keywords{' + ', '.join([term.text for term in keywords.findall('tei:term', ns)]) + '}')

    # Process each section in the body of the document
    for body in root.findall('.//tei:body', ns):
        for div in body.findall('.//tei:div', ns):
            # Add section
            section_title = div.find('tei:head', ns)
            if section_title is not None:
                latex_doc.append('\\section{' + section_title.text + '}')
            
            # Process each child element in the div
            for child in div:
                # If the child is a paragraph
                if child.tag == '{http://www.tei-c.org/ns/1.0}p':
                    paragraph_text = recursive_text_extraction(child)
                    latex_doc.append(paragraph_text)

                # If the child is a formula
                elif child.tag == '{http://www.tei-c.org/ns/1.0}formula':
                    # Add equation
                    latex_doc.append('\\begin{equation}')
                    latex_doc.append(child.text.strip())  # strip leading and trailing whitespace
                    latex_doc.append('\\end{equation}')

                    
    # Begin the bibliography
    latex_doc.append('\\begin{thebibliography}{99}')

    # Extract the references
    for biblStruct in root.findall('.//tei:div[@type="references"]/tei:listBibl/tei:biblStruct', ns):
        # Extract the authors
        authors = [forename.text + ' ' + surname.text for forename, surname in zip(biblStruct.findall('.//tei:author/tei:persName/tei:forename', ns), biblStruct.findall('.//tei:author/tei:persName/tei:surname', ns))]

        # Extract the title
        title = biblStruct.find('.//tei:title', ns)

        # Extract the year
        year = biblStruct.find('.//tei:date', ns)

        # Extract the publisher (for books) or journal title (for articles)
        publisher = biblStruct.find('.//tei:publisher', ns)
        journal = biblStruct.find('.//tei:title[@level="j"]', ns)

        # Extract the volume and page numbers (for articles)
        volume = biblStruct.find('.//tei:biblScope[@unit="volume"]', ns)
        page = biblStruct.find('.//tei:biblScope[@unit="page"]', ns)

        # Format the reference for the bibliography
        reference = ', '.join(filter(None, [', '.join(authors), (title.text if title is not None else None), (year.text if year is not None else None), (publisher.text if publisher is not None else None), (journal.text if journal is not None else None), (volume.text if volume is not None else None), (page.text if page is not None else None)]))
        latex_doc.append('\\bibitem{' + biblStruct.attrib['{http://www.w3.org/XML/1998/namespace}id'] + '} ' + reference + '.')

    # End the bibliography
    latex_doc.append('\\end{thebibliography}')

    details['latex_doc'] = '\n'.join(latex_doc)
    return details

def slugStrip(instr):
    """
        Description:
            The slugStrip function sanitizes and formats a given string to make it suitable for use as a file name or URL slug. It removes any non-alphanumeric characters, replaces spaces with hyphens, and converts the string to lowercase. The function also ensures that the resulting string does not start or end with a hyphen.

        Parameters:

            instr: The input string that needs to be transformed into a slug.

        Returns:

            A sanitized, hyphen-separated, and lowercase string suitable for use as a file name or URL slug. 
    """
    outstr = re.sub('[^a-zA-Z0-9 ]','',instr)
    while "  " in outstr:
        outstr = outstr.replace("  "," ")
    outstr = outstr.replace(" ","-")
    outstr = outstr.lower()
    if len(outstr) > 0:
        if outstr[0] == "-":
            outstr = outstr[1:]
    if len(outstr) > 0: 
        if outstr[-1] == "-":
            outstr = outstr[:-1]
    return outstr

def create_file_name(title):
    """ 
    Description:
        The create_file_name function is designed to transform a given string (typically a title or heading) into a filename suitable for a JSON file. It ensures that the resulting filename is sanitized, appropriately formatted, and adheres to common filesystem constraints.

    Parameters:

        title: A string representing the title or heading that you want to convert into a filename.

    Returns:

        A string representing the sanitized and formatted filename with a ".json" extension.
    """
    # Use the slugStrip function to clean the title
    title = slugStrip(title)

    # Replace spaces with underscores
    title = title.replace(' ', '_')

    # Limit length to 250 characters (to allow for the .json extension)
    title = title[:250]
    
    # Append the .json extension
    title += '.json'

    return title


def extract_and_save_data_from_tei(dir_source_path: str, dir_destination_path: str):
    """
    Extracts data from .tei.xml files in a source directory and saves the extracted data 
    as .json files in a destination directory.
    
    Parameters:
    - dir_source_path (str): Path to the source directory containing .tei.xml files.
    - dir_destination_path (str): Path to the destination directory where .json files will be saved.
    
    Returns:
    None
    """
    
    # Walk through the source directory structure
    for dirpath, dirnames, filenames in os.walk(dir_source_path):
        # Process each .tei.xml file in the current directory
        for filename in filenames:
            if filename.endswith('.tei.xml'):
                # Create the full source file path
                full_source_path = os.path.join(dirpath, filename)

                loader = TextLoader(full_source_path)
                documents = loader.load()

                # Extract the information from each loaded document
                for document in documents:
                    try:
                        latex_doc = extract_information_from_tei(document.page_content)
                    except ValueError as e:
                        print(f"Skipping file due to error: {e}")
                        continue

                    # Create the destination directory path
                    relative_dirpath = os.path.relpath(dirpath, dir_source_path)
                    full_destination_dirpath = os.path.join(dir_destination_path, relative_dirpath)

                    # Create the destination directory if it does not exist
                    os.makedirs(full_destination_dirpath, exist_ok=True)

                    # Create the destination file name
                    file_destination_name = create_file_name(latex_doc['title'])

                    # Create the full destination file path
                    full_destination_path = os.path.join(full_destination_dirpath, file_destination_name)

                    # Save the latex_doc dictionary to a JSON file
                    with open(full_destination_path, 'w') as f:
                        json.dump(latex_doc, f)

def main(args):
    dir_source_path = args.dir_source_path
    dir_destination_path = args.dir_destination_path

    extract_and_save_data_from_tei(dir_source_path,dir_destination_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir_source_path", default="data/xml/", help="The path to the source directory containing XML files.")
    parser.add_argument("--dir_destination_path", default="data/json/", help="The path to the destination directory where JSON files will be saved.")
    
    args = parser.parse_args()
    main(args)

# scripts/process_data_to_json.py

import os
import requests
import argparse
import shutil
import re
import json
from urllib.parse import urlparse
from grobid_client.grobid_client import GrobidClient
from xml_to_json.process_xml_to_json import extract_and_save_data_from_tei
from datetime import datetime


class UnsupportedFileTypeError(Exception):
    """Exception raised for unsupported file types."""
    def __init__(self, message="Unsupported file type"):
        self.message = message
        super().__init__(self.message)

def determine_file_type(input_file):
    file_extension = os.path.splitext(input_file)[1]
    if file_extension == '.pdf':
        return 'pdf'
    elif file_extension == '.tex':
        return 'latex'
    elif file_extension == '.txt':
        return 'text'
    elif file_extension == '.eml':
        return 'email'
    # Add other file extensions here

    # Remove the temporary file
    if os.path.exists(input_file):
        os.remove(input_file)
    raise UnsupportedFileTypeError("Unsupported file type: " + str(input_file))



def send_pdf_to_grobid(input_path, temp_input_dir, output_dir="./grobid_output/"):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    client = GrobidClient(config_path="./grobid_config.json")
    
    # Pass the temporary input directory to GROBID
    client.process("processFulltextDocument", temp_input_dir, output_dir, n=10)
    #client.process("processFulltextDocument", input_path_or_url, output_dir, n=10, consolidate_citations=True, consolidate_header=True)



    # Remove the temporary file
    temp_file_path = os.path.join(temp_input_dir, os.path.basename(input_path))
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)
    
    # Construct the path to the output XML based on the input filename
    xml_filename = os.path.basename(temp_file_path).replace('.pdf', '.grobid.tei.xml')
    xml_file_path = os.path.join(output_dir, xml_filename)

    return xml_file_path


def save_file(temp_input_dir,input_path_or_url):

    
    # Determine if the input is a URL or a local file
    if input_path_or_url.startswith("http://") or input_path_or_url.startswith("https://"):
        # Download the file
        response = requests.get(input_path_or_url)
        filename = os.path.basename(urlparse(input_path_or_url).path)
        temp_file_path = os.path.join(temp_input_dir, filename)
        with open(temp_file_path, 'wb') as f:
            f.write(response.content)
    else:
        # Copy the local file to the temporary directory
        shutil.copy(input_path_or_url, temp_input_dir)
        temp_file_path = os.path.join(temp_input_dir, os.path.basename(input_path_or_url))

    return temp_file_path


def latex_to_json(input_file, dir_destination_path):
    # Read the LaTeX content from the input file
    with open(input_file, 'r') as f:
        latex_text = f.read()
    
    # Initialize the JSON object
    json_data = {}
    
    # Parse title, author, and date
    title_match = re.search(r'\\title\{(.*?)\}', latex_text)
    author_match = re.search(r'\\author\{(.*?)\}', latex_text)
    date_match = re.search(r'\\date\{(.*?)\}', latex_text)
    
    if title_match:
        json_data['title'] = title_match.group(1)
    if author_match:
        json_data['authors'] = [author.strip() for author in author_match.group(1).split(",")]
    if date_match:
        json_data['date'] = date_match.group(1)
        
    # Parse abstract
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', latex_text, re.DOTALL)
    if abstract_match:
        json_data['abstract'] = abstract_match.group(1).strip()
    
    # Include the whole LaTeX document
    json_data['latex_doc'] = latex_text

    # Create the destination directory if it doesn't exist
    if not os.path.exists(dir_destination_path):
        os.makedirs(dir_destination_path)
    
    # Generate the JSON file name based on the input LaTeX file name
    json_file_name = os.path.splitext(os.path.basename(input_file))[0] + '.json'
    json_file_path = os.path.join(dir_destination_path, json_file_name)
    
    # Save the JSON data to the destination directory
    with open(json_file_path, 'w') as f:
        json.dump(json_data, f, indent=4)

    # Remove the temporary file
    if os.path.exists(input_file):
        os.remove(input_file)
    
    return json_file_path


def main(input_path_or_url):
    try:
        # Create a temporary input directory
        temp_input_dir = "./data_input/"
        if not os.path.exists(temp_input_dir):
            os.makedirs(temp_input_dir)
        
        input_file = save_file(temp_input_dir, input_path_or_url)
        file_type = determine_file_type(input_file)
        
        dir_destination_path = "./process_json/new_2023/"
        
        if file_type == 'pdf':
            grobid_output_dir="./grobid_output/"
            xml_data = send_pdf_to_grobid(input_file, temp_input_dir, grobid_output_dir)
            if os.path.exists(xml_data):
                extract_and_save_data_from_tei(grobid_output_dir, dir_destination_path)
                os.remove(xml_data)
                print("New JSON file from pdf saved in:", dir_destination_path)
        
        elif file_type == 'latex':
            latex_to_json(input_file, dir_destination_path)
            print("New JSON file from latex saved in:", dir_destination_path)
        
        elif file_type == 'text':
            json_data = text_to_json(input_file, dir_destination_path)
        
        elif file_type == 'email':
            json_data = email_to_json(input_path_or_url)
        
        else:
            print("Unsupported file type:", file_type)
            # Remove the temporary file
            if os.path.exists(input_file):
                os.remove(input_file)
            return

    except Exception as e:
        print(f"An error occurred: {e}")




def text_to_json(input_file, dir_destination_path):
    # Read the plain text content from the input file
    with open(input_file, 'r') as f:
        text_content = f.read()
    
    # Initialize the JSON object
    json_data = {}
    
    # Use the file name as the title
    json_data['title'] = os.path.splitext(os.path.basename(input_file))[0]
    
    # Use the current date as the date
    json_data['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Assume authors list is empty (since we don't have this metadata in plain text)
    json_data['authors'] = []
    
    # Assume the first paragraph is the abstract
    paragraphs = text_content.split('\n\n', 1)
    if paragraphs:
        json_data['abstract'] = paragraphs[0].strip()
    
    # Limit the abstract to 1000 characters
    json_data['abstract'] = json_data['abstract'][:1000]

    # Include the whole text document, ensuring we escape any characters that need it
    json_data['latex_doc'] = text_content

    # Create the destination directory if it doesn't exist
    if not os.path.exists(dir_destination_path):
        os.makedirs(dir_destination_path)
    
    # Generate the JSON file name based on the input text file name
    json_file_name = os.path.splitext(os.path.basename(input_file))[0] + '.json'
    json_file_path = os.path.join(dir_destination_path, json_file_name)
    
    # Save the JSON data to the destination directory
    with open(json_file_path, 'w') as f:
        json.dump(json_data, f, indent=4)
    
    return json_file_path


def email_to_json(input_path_or_url):
    # Convert email to JSON
    pass

def process_and_insert_into_milvus(json_data):
    # Use your existing process_json.py logic here for inserting into Milvus
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process various types of files and convert them to JSON.')
    parser.add_argument('input_path_or_url', type=str, help='The path or URL of the file to be processed.')
    args = parser.parse_args()
    main(args.input_path_or_url)


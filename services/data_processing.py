"""
Copyright (c) 2023 Your Name

Filename: QGR_data_processing.py
Authors: Marcelo Amaral, ChatGPT
Created: Aug 17, 2023
Last Updated: Aug 17, 2023

Description:
This script collects, processes, and organizes personal data into Milvus vector database. 

For detailed descriptions of each function, refer to the function-level docstrings or the script documentation.
"""

#numpy and milvus connection

import os
import json
import re
import hashlib
from typing import List
import numpy as np
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
import requests

from models.models import Document, DocumentChunk, DocumentChunkMetadata, Partition, Collection
from typing import Dict, List, Optional, Tuple



# The powerfull transformers models
from sentence_transformers import SentenceTransformer

#tokenize
from transformers import GPT2Tokenizer

# Initialize the tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")

#Text splitter
from langchain.text_splitter import LatexTextSplitter


# Load the pre-trained SBERT model once
sbert_model = SentenceTransformer('sentence-transformers/multi-qa-MiniLM-L6-cos-v1') 

# default values
MILVUS_COLLECTION = os.environ.get("MILVUS_COLLECTION") #Default Collection
CATEGORY = "ChatGPT"
PARTITION = "chats"
MAX_TOKEN_COUNT = 2000  # Set your maximum token count based on your GPT model's limitatio

#using sentence level embedding
def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Embed texts using the pre-trained SBERT model.

    Args:
        texts: The list of texts to embed.

    Returns:
        A list of embeddings, each of which is a list of floats.
    """
    # Truncate each sentence in texts to the first 512 characters
    truncated_texts = [text[:512] for text in texts]

    # Generate the sentence embeddings using SBERT
    embeddings = sbert_model.encode(truncated_texts)

    # Normalize the embeddings
    normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1)[:, None]

    return normalized_embeddings.tolist()


def clean_description(description):
    if pd.isnull(description):
        return ''
    # Remove URLs
    description = re.sub(r'http\S+|www.\S+', '', description, flags=re.MULTILINE)
    # Remove timestamps
    description = re.sub(r'\d+:\d+:\d+|\d+:\d+', '', description)
    # Remove sequences of characters that are longer than a certain threshold (e.g., 30)
    description = re.sub(r'\S{30,}', '', description)
    # Remove special characters
    description = re.sub(r'[^a-zA-Z0-9 \n\.]', '', description)
    # Replace multiple consecutive newlines with a single space
    description = re.sub(r'\n+', '\n', description)
    # Remove extra spaces
    description = re.sub(r' +', ' ', description)
    return description

def clean_latex(latex_content):
    cleaned_content = re.sub(r'[\u2022-\u5424]', '', latex_content)
    cleaned_content = re.sub(r'[^\x00-\x7F]+', '', cleaned_content)
    # Remove extra spaces
    cleaned_content = re.sub(r' +', ' ', cleaned_content)
    return cleaned_content


def splitText(content, splitter, length, overlap=20):

    text_splitter = splitter(
        chunk_size = length,
        chunk_overlap  = overlap,
        length_function = len,
    )
    textsDocument = text_splitter.create_documents([content])
    texts = text_splitter.split_documents(textsDocument)
    return texts


def process_file_from_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        # Get the relative path from the root folder to the current directory
        rel_path = os.path.relpath(root, folder_path)
        
        # Replace path separators with underscores (or any other character) to create a single string
        category = rel_path.replace(os.path.sep, '_')
        
        # If the relative path is ".", set the category to the base name of the root directory
        if category == ".":
            category = os.path.basename(root)

        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as json_file:
                    data = json.load(json_file)
                    entry = {
                        "title": data.get("title"),
                        "date": data.get("date"),
                        "authors": ", ".join(data.get("authors", [])),
                        "abstract": data.get("abstract"),
                        "content": data.get("latex_doc"),
                        "category": category
                    }
                return entry, file_path
    return None, None


def generate_document_id(title, authors, date):
    combined_str = f"{title}-{authors}-{date}"
    return hashlib.sha256(combined_str.encode()).hexdigest()


def get_document_chunks(documents: List[Document], chunk_token_size: Optional[int]) -> Dict[str, List[DocumentChunk]]:
    """Convert a list of documents into a dictionary from document id to list of document chunks."""
    document_chunks: Dict[str, List[DocumentChunk]] = {}
 
    for doc in documents:
        # Extracting the metadata and content from the document
        # Default values if metadata is None
        title_value = "Unknown"
        current_date = str(datetime.now().strftime("%Y-%m-%d"))
        date_value = current_date
        author_value = "Unknown"
        abstract_value = "Unknown"
        keywords_value = "Unknown"
        category_value = "Unknown"

        # Update the values if metadata is provided
        if doc.metadata is not None:
            title_value = doc.metadata.title or "Unknown"
            date_value = doc.metadata.created_at or current_date
            author_value = doc.metadata.authors or "Unknown"
            abstract_value = doc.metadata.abstract or "Unknown"
            keywords_value = doc.metadata.keywords or "Unknown"
            category_value = doc.metadata.category or "Unknown"
            
            
       
        content = doc.text
        partition_name = doc.partition or PARTITION
        collection_name = doc.collection or MILVUS_COLLECTION

        if len(date_value) > 1000:
            date_value = clean_description(date_value)
        date_value = date_value[:250]  # Truncate to 256 characters

        if len(keywords_value) > 1000:
            keywords_value = clean_description(keywords_value)
        keywords_value = keywords_value[:1004]  # Truncate to 1024 characters
        
        if len(author_value) > 1000:
            author_value = clean_description(author_value)
        author_value = author_value[:1000]  # Truncate to 1024 characters
        
        if len(title_value) > 1000:
            title_value = clean_description(title_value)
        title_value = title_value[:900]  # Truncate to 1024 characters
        
        if len(abstract_value) > 4000:
            abstract_value = clean_description(abstract_value)
        abstract_value = abstract_value[:4000]  # Truncate to 4096 characters

        if len(category_value) > 1000:
            category_value = clean_description(category_value)
        category_value = category_value[:250]  # Truncate to 256 characters
        
        
        if partition_name == "notes":
            content = clean_description(content)
        else:
            content = clean_latex(content)
        docslatex = splitText(content, LatexTextSplitter, chunk_token_size)


        documentId_value = generate_document_id(title_value, author_value, date_value)

        #doc_id = doc.id or documentId_value
        doc_id = documentId_value

        # Create DocumentChunk objects for each chunk
        doc_chunks = []
        for chunk in docslatex:
            if len(chunk.page_content) > chunk_token_size:
                embeddingElement = clean_description(chunk.page_content)
            else:
                embeddingElement = chunk.page_content

            content_vector_element = get_embeddings([embeddingElement])[0]
            
            chunk_metadata = DocumentChunkMetadata(
                created_at=date_value,
                authors=author_value,
                title=title_value,
                abstract=abstract_value,
                keywords=keywords_value,
                category=category_value,
                document_id=doc_id,
            )

            doc_chunk = DocumentChunk(
                id=f"{doc_id}_{len(doc_chunks)}",
                text=embeddingElement,
                collection=collection_name,
                partition=partition_name,
                metadata=chunk_metadata,
                embedding=content_vector_element
            )   

            doc_chunks.append(doc_chunk)
            
        document_chunks[doc_id] = doc_chunks


    return document_chunks


def convertToVector(sentence, model, length):
    # Truncate the sentence 
    sentence = sentence[:length]

    # Generate the sentence embedding using SBERT
    embedding = model.encode(sentence)

    # Normalize the embeddings
    embedding = embedding / np.linalg.norm(embedding)

    return embedding.tolist()  



# Function to load existing processed files
def load_processed_files(filename):
    try:
        with open(filename, 'r') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return []
    
class UnsupportedFileTypeError(Exception):
    """Exception raised for unsupported file types."""
    def __init__(self, message="Unsupported file type"):
        self.message = message
        super().__init__(self.message)

class UnsupportedPartitionError(Exception):
    """Exception raised for unsupported Partition."""
    def __init__(self, message="Unsupported Partition for the database"):
        self.message = message
        super().__init__(self.message)

class UnsupportedCollectionError(Exception):
    """Exception raised for unsupported Collection."""
    def __init__(self, message="Unsupported Collection for the database"):
        self.message = message
        super().__init__(self.message)        

def process_and_upload_documents_url(documents_url, collection, partition):
    errors = []
    if collection not in Collection.__members__:
        raise UnsupportedCollectionError("Unsupported Collection: " + str(collection))
    
    if partition not in Partition.__members__:
        raise UnsupportedPartitionError("Unsupported Partition: " + str(partition))
    
    for document_url in documents_url:
        parsed_url = urlparse(document_url)
        if not parsed_url.scheme in ['http', 'https']:
            raise ValueError("Invalid URL scheme")
        if not parsed_url.netloc:
            raise ValueError("Invalid URL")
        try:
            file_extension = os.path.splitext(document_url)[1].lower()
            if file_extension not in {'.pdf', '.tex', '.txt'}:
                raise UnsupportedFileTypeError("Unsupported file type: " + file_extension)

            input_dir = os.path.join("./data", collection)
            input_dir = os.path.join(input_dir, partition)
            os.makedirs(input_dir, exist_ok=True)

            # Download the file
            response = requests.get(document_url)
            response.raise_for_status()

            filename = os.path.basename(urlparse(document_url).path)
            file_path = os.path.join(input_dir, filename)

            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Add logic to process and upload the file

        except requests.RequestException as e:
            errors.append(f"Error downloading {document_url}: {e}")
        except UnsupportedFileTypeError as e:
            errors.append(f"Error: {e}")
        except Exception as e:
            errors.append(f"An error occurred: {e}")
    
    if errors:
        raise Exception("Errors occurred during processing: " + "; ".join(errors))

    return "Documents scheduled to upload successfully"


def get_document_content(document_id: str) -> dict:
    """
    Retrieves the content of a document based on its document_id.

    :param document_id: The unique identifier of the document.
    :return: A dictionary containing the document_id and its content.
    :raises FileNotFoundError: If the document does not exist.
    """
    # Validate that the document_id does not contain path traversal characters
    if '..' in document_id or '/' in document_id or '\\' in document_id:
        raise ValueError("Invalid document_id")

    document_path = f"./data/json_source/{document_id}.json"
    if not os.path.exists(document_path):
        raise FileNotFoundError(f"Document with ID {document_id} not found")

    with open(document_path, 'r') as file:
        document_content = json.load(file)
    
    # Ensure the content is in string format if it's JSON
    document_text = json.dumps(document_content) if isinstance(document_content, dict) else document_content

    # Tokenize and count the tokens
    tokens = tokenizer.encode(document_text)
    token_count = len(tokens)
    
    if token_count > MAX_TOKEN_COUNT:
        raise ValueError("Document size exceeds the maximum token limit supported")


    return {"document_id": document_id, "content": document_content}

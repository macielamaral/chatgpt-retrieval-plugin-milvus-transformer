# scripts/process_json.py

# Importing qgr package functions
import services.data_processing as qgr

from pymilvus import Collection
from sentence_transformers import SentenceTransformer
import argparse
import json
import os
import shutil
#Text splitter
from langchain.text_splitter import LatexTextSplitter
from datastore.factory import get_datastore
import asyncio


def save_document_as_json(document_id, document_content, base_folder="../../data/json_source"):
    """
    Save the document content as a JSON file named with the document_id.
    """
    
    # Ensure the base directory exists
    os.makedirs(base_folder, exist_ok=True)

    file_path = os.path.join(base_folder, f"{document_id}.json")

    try:
        # Attempt to save as JSON
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(document_content, json_file, ensure_ascii=False, indent=4)
    except TypeError as e:
        print(f"Error saving document {document_id}: {e}")
        # Handle or log the error appropriately

def stringify_authors_or_keywords(value):
    if isinstance(value, list):
        return ', '.join(value)
    elif isinstance(value, str):
        return value
    else:
        return "Unknown"
    
async def insert_data_json_into_milvus(
        collection_name,
        partition_name,
        sbert_model_name,
        folder_path,
        folder_path_not_processed,
        processed_file_name,
        files_processed_save_max=100
    ):

    files_process_max=12000
    
    # Load the pre-trained SBERT model
    sbert_model = SentenceTransformer(sbert_model_name) 

    # Initialize a list to keep track of processed file paths
    processed_files = qgr.load_processed_files(processed_file_name)

    files_processed = 0
    while files_processed < files_process_max:
        try:
            entry, file_path = qgr.process_file_from_folder(folder_path)
        except Exception as e:
            print(f"error folder_path: {folder_path}")
            print(f"Error details: {str(e)}")
            break

        if entry is None:
            break
        
        try:
            date_value = entry.get("date", "") or "Unknown"  # Use "Unknown" if date is None or empty
            if len(date_value) > 1000:
                date_value = qgr.clean_description(date_value)
            date_value = date_value[:250]  # Truncate to 256 characters

            keywords = entry.get("keywords", "") or "Unknown"  # Use "Unknown" if keywords is None or empty
            keywords_value = stringify_authors_or_keywords(keywords)[:1004]
            if len(keywords_value) > 1000:
                keywords_value = qgr.clean_description(keywords_value)
            keywords_value = keywords_value[:1004]  # Truncate to 1024 characters
            
            authors = entry.get("authors", "") or "Unknown" 
            author_value = stringify_authors_or_keywords(authors)[:1000]
            if len(author_value) > 1000:
                author_value = qgr.clean_description(author_value)
            author_value = author_value[:1000]  # Truncate to 1024 characters
            
            title_value = entry.get("title", "") or "Unknown"
            if len(title_value) > 1000:
                title_value = qgr.clean_description(title_value)
            title_value = title_value[:900]  # Truncate to 1024 characters
            
            abstract_value = entry.get("abstract", "") or "Unknown"
            if len(abstract_value) > 4000:
                abstract_value = qgr.clean_description(abstract_value)
            abstract_value = abstract_value[:4000]  # Truncate to 4096 characters

            category_value = entry.get("category", "") or "Unknown"
            if len(category_value) > 1000:
                category_value = qgr.clean_description(category_value)
            category_value = category_value[:250]  # Truncate to 256 characters
            
            content = entry.get("latex_doc", "")
            
            if partition_name == "notes":
                content = qgr.clean_description(content)
            else:
                content = qgr.clean_latex(content)
            
            docslatex = qgr.splitText(content, LatexTextSplitter, 512)            
    
            documentId_value = qgr.generate_document_id(title_value, author_value, date_value)

            # Save the document as a JSON file
            save_document_as_json(documentId_value, entry, base_folder="../../data/json_source")

            for chunk in docslatex:
                if len(chunk.page_content) > 512:
                    embeddingElement = qgr.clean_description(chunk.page_content)
                else:
                    embeddingElement = chunk.page_content  # Access the page_content attribute
                content_vector_element = qgr.convertToVector(embeddingElement, sbert_model, 512)  # Provide the model and length

                # Create a dictionary for the document
                doc = [
                    [documentId_value],
                    [title_value],
                    [date_value],
                    [author_value],
                    [abstract_value],
                    [keywords_value],
                    [category_value],
                    [embeddingElement],
                    [content_vector_element]
                ]
                #insert data
                #To Do: use different collection_name, currently set global a default
                insert_result = await datastore.raw_upsert(doc, collection_name, partition_name)
                
                if not insert_result:
                    title = entry.get("title", "")
                    print(f"fail: {title_value} : {embeddingElement}")


            # Delete the file after insertion
            os.remove(file_path)

            # Append the successfully processed file path to the list
            processed_files.append(file_path)

            files_processed += 1  # Increment the counter

            # Flush the data and save the processed file paths every 1000 files
            if files_processed % files_processed_save_max == 0:
                await datastore.flush()

                with open(processed_file_name, 'w') as json_file:
                    json.dump(processed_files, json_file)
                print(f"Flushed and saved processed files at {files_processed}")

        except Exception as e:
            print(f"file not fully processed: {file_path}")
            print(f"Error details: {str(e)}")

            # Move the file to the "notprocessed" folder
            destination_path = os.path.join(folder_path_not_processed, os.path.basename(file_path))
            shutil.move(file_path, destination_path)

    # Flush the data
    await datastore.flush()

    print(f"Flushed and saved processed files at {files_processed}")

    # Save the updated list of processed file paths to the JSON file
    with open(processed_file_name, 'w') as json_file:
        json.dump(processed_files, json_file)
        
        

async def main():
    global datastore
    datastore = await get_datastore()

    # Parse the command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--collection_name", required=True, help="The name of the Milvus collection.")
    parser.add_argument("--partition_name", required=True, help="The name of the Milvus partition.")
    parser.add_argument("--sbert_model_name", default='sentence-transformers/multi-qa-MiniLM-L6-cos-v1', help="The name of the SentenceTransformer model.")
    parser.add_argument("--folder_path", required=True, help="The path to the folder containing files to be processed.")
    parser.add_argument("--folder_path_not_processed", required=True, help="The path to the folder where unprocessed files will be moved.")
    parser.add_argument("--processed_file_name", required=True, help="The name of the file where processed files will be listed.")
    parser.add_argument("--files_processed_save_max", default=100, type=int, help="Steps to flush processed data.")
    
    args = parser.parse_args()

    # Get the arguments
    collection_name = args.collection_name
    partition_name = args.partition_name
    sbert_model_name = args.sbert_model_name
    folder_path = args.folder_path
    folder_path_not_processed = args.folder_path_not_processed
    processed_file_name = args.processed_file_name
    files_processed_save_max = args.files_processed_save_max

    # Call the insert_data_into_milvus function
    await insert_data_json_into_milvus(
        collection_name,
        partition_name,
        sbert_model_name,
        folder_path,
        folder_path_not_processed,
        processed_file_name,
        files_processed_save_max
    )

    # If you have other asynchronous tasks, put them here
    # For example: await some_async_function()

if __name__ == "__main__":
    asyncio.run(main())
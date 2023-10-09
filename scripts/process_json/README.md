## Process a JSON File

process_json.py

This script serves as an interface for bulk processing and indexing of documents, specifically designed to work with the Milvus vector database. It is part of a larger system designed for XML Data Extraction & Transformation.
Key Features:

    Asynchronous Data Insertion: The script uses Python's asyncio library to perform asynchronous tasks, making it efficient for handling large sets of documents.

    Sentence Embedding: Utilizes the SentenceTransformer library to convert document text into vector embeddings, which are then inserted into Milvus for similarity search.

    Data Cleaning: Truncates and cleans various metadata fields (e.g., date, keywords, author, title, abstract, and category) to ensure they fit into designated sizes.

    Batch Processing: Enables bulk processing by walking through a folder containing the data files, thereby automating the indexing process.

    Fault Tolerance: In case of errors, the script moves unprocessed files to a separate folder for future review.

    Flush Control: Flushing of the processed data to disk is controlled by a configurable step-size, allowing for better memory management.



## Usage

How to Run:

The script accepts command-line arguments for specifying the Milvus collection name, partition name, SentenceTransformer model, folder paths, and other options. Use the following command to run the script:

```
python process_json.py --collection_name YOUR_COLLECTION_NAME --partition_name YOUR_PARTITION_NAME --sbert_model_name YOUR_MODEL_NAME --folder_path YOUR_FOLDER_PATH --folder_path_not_processed YOUR_UNPROCESSED_FOLDER_PATH --processed_file_name YOUR_PROCESSED_FILE_NAME

```

## Dependencies:

    Milvus
    SentenceTransformer
    langchain for LaTeX text splitting
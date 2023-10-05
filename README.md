# ChatGPT Retrieval Plugin with Milvus and Transformer 

> **Original ChatGPT Retrieval Plugin and documentation: https://github.com/openai/chatgpt-retrieval-plugin **


## Introduction

Modification of the ChatGPT Retrieval Plugin to utilize embeddings from open models like sentence-transformers and integrate with the Milvus vector database. Tailored for Quantum Gravity Research papers. The repository is organized into several directories:

| Directory                       | Description                                                                                                                |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| [`datastore`](/datastore)       | Contains the core logic for storing and querying document embeddings using various vector database providers.              |
| [`docs`](/docs)                 | Includes documentation for setting up and using the vector database |
| [`examples`](/examples)         | Provides example configurations, authentication methods, and milvus-specific examples.                                   |
| [`local_server`](/local_server) | Contains an implementation of the retrieval plugin configured for localhost testing.                                       |
| [`models`](/models)             | Contains the data models used by the plugin, such as document and metadata models.                                         |
| [`scripts`](/scripts)           | Offers scripts for processing documents.                                         |
| [`server`](/server)             | Houses the main FastAPI server implementation.                                                                             |
| [`services`](/services)         | Contains utility services for tasks like chunking and embedding.                                 |
| [`.well-known`](/.well-known)   | Stores the plugin manifest file and OpenAPI schema, which define the plugin configuration and API specification.           |

This README provides detailed information on the modifications of the ChatGPT Retrieval Plugin.

## Table of Contents

- [Quickstart](#quickstart)
- [About](#about)
  - [API Endpoints](#api-endpoints)
- [Development](#development)
  - [Milvus](#milvus)
- [Scripts](#scripts)
- [Computational Notebooks with More details](#computational-notebooks-with-more-details)

## Quickstart

See the original plugin documentation for installation and understand the plugin. 
Follow these steps to quickly set up and run the ChatGPT Retrieval Plugin with Milvus and Sentence-Transformer

1. Install Python 3.10, if not already installed. Here an example with ubuntu 20.04:
  python3 --version
  sudo apt update
  sudo apt install -y software-properties-common
  sudo add-apt-repository ppa:deadsnakes/ppa
  sudo apt update
  sudo apt install -y python3.10 python3.10-venv python3.10-dev
  python3.10 --version
  cd
  mkdir venvs
  python3.10 -m venv ~/venvs/chatgpt_retrieval
  source ~/venvs/chatgpt_retrieval/bin/activate
  cd venvs/chatgpt_retrieval/
2. Clone the repository: `git clone https://github.com/openai/chatgpt-retrieval-plugin-milvus-transformer.git`
3. Navigate to the cloned repository directory: `cd chatgpt-retrieval-plugin-milvus-transformer`
4. Install poetry: `pip install poetry`
5. Create a new virtual environment with Python 3.10: `poetry env use python3.10`
6. Activate the virtual environment: `poetry shell`
7. Install app dependencies: `poetry install`
8. Create a [bearer token](#general-environment-variables)
9. Set the required environment variables:

   ```
   export DATASTORE=milvus
   export BEARER_TOKEN=<your_bearer_token>

   # Milvus Example:
  export MILVUS_COLLECTION=QGRmemory
  export MILVUS_HOST=192.168.1.1
  export MILVUS_PORT=19530
  export MILVUS_INDEX_PARAMS='{"metric_type": "IP", "index_type": "IVF_FLAT", "params": {"nlist": 2048}}'
  export MILVUS_SEARCH_PARAMS='{"metric_type": "IP", "param": {"nprobe": 1000}, "round_decimal": -1}'


10. Run the API locally: `poetry run start`
11. Access the API documentation at `http://192.168.1.1:3333/docs` and test the API endpoints.

### Testing in ChatGPT

To test a locally hosted plugin in ChatGPT, follow these steps:

1. Run the API on localhost: `poetry run dev`
2. Follow the instructions in the [Testing a Localhost Plugin in ChatGPT](#testing-a-localhost-plugin-in-chatgpt) section of the README.

For more detailed information on setting up, developing, and deploying the ChatGPT Retrieval Plugin, refer to the full Development section below.

## About

### API Endpoints

The Retrieval Plugin is built using FastAPI, a web framework for building APIs with Python. FastAPI allows for easy development, validation, and documentation of API endpoints. Find the FastAPI documentation [here](https://fastapi.tiangolo.com/).

One of the benefits of using FastAPI is the automatic generation of interactive API documentation with Swagger UI. When the API is running locally, Swagger UI at `<local_host_url i.e. http://192.168.1.1:3333>/docs` can be used to interact with the API endpoints, test their functionality, and view the expected request and response models.

The plugin exposes the following endpoints for upserting, querying, and deleting documents from the vector database. All requests and responses are in JSON format, and require a valid bearer token as an authorization header.

- `/upsert`: This endpoint allows uploading one or more documents and storing their text and metadata in the vector database. The documents are split into chunks of around 512 tokens, each with a unique ID. The endpoint expects a list of documents in the request body, each with a `text` field, and optional fields.

- `/query`: This endpoint allows querying the vector database using one or more natural language queries and optional metadata filters. The endpoint expects a list of queries in the request body, each with a `query` and optional `filter` and `top_k` fields.

- `/delete`: This endpoint allows deleting one or more documents from the vector database using their Document_IDs. The endpoint returns a boolean indicating whether the deletion was successful.


To include custom metadata fields, edit data models (/models/models.py), and update the OpenAPI schema (/.well-known/openapi.yaml). You can update this easily by running the app locally, copying the JSON found at http://192.168.1.1:3333/sub/openapi.json, and converting it to YAML format with [Swagger Editor](https://editor.swagger.io/). Alternatively, you can replace the `openapi.yaml` file with an `openapi.json` file. Do the same in local_server.

## Development

### Milvus

[Milvus](https://milvus.io/) is an open-source, cloud-native vector database that scales to billions of vectors. It is the open-source version of Zilliz and shares many of its features, such as various indexing algorithms, distance metrics, scalar filtering, time travel searches, rollback with snapshots, multi-language SDKs, storage and compute separation, and cloud scalability. For detailed setup instructions, refer to [`/docs/providers/milvus/setup.md`](/docs/providers/milvus/setup.md).

## Scripts

The `scripts` folder contains a package with functions for XML Data Extraction & Transformation Utilities.

This is a set of utility functions designed to parse, transform, and extract data from XML files, especially those structured according to the Text Encoding Initiative (TEI) guidelines. The utilities cater to various needs, from basic text extraction to advanced metadata processing and LaTeX content conversion.
Functions Overview:

    recursive_text_extraction: Extracts all textual content from an XML element, including nested child elements.
    extract_information_from_tei: Processes a TEI-formatted XML string, extracting metadata and content, which is then transformed to LaTeX syntax.
    slugStrip: Sanitizes a string for use as a URL slug or filename, ensuring adherence to common formatting standards.
    create_file_name: Converts a title or heading into a sanitized filename, suitable for JSON files.
    extract_and_save_data_from_tei: Processes .tei.xml files from a source directory, extracting data and saving it as .json files in a destination directory.

You can use GROBID (https://github.com/kermitt2/grobid/archive/0.7.3.zip) to automatically extract structured data from scientific PDFs in nested directories. 

## Computational Notebooks with More details

https://github.com/macielamaral/computational_essays/blob/main/Tutorial_Milvus_for_LLM_Memory_Data_Processing.ipynb

https://github.com/macielamaral/computational_essays/blob/main/Tutorial_Scientific_Data_for_LLMs.ipynb
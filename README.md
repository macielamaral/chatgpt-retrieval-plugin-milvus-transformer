# ChatGPT Retrieval Plugin with Milvus and Transformer 

> **Original ChatGPT Retrieval Plugin: https://github.com/openai/chatgpt-retrieval-plugin **

Find an example video of a Retrieval Plugin that has access to the UN Annual Reports from 2018 to 2022 [here](https://cdn.openai.com/chat-plugins/retrieval-gh-repo-readme/Retrieval-Final.mp4).

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

This README provides detailed information on how to set up, develop, and deploy the ChatGPT Retrieval Plugin.

## Table of Contents

- [Quickstart](#quickstart)
- [About](#about)
  - [Plugins](#plugins)
  - [Retrieval Plugin](#retrieval-plugin)
  - [Memory Feature](#memory-feature)
  - [API Endpoints](#api-endpoints)
- [Development](#development)
  - [Setup](#setup)
  - [Milvus](#milvus)
  - [Running the API Locally](#running-the-api-locally)
  - [Testing a Localhost Plugin in ChatGPT](#testing-a-localhost-plugin-in-chatgpt)
  - [Personalization](#personalization)
  - [Authentication Methods](#authentication-methods)
- [Installing a Developer Plugin](#installing-a-developer-plugin)
- [Scripts](#scripts)

## Quickstart

Follow these steps to quickly set up and run the ChatGPT Retrieval Plugin:

1. Install Python 3.10, if not already installed.
2. Clone the repository: `git clone https://github.com/openai/chatgpt-retrieval-plugin-milvus-transformer.git`
3. Navigate to the cloned repository directory: `cd /path/to/chatgpt-retrieval-plugin-milvus-transformer`
4. Install poetry: `pip install poetry`
5. Create a new virtual environment with Python 3.10: `poetry env use python3.10`
6. Activate the virtual environment: `poetry shell`
7. Install app dependencies: `poetry install`
8. Create a [bearer token](#general-environment-variables)
9. Set the required environment variables:

   ```
   export DATASTORE=<your_datastore>
   export BEARER_TOKEN=<your_bearer_token>

   # Milvus
   export MILVUS_COLLECTION=<your_milvus_collection>
   export MILVUS_HOST=<your_milvus_host>
   export MILVUS_PORT=<your_milvus_port>
   export MILVUS_USER=<your_milvus_username>
   export MILVUS_PASSWORD=<your_milvus_password>


10. Run the API locally: `poetry run start`
11. Access the API documentation at `http://0.0.0.0:8000/docs` and test the API endpoints (make sure to add your bearer token).

### Testing in ChatGPT

To test a locally hosted plugin in ChatGPT, follow these steps:

1. Run the API on localhost: `poetry run dev`
2. Follow the instructions in the [Testing a Localhost Plugin in ChatGPT](#testing-a-localhost-plugin-in-chatgpt) section of the README.

For more detailed information on setting up, developing, and deploying the ChatGPT Retrieval Plugin, refer to the full Development section below.

## About

### Plugins

A plugin consists of:

- An API
- An API schema (OpenAPI JSON or YAML format)
- A manifest (JSON file) that defines relevant metadata for the plugin

The Retrieval Plugin already contains all of these components. Read the Chat Plugins blogpost [here](https://openai.com/blog/chatgpt-plugins), and find the docs [here](https://platform.openai.com/docs/plugins/introduction).

### Retrieval Plugin

This is a plugin for ChatGPT that enables semantic search and retrieval of personal or organizational documents. It allows users to obtain the most relevant document snippets from their data sources, such as files, notes, or emails, by asking questions or expressing needs in natural language. Enterprises can make their internal documents available to their employees through ChatGPT using this plugin.

The plugin uses sentence-transformers embeddings model to generate embeddings of document chunks, and then stores and queries them using a Milvus vector database on the backend. 

A FastAPI server exposes the plugin's endpoints for upserting, querying, and deleting documents. Users can refine their search results by using metadata filters by source, date, authors, or other criteria.

### Memory Feature

A notable feature of the Retrieval Plugin is its capacity to provide ChatGPT with memory. By utilizing the plugin's upsert endpoint, ChatGPT can save snippets from the conversation to the vector database for later reference (only when prompted to do so by the user). This functionality contributes to a more context-aware chat experience by allowing ChatGPT to remember and retrieve information from previous conversations. 

### API Endpoints

The Retrieval Plugin is built using FastAPI, a web framework for building APIs with Python. FastAPI allows for easy development, validation, and documentation of API endpoints. Find the FastAPI documentation [here](https://fastapi.tiangolo.com/).

One of the benefits of using FastAPI is the automatic generation of interactive API documentation with Swagger UI. When the API is running locally, Swagger UI at `<local_host_url i.e. http://0.0.0.0:8000>/docs` can be used to interact with the API endpoints, test their functionality, and view the expected request and response models.

The plugin exposes the following endpoints for upserting, querying, and deleting documents from the vector database. All requests and responses are in JSON format, and require a valid bearer token as an authorization header.

- `/upsert`: This endpoint allows uploading one or more documents and storing their text and metadata in the vector database. The documents are split into chunks of around 512 tokens, each with a unique ID. The endpoint expects a list of documents in the request body, each with a `text` field, and optional fields.

- `/query`: This endpoint allows querying the vector database using one or more natural language queries and optional metadata filters. The endpoint expects a list of queries in the request body, each with a `query` and optional `filter` and `top_k` fields.

- `/delete`: This endpoint allows deleting one or more documents from the vector database using their Document_IDs. The endpoint returns a boolean indicating whether the deletion was successful.


To include custom metadata fields, edit the `DocumentMetadata` and `DocumentMetadataFilter` data models [here](/models/models.py), and update the OpenAPI schema [here](/.well-known/openapi.yaml). You can update this easily by running the app locally, copying the JSON found at http://0.0.0.0:8000/sub/openapi.json, and converting it to YAML format with [Swagger Editor](https://editor.swagger.io/). Alternatively, you can replace the `openapi.yaml` file with an `openapi.json` file.

## Development

### Setup

This app uses Python 3.10, and [poetry](https://python-poetry.org/) for dependency management.

Install Python 3.10 on your machine if it isn't already installed. It can be downloaded from the official [Python website](https://www.python.org/downloads/) or with a package manager like `brew` or `apt`, depending on your system.

Clone the repository from GitHub:

```
git clone https://github.com/openai/chatgpt-retrieval-plugin-milvus-transformer.git
```

Navigate to the cloned repository directory:

```
cd /path/to/chatgpt-retrieval-plugin-milvus-transformer
```

Install poetry:

```
pip install poetry
```

Create a new virtual environment that uses Python 3.10:

```
poetry env use python3.10
poetry shell
```

Install app dependencies using poetry:

```
poetry install
```

**Note:** If adding dependencies in the `pyproject.toml`, make sure to run `poetry lock` and `poetry install`.

### Milvus

[Milvus](https://milvus.io/) is an open-source, cloud-native vector database that scales to billions of vectors. It is the open-source version of Zilliz and shares many of its features, such as various indexing algorithms, distance metrics, scalar filtering, time travel searches, rollback with snapshots, multi-language SDKs, storage and compute separation, and cloud scalability. For detailed setup instructions, refer to [`/docs/providers/milvus/setup.md`](/docs/providers/milvus/setup.md).

### Running the API locally

To run the API locally, you first need to set the requisite environment variables with the `export` command:

```
export DATASTORE=<your_datastore>
export BEARER_TOKEN=<your_bearer_token>
<Add the environment variables for your chosen vector DB here>
```

Start the API with:

```
poetry run start
```

Append `docs` to the URL shown in the terminal and open it in a browser to access the API documentation and try out the endpoints (i.e. http://0.0.0.0:8000/docs). Make sure to enter your bearer token and test the API endpoints.

**Note:** If you add new dependencies to the pyproject.toml file, you need to run `poetry lock` and `poetry install` to update the lock file and install the new dependencies.

### Testing a Localhost Plugin in ChatGPT

To test a localhost plugin in ChatGPT, use the provided [`local_server/main.py`](/local_server/main.py) file, which is specifically configured for localhost testing with CORS settings, no authentication and routes for the manifest, OpenAPI schema and logo.

Follow these steps to test your localhost plugin:

1. Run the localhost server using the `poetry run dev` command. This starts the server at the default address (e.g. `localhost:3333`).

2. Visit [ChatGPT](https://chat.openai.com/), select "Plugins" from the model picker, click on the plugins picker, and click on "Plugin store" at the bottom of the list.

3. Choose "Develop your own plugin" and enter your localhost URL (e.g. `localhost:3333`) when prompted.

4. Your localhost plugin is now enabled for your ChatGPT session.

For more information, refer to the [OpenAI documentation](https://platform.openai.com/docs/plugins/getting-started/openapi-definition).

### Personalization

You can personalize the Retrieval Plugin for your own use case by doing the following:

- **Replace the logo**: Replace the image in [logo.png](/.well-known/logo.png) with your own logo.

- **Edit the data models**: Edit the `DocumentMetadata` and `DocumentMetadataFilter` data models in [models.py](/models/models.py) to add custom metadata fields. Update the OpenAPI schema in [openapi.yaml](/.well-known/openapi.yaml) accordingly. To update the OpenAPI schema more easily, you can run the app locally, then navigate to `http://0.0.0.0:8000/sub/openapi.json` and copy the contents of the webpage. Then go to [Swagger Editor](https://editor.swagger.io/) and paste in the JSON to convert it to a YAML format. You could also replace the [openapi.yaml](/.well-known/openapi.yaml) file with an openapi.json file in the [.well-known](/.well-known) folder.

- **Change the plugin name, description, and usage instructions**: Update the plugin name, user-facing description, and usage instructions for the model. You can either edit the descriptions in the [main.py](/server/main.py) file or update the [openapi.yaml](/.well-known/openapi.yaml) file. Follow the same instructions as in the previous step to update the OpenAPI schema.


### Authentication Methods

You can choose from four options for authenticating requests to your plugin:

1. **No Authentication**: Anyone can add your plugin and use its API without any credentials. This option is suitable if you are only exposing documents that are not sensitive or already public. It provides no security for your data. If using this method, copy the contents of this [main.py](/examples/authentication-methods/no-auth/main.py) into the [actual main.py file](/server/main.py). Example manifest [here](/examples/authentication-methods/no-auth/ai-plugin.json).

2. **HTTP Bearer**: You can use a secret token as a header to authorize requests to your plugin. There are two variants of this option:

   - **User Level** (default for this implementation): Each user who adds your plugin to ChatGPT must provide the bearer token when adding the plugin. You can generate and distribute these tokens using any tool or method you prefer, such as [jwt.io](https://jwt.io/). This method provides better security as each user has to enter the shared access token. If you require a unique access token for each user, you will need to implement this yourself in the [main.py](/server/main.py) file. Example manifest [here](/examples/authentication-methods/user-http/ai-plugin.json).

   - **Service Level**: Anyone can add your plugin and use its API without credentials, but you must add a bearer token when registering the plugin. When you install your plugin, you need to add your bearer token, and will then receive a token from ChatGPT that you must include in your hosted manifest file. Your token will be used by ChatGPT to authorize requests to your plugin on behalf of all users who add it. This method is more convenient for users, but it may be less secure as all users share the same token and do not need to add a token to install the plugin. Example manifest [here](/examples/authentication-methods/service-http/ai-plugin.json).

3. **OAuth**: Users must go through an OAuth flow to add your plugin. You can use an OAuth provider to authenticate users who add your plugin and grant them access to your API. This method offers the highest level of security and control, as users authenticate through a trusted third-party provider. However, you will need to implement the OAuth flow yourself in the [main.py](/server/main.py) file and provide the necessary parameters in your manifest file. Example manifest [here](/examples/authentication-methods/oauth/ai-plugin.json).

Consider the benefits and drawbacks of each authentication method before choosing the one that best suits your use case and security requirements. If you choose to use a method different to the default (User Level HTTP), make sure to update the manifest file [here](/.well-known/ai-plugin.json).

## Installing a Developer Plugin

To install a developer plugin, follow the steps below:

- First, create your developer plugin by deploying it to your preferred hosting platform (e.g. Fly.io, Heroku, etc.) and updating the plugin URL in the manifest file and OpenAPI schema.

- Go to [ChatGPT](https://chat.openai.com/) and select "Plugins" from the model picker.

- From the plugins picker, scroll to the bottom and click on "Plugin store."

- Go to "Develop your own plugin" and follow the instructions provided. You will need to enter the domain where your plugin is deployed.

- Follow the instructions based on the authentication type you have chosen for your plugin (e.g. if your plugin uses Service Level HTTP, you will have to paste in your access token, then paste the new access token you receive from the plugin flow into your [ai-plugin.json](/.well-known/ai-plugin.json) file and redeploy your app).

- Next, you must add your plugin. Go to the "Plugin store" again and click on "Install an unverified plugin."

- Follow the instructions provided, which will require you to enter the domain where your plugin is deployed.

- Follow the instructions based on the authentication type you have chosen for your plugin (e.g. if your plugin uses User Level HTTP, you will have to paste in your bearer token).

After completing these steps, your developer plugin should be installed and ready to use in ChatGPT.

## Scripts

The `scripts` folder contains a package with functions for XML Data Extraction & Transformation Utilities

This is a set of utility functions designed to parse, transform, and extract data from XML files, especially those structured according to the Text Encoding Initiative (TEI) guidelines. The utilities cater to various needs, from basic text extraction to advanced metadata processing and LaTeX content conversion.
Functions Overview:

    recursive_text_extraction: Extracts all textual content from an XML element, including nested child elements.
    extract_information_from_tei: Processes a TEI-formatted XML string, extracting metadata and content, which is then transformed to LaTeX syntax.
    slugStrip: Sanitizes a string for use as a URL slug or filename, ensuring adherence to common formatting standards.
    create_file_name: Converts a title or heading into a sanitized filename, suitable for JSON files.
    extract_and_save_data_from_tei: Processes .tei.xml files from a source directory, extracting data and saving it as .json files in a destination directory.

You can use GROBID (https://github.com/kermitt2/grobid/archive/0.7.3.zip) to automatically extract structured data from scientific PDFs in nested directories. 
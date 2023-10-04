import json
import os
import asyncio
import ast

from loguru import logger
from typing import Dict, List, Optional
from pymilvus import (
    Collection,
    connections,
    utility,
    FieldSchema,
    DataType,
    CollectionSchema,
    MilvusException,
)
from uuid import uuid4


from datastore.datastore import DataStore
from models.models import (
    DocumentChunk,
    DocumentChunkMetadata,
    Partition,
    SearchPrecision,
    DocumentMetadataFilter,
    QueryResult,
    QueryWithEmbedding,
    DocumentChunkWithScore,
)


MILVUS_COLLECTION = os.environ.get("MILVUS_COLLECTION") or "c" + uuid4().hex
MILVUS_HOST = os.environ.get("MILVUS_HOST") or "localhost"
MILVUS_PORT = os.environ.get("MILVUS_PORT") or 19530
MILVUS_USER = os.environ.get("MILVUS_USER")
MILVUS_PASSWORD = os.environ.get("MILVUS_PASSWORD")
MILVUS_USE_SECURITY = False if MILVUS_PASSWORD is None else True

MILVUS_INDEX_PARAMS = json.loads(os.environ.get("MILVUS_INDEX_PARAMS", '{}'))
MILVUS_SEARCH_PARAMS = json.loads(os.environ.get("MILVUS_SEARCH_PARAMS", '{}'))
MILVUS_CONSISTENCY_LEVEL = os.environ.get("MILVUS_CONSISTENCY_LEVEL")

#UPSERT_BATCH_SIZE = 100
OUTPUT_DIM = 384
EMBEDDING_FIELD = "content_vector"
MILVUS_COLLECTION_PARTITIONS = ['mypapers', 'papers', 'notes', 'books', 'others', 'chats']
MILVUS_COLLECTION_PARTITION = "chats"

class Required:
    pass


# The fields names that we are going to be storing within Milvus, the field declaration for schema creation, and the default value
SCHEMA_V3 = [
    (
        "id",
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        Required,
    ),
    (
        "documentId",
        FieldSchema(name="documentId", dtype=DataType.VARCHAR, max_length=256),
        "",
    ),
    (
        "title",
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=1024),
        "",
    ),
    (
        "date",
        FieldSchema(name="date", dtype=DataType.VARCHAR, max_length=256),
        "",
    ),
    (
        "authors",
        FieldSchema(name="authors", dtype=DataType.VARCHAR, max_length=1024),
        "",
    ),
    (
        "abstract",
        FieldSchema(name="abstract", dtype=DataType.VARCHAR, max_length=4096),
        "",
    ),
    (
        "keywords",
        FieldSchema(name="keywords", dtype=DataType.VARCHAR, max_length=1024),
        "",
    ),
    (
        "category",
        FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=256),
        "",
    ),
        (
        "content",
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=1024),
        Required,
    ),
    (
        "content_vector",
        FieldSchema(name="content_vector", dtype=DataType.FLOAT_VECTOR, dim=OUTPUT_DIM),
        Required,
    ),
]

class MilvusDataStore(DataStore):
    def __init__(
        self,
        create_new: Optional[bool] = False,
        consistency_level: str = "Bounded",
    ):
        """Create a Milvus DataStore.

        The Milvus Datastore allows for storing your indexes and metadata within a Milvus instance.

        Args:
            create_new (Optional[bool], optional): Whether to overwrite if collection already exists. Defaults to True.
            consistency_level(str, optional): Specify the collection consistency level.
                                                Defaults to "Bounded" for search performance.
                                                Set to "Strong" in test cases for result validation.
        """
        # Overwrite the default consistency level by MILVUS_CONSISTENCY_LEVEL
        self._consistency_level = MILVUS_CONSISTENCY_LEVEL or consistency_level
        self._create_connection()

        self._create_collection(MILVUS_COLLECTION, create_new)  # type: ignore
        self._create_index()

    def _get_schema(self):
        return SCHEMA_V3
    
    def _create_connection(self):
        try:
            self.alias = ""
            # Check if the connection already exists
            for x in connections.list_connections():
                addr = connections.get_connection_addr(x[0])
                if x[1] and ('address' in addr) and (addr['address'] == "{}:{}".format(MILVUS_HOST, MILVUS_PORT)):
                    self.alias = x[0]
                    logger.info("Reuse connection to Milvus server '{}:{}' with alias '{:s}'"
                                     .format(MILVUS_HOST, MILVUS_PORT, self.alias))
                    break

            # Connect to the Milvus instance using the passed in Environment variables
            if len(self.alias) == 0:
                self.alias = uuid4().hex
                connections.connect(
                    alias=self.alias,
                    host=MILVUS_HOST,
                    port=MILVUS_PORT,
                    user=MILVUS_USER,  # type: ignore
                    password=MILVUS_PASSWORD,  # type: ignore
                    secure=MILVUS_USE_SECURITY,
                )
                logger.info("Create connection to Milvus server '{}:{}' with alias '{:s}'"
                                 .format(MILVUS_HOST, MILVUS_PORT, self.alias))
        except Exception as e:
            logger.error("Failed to create connection to Milvus server '{}:{}', error: {}"
                            .format(MILVUS_HOST, MILVUS_PORT, e))

    def _create_collection(self, collection_name, create_new: bool) -> None:
        """Create a collection based on environment and passed in variables.

        Args:
            create_new (bool): Whether to overwrite if collection already exists.
        """
        try:
            self._schema_ver = "V3"
            # If the collection exists and create_new is True, drop the existing collection
            if utility.has_collection(collection_name, using=self.alias) and create_new:
                utility.drop_collection(collection_name, using=self.alias)

            # Check if the collection doesnt exist
            if utility.has_collection(collection_name, using=self.alias) is False:
                # If it doesnt exist use the field params from init to create a new schem
                schema = [field[1] for field in SCHEMA_V3]
                schema = CollectionSchema(schema)
                # Use the schema to create a new collection
                self.col = Collection(
                    collection_name,
                    schema=schema,
                    using=self.alias,
                    consistency_level=self._consistency_level,
                )

                # Create the partitions
                for partition_name in MILVUS_COLLECTION_PARTITIONS:
                    self.col.create_partition(partition_name)

                self._schema_ver = "V3"
                logger.info("Create Milvus collection '{}' with schema {} and consistency level {}"
                                 .format(collection_name, self._schema_ver, self._consistency_level))
            else:
                # If the collection exists, point to it
                self.col = Collection(
                    collection_name, using=self.alias
                )  # type: ignore
                # Which sechma is used
                self._schema_ver = "V3"
                for field in self.col.schema.fields:
                    if field.name == "id" and field.is_primary:
                        self._schema_ver = "V3"
                        break
                logger.info("Milvus collection '{}' already exists with schema {}"
                                 .format(collection_name, self._schema_ver))
        except Exception as e:
            logger.error("Failed to create collection '{}', error: {}".format(collection_name, e))

    def _create_index(self):
        # TODO: verify index/search params passed by os.environ
        self.index_params = MILVUS_INDEX_PARAMS or None
        self.search_params = MILVUS_SEARCH_PARAMS or None
        try:
            # If no index on the collection, create one
            if len(self.col.indexes) == 0:
                if self.index_params is not None:
                    # Convert the string format to JSON format parameters passed by MILVUS_INDEX_PARAMS
                    self.index_params = json.loads(self.index_params)
                    logger.info("Create Milvus index: {}".format(self.index_params))
                    # Create an index on the 'embedding' field with the index params found in init
                    self.col.create_index(EMBEDDING_FIELD, index_params=self.index_params)
                else:
                    # If no index param supplied, to first create an HNSW index for Milvus
                    try:
                        i_p = {
                            "metric_type": "IP",
                            "index_type": "IVF_FLAT",
                            "params": {"nlist": 2048},
                        }
                        logger.info("Attempting creation of Milvus '{}' index".format(i_p["index_type"]))
                        self.col.create_index(EMBEDDING_FIELD, index_params=i_p)
                        self.index_params = i_p
                        logger.info("Creation of Milvus '{}' index successful".format(i_p["index_type"]))
                    # If create fails, most likely due to being Zilliz Cloud instance, try to create an AutoIndex
                    except MilvusException:
                        logger.info("Attempting creation of Milvus default index")
                        i_p = {"metric_type": "IP", "index_type": "IVF_FLAT", "params": {"nlist": 2048}}
                        self.col.create_index(EMBEDDING_FIELD, index_params=i_p)
                        self.index_params = i_p
                        logger.info("Creation of Milvus default index successful")
            # If an index already exists, grab its params
            else:
                # How about if the first index is not vector index?
                for index in self.col.indexes:
                    idx = index.to_dict()
                    if idx["field"] == EMBEDDING_FIELD:
                        logger.info("Index already exists: {}".format(idx))
                        self.index_params = idx['index_param']
                        break

            self.col.load()

            if self.search_params is None:
                # The default search params
                self.search_params = {
                        "metric_type": "IP",
                        "param": {"nprobe": 1000},
                        "round_decimal": -1
                    }
            logger.info("Milvus search parameters: {}".format(self.search_params))
        except Exception as e:
            logger.error("Failed to create index, error: {}".format(e))
            
    async def _upsert(self, document_chunks: Dict[str, List[DocumentChunk]]) -> Dict[str, Dict[str, str]]:
        try:
            
            # The doc id's to return for the upsert
            document_ids_count: Dict[str, Dict[str, str]] = {}

            # Prepare data for insertion
            for document_id, chunk_list in document_chunks.items():
                insert_count = 0
                for chunk in chunk_list:
                    documentId_value = document_id
                    title_value = chunk.metadata.title or "Unknown"
                    date_value = chunk.metadata.created_at or "Unknown"
                    author_value = chunk.metadata.authors or "Unknown"
                    abstract_value = chunk.metadata.abstract or "Unknown"
                    keywords_value = chunk.metadata.keywords or "Unknown"
                    category_value = chunk.metadata.category or "Unknown"
                    embeddingElement = chunk.text
                    content_vector_element = chunk.embedding


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

                    # Insert the data directly
                    insert_result = self.col.insert(data=doc, partition_name=chunk.partition)
                    insert_count += 1

                    if not insert_result:
                        logger.error(f"Failed to insert document with title: {title_value} and content: {embeddingElement}")
                    else:
                        self.col.flush()  # Flush the data to ensure it's persisted
                # Append the doc_id to the list we are returning
                document_ids_count[document_id] = {"count": str(insert_count)}

            return document_ids_count
        except Exception as e:
            logger.error("Failed to insert records, error: {}".format(e))
            return []


    async def _query(
        self,
        queries: List[QueryWithEmbedding],
    ) -> List[QueryResult]:
        """Query the QueryWithEmbedding against the MilvusDocumentSearch

        Search the embedding and its filter in the collection.

        Args:
            queries (List[QueryWithEmbedding]): The list of searches to perform.

        Returns:
            List[QueryResult]: Results for each search.
        """
        # Async to perform the query, adapted from pinecone implementation
        async def _single_query(query: QueryWithEmbedding) -> QueryResult:
            try:
                # Initialize default search parameters if not set
                if not self.search_params:
                    self.search_params = {
                        "metric_type": "IP",
                        "param": {"nprobe": 1000},
                        "round_decimal": -1
                    }

                
                # Set the filter to expression that is valid for Milvus
                # Given the query object, extract the filter
                filter_object = query.filter  # This will extract the filter from the query

                # Initialize an empty list to store individual filter expressions
                expressions = []

                # Check if document_id is set and add its expression
                document_id = getattr(filter_object, "document_id", None)
                if document_id:
                    expressions.append(f"documentId == '{document_id}'")

                # Check if authors is set and add its expression
                # Here, assuming authors is a single string. If it's a list, the logic would be different.
                authors = getattr(filter_object, "authors", None)
                if authors:
                    expressions.append(f"authors == '{authors}'")

                # Combine individual expressions with "AND" operator to get the final filter expression
                filter_expr = " AND ".join(expressions)

                # If no filter fields are set, set filter_expr to None
                filter_expr = filter_expr if expressions else None


                
                # set partition
                partition_names = None

                #  partition name
                partition_name = query.partition or MILVUS_COLLECTION_PARTITION
                if partition_name:
                    partition_names = [partition_name]

                
                #new functionality to have frexible search
                if query.searchprecision == SearchPrecision.low:
                    limit_value = query.top_k * 20
                elif query.searchprecision == SearchPrecision.medium:
                    limit_value = query.top_k * 10
                else:
                    limit_value = query.top_k
                    
                
                # Perform our search
                res = self.col.search(
                    [query.embedding],  # Embedding from QueryWithEmbedding
                    "content_vector",
                    param=self.search_params,
                    output_fields=["documentId", "title", "date", "authors", "abstract", "keywords", "category", "content"],
                    limit=limit_value,  
                    expr=filter_expr,  # Milvus filter expression
                    partition_names=partition_names
                )


                if not res:
                    return QueryResult(query=query.query, results=[])


                
                # Directly use res[0] for the results
                sorted_results = sorted(res[0], key=lambda x: x.score, reverse=True)

                results = []
                # Parse every result from the sorted results
                for hit in sorted_results:
                    # Extracting document details
                    doc_id = hit.id
                    score = hit.score
                    entity = hit.entity
                    
                    title = entity.title
                    date = entity.date
                    authors = entity.authors
                    abstract = entity.abstract
                    keywords = entity.keywords
                    category = entity.category
                    contents = entity.content
                    documentId = entity.documentId
                    
                    # Creating metadata dictionary
                    metadata = {
                        "created_at": date,
                        "authors": authors,
                        "title": title,
                        "abstract": abstract,
                        "keywords": keywords,
                        "category": category,
                        "document_id": documentId
                    }

                    chunk = DocumentChunkWithScore(
                        id=doc_id,
                        text=contents,
                        partition=query.partition or None,
                        metadata=DocumentChunkMetadata(**metadata),
                        score=score,
                    )

                    results.append(chunk)

                return QueryResult(query=query.query, results=results)

            except Exception as e:
                logger.error("Failed to query, error: {}".format(e))
                return QueryResult(query=query.query, results=[])

        results: List[QueryResult] = await asyncio.gather(
            *[_single_query(query) for query in queries]
        )
        return results

    async def _delete(
        self,
        documentIds: List[str],
    ) -> bool:
        """Delete the entities based on documentId.

        Args:
            documentIds List[str]: The documentIds to delete. 
        """

        delete_count = 0  # Count of total deleted records (chunks)
        try:
            for document_id_to_search in documentIds:
                # Step 1: Search for the documentId to get the primary key (id)
                search_results = self.col.query(f"documentId == '{document_id_to_search}'")

                # Step 2: Extract the primary keys from the search results
                primary_keys_to_delete = [result['id'] for result in search_results]

                # Check if there are primary keys to delete
                if primary_keys_to_delete:
                    # Step 3: Delete the entities using the primary keys
                    delete_expr = f"id in {primary_keys_to_delete}"
                    self.col.delete(delete_expr)
                    delete_count += len(primary_keys_to_delete)

        except Exception as e:
            #logger.error("Failed to delete by ids, error: {}".format(e))
            return False  # Indicate that the delete operation failed

        logger.info("{:d} records deleted".format(delete_count))

        if delete_count > 0:
            # This setting performs flushes after delete. Small delete == bad to use
            self.col.flush()
            return True  # Indicate that the delete operation succeeded
        else:
            #logger.error("Failed to delete by ids")
            return False

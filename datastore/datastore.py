from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
import asyncio
import random

from models.models import (
    Document,
    DocumentChunk,
    DocumentMetadataFilter,
    Query,
    QueryGroupResult,
    QueryWithEmbedding,
    SearchPrecision,
    DocumentDelete
)

from services.data_processing import get_embeddings, get_document_chunks


#default values
MODEL_SEARCH_SIZE = 5

#import qgr_data_processing as qgr

class DataStore(ABC):
    async def upsert(
        self, documents: List[Document], chunk_token_size: Optional[int] = 512
    ) -> Dict[str, Dict[str, str]]:
        """
            Takes in a list of documents and inserts them into the database.
        """

        document_chunks = get_document_chunks(documents, chunk_token_size)
        
        response = await self._upsert(document_chunks)
    
        return response or {"document_id": {}, "message": "Nothing processed."}

    
    async def query(self, queries: List[Query]) -> List[QueryGroupResult]:
        """
        Takes in a list of queries and filters and returns a list of query results with matching document chunks and scores.
        """
        # get a list of of just the queries from the Query list
        query_texts = [query.query for query in queries]
        query_embeddings = get_embeddings(query_texts)
        
        # hydrate the queries with embeddings
        queries_with_embeddings = [
            QueryWithEmbedding(**query.dict(), embedding=embedding)
            for query, embedding in zip(queries, query_embeddings)
        ]
        response = await self._query(queries_with_embeddings)
    
                        
        def truncate_results(results, size, precision):
            """Helper function to truncate results based on precision."""
            if precision == SearchPrecision.low or precision == SearchPrecision.medium:
                return random.sample(results, min(size, len(results)))
            else:
                return results[:size]

        num_queries = len(response)

        if num_queries == 1:
            response[0].results = truncate_results(
                response[0].results, MODEL_SEARCH_SIZE, queries[0].searchprecision
            )
        elif num_queries == 2:
            response[0].results = truncate_results(
                response[0].results, MODEL_SEARCH_SIZE - 2, queries[0].searchprecision
            )
            response[1].results = truncate_results(
                response[1].results, MODEL_SEARCH_SIZE - 2, queries[1].searchprecision
            )
        else:
            for i, r in enumerate(response):
                r.results = truncate_results(r.results, 1, queries[i].searchprecision)


        def process_query_results(query_results):
            grouped_results = []
            
            for query_result in query_results:
                # Dictionary to hold the grouped results by document_id
                document_groups = {}

                for result in query_result.results:
                    doc_id = result.metadata.document_id
                    if doc_id not in document_groups:
                        # Initialize a new group for this document_id
                        document_groups[doc_id] = {
                            "texts": [],
                            "document_id": doc_id,
                            "scores": [],
                            "collection": result.collection,
                            "partition": result.partition,
                            "metadata": result.metadata,
                            "embedding": result.embedding
                        }

                    # Append the text and score to the respective lists in the group
                    document_groups[doc_id]["texts"].append(result.text)
                    document_groups[doc_id]["scores"].append(result.score)

                # Convert the grouped results into the desired list format
                grouped_query_results = [value for key, value in document_groups.items()]
                grouped_results.append({
                    "query": query_result.query,
                    "results": grouped_query_results
                })

            return grouped_results

        return process_query_results(response)

    async def delete(
        self,
        documents: List[DocumentDelete]
    ) -> bool:
        """
        Removes vectors by documentId
        Returns whether the operation was successful.
        """
        return await self._delete(documents)
    
    async def raw_upsert(
            self,
            document: List[List[Any]],
            collection_name: str,
            partition_name: str
        ) -> Any:  
        """
        Insert data
        """
        return await self._raw_upsert(document, collection_name, partition_name)
    
    async def flush(
            self
        ) -> Any:  
        """
        Flush
        """
        return await self._flush()
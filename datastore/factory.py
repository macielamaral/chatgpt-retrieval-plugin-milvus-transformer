from datastore.datastore import DataStore
import os
from datastore.providers.milvus_datastore import MilvusDataStore

async def get_datastore() -> DataStore:
    return MilvusDataStore()
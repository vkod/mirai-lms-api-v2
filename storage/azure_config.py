import os
from typing import Optional
from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
from azure.core.credentials import AzureKeyCredential
import redis
from dotenv import load_dotenv

load_dotenv()

class AzureStorageConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.blob_service_client = None
        self.cosmos_client = None
        self.redis_client = None
        self.search_client = None
        
        self._init_blob_storage()
        self._init_cosmos_db()
        #self._init_redis_cache()
    
    def _init_blob_storage(self):
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            self._ensure_containers_exist()
    
    def _init_cosmos_db(self):
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")
        print(f"Cosmos Endpoint: {endpoint}, Key: {key if key else None}")
        if endpoint and key:
            self.cosmos_client = CosmosClient(url=endpoint, credential=key)
            self._ensure_database_exists()
    
    def _init_redis_cache(self):
        host = os.getenv("REDIS_HOST")
        key = os.getenv("REDIS_KEY")
        if host and key:
            self.redis_client = redis.Redis(
                host=host,
                port=6380,
                password=key,
                ssl=True,
                decode_responses=True
            )
    
    
    def _ensure_containers_exist(self):
        containers = ["digital-twins", "persona-images", "training-data", "optimized-models"]
        for container_name in containers:
            try:
                self.blob_service_client.create_container(container_name)
            except Exception:
                pass
    
    def _ensure_database_exists(self):
        try:
            database = self.cosmos_client.create_database_if_not_exists(
                id="mirai-lms"
                #offer_throughput=400
            )
            database.create_container_if_not_exists(
                id="metadata",
                partition_key={"paths": ["/partition_key"], "kind": "Hash"}
            )
            database.create_container_if_not_exists(
                id="surveys",
                partition_key={"paths": ["/lead_id"], "kind": "Hash"}
            )
        except Exception as e:
            print(f"Error ensuring Cosmos DB exists: {e}")
    
    def get_blob_container_client(self, container_name: str):
        if self.blob_service_client:
            return self.blob_service_client.get_container_client(container_name)
        return None
    
    def get_cosmos_container_client(self, container_name: str):
        if self.cosmos_client:
            database = self.cosmos_client.get_database_client("mirai-lms")
            return database.get_container_client(container_name)
        return None
    
    def get_redis_client(self):
        return self.redis_client
    
    def get_search_client(self):
        return self.search_client

azure_config = AzureStorageConfig()
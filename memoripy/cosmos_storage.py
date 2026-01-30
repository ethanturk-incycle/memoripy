import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from memoripy.storage import BaseStorage
from memoripy.memory_store import MemoryStore

load_dotenv()

def _get_cosmos_endpoint() -> str | None:
    return os.environ.get("MEMORIPY_COSMOS_ENDPOINT", None)

def _get_cosmos_key() -> str | None:
    return os.environ.get("MEMORIPY_COSMOS_KEY", None)

def _get_cosmos_database() -> str:
    return os.environ.get("MEMORIPY_COSMOS_DATABASE", "memoripy")

def _get_cosmos_container() -> str:
    return os.environ.get("MEMORIPY_COSMOS_CONTAINER", "memory_store")

from pydantic import BaseModel

class ShortTermMemory(BaseModel):
    id: str
    prompt: str
    output: str
    timestamp: float
    access_count: int
    decay_factor: float
    embedding: list[float]
    concepts: list[str]

    def get(self, key, default):
        return getattr(self, key, default)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

class LongTermMemory(BaseModel):
    id: str
    prompt: str
    output: str
    timestamp: float
    access_count: int
    decay_factor: float
    total_score: float

    def get(self, key, default):
        return getattr(self, key, default)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

class CosmosStorage(BaseStorage):
    """
    Leverage Azure Cosmos DB for storage of memory interactions.
    """

    def __init__(self, set_id: str):
        """
        Create an instance of CosmosStorage.
        
        Args:
            set_id: A unique identifier for the memory set.
        """
        self.set_id = set_id
        
        endpoint = _get_cosmos_endpoint()
        key = _get_cosmos_key()
        
        if not endpoint or not key:
            raise ValueError(
                "Azure Cosmos DB configuration missing. "
                "Please set MEMORIPY_COSMOS_ENDPOINT and MEMORIPY_COSMOS_KEY."
            )
            
        self.client = CosmosClient(endpoint, credential=key)
        self.database_name = _get_cosmos_database()
        self.container_name = _get_cosmos_container()
        
        self.database = self.client.create_database_if_not_exists(id=self.database_name)
        
        self.container = self.database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path="/set_id"),
            offer_throughput=400
        )

    def load_history(self):
        query = "SELECT * FROM c WHERE c.set_id = @set_id"
        params = [{"name": "@set_id", "value": self.set_id}]
        
        short_term_memory = []
        long_term_memory = []
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=False
            ))
            
            for item in items:
                mem_type = item.get("type")
                if mem_type == "short_term":
                    model = ShortTermMemory(
                        id=item["id"],
                        prompt=item["prompt"],
                        output=item["output"],
                        timestamp=item["timestamp"],
                        access_count=item["access_count"],
                        decay_factor=item.get("decay_factor", 1.0),
                        embedding=item["embedding"],
                        concepts=item["concepts"]
                    )
                    short_term_memory.append(model)
                elif mem_type == "long_term":
                    model = LongTermMemory(
                        id=item["id"],
                        prompt=item["prompt"],
                        output=item["output"],
                        timestamp=item["timestamp"],
                        access_count=item["access_count"],
                        decay_factor=item.get("decay_factor", 1.0),
                        total_score=item["total_score"]
                    )
                    long_term_memory.append(model)
                    
            return short_term_memory, long_term_memory
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error loading history from Cosmos DB: {e}")
            return [], []


    def save_memory_to_history(self, memory_store: MemoryStore):
        """
        Save the current state of memory to Cosmos DB.
        Note: This implementation upserts individual memory items. 
        Items removed from MemoryStore but present in DB are currently NOT deleted.
        """
        for idx in range(len(memory_store.short_term_memory)):
            
            memory_data = memory_store.short_term_memory[idx]
            embedding = memory_store.embeddings[idx].flatten().tolist()
            concepts = list(memory_store.concepts_list[idx])
            
            item = {
                "id": memory_data["id"],
                "set_id": self.set_id,
                "type": "short_term",
                "prompt": memory_data["prompt"],
                "output": memory_data["output"],
                "timestamp": memory_store.timestamps[idx],
                "access_count": memory_store.access_counts[idx],
                "decay_factor": memory_data.get("decay_factor", 1.0),
                "embedding": embedding,
                "concepts": concepts
            }
            self.container.upsert_item(item)

        for memory in memory_store.long_term_memory:
            item = {
                "id": memory["id"],
                "set_id": self.set_id,
                "type": "long_term",
                "prompt": memory["prompt"],
                "output": memory["output"],
                "timestamp": memory["timestamp"],
                "access_count": memory["access_count"],
                "decay_factor": memory["decay_factor"],
                "total_score": memory["total_score"]
            }
            self.container.upsert_item(item)
            
        print(f"Saved interaction history to Cosmos DB for set_id: {self.set_id}")

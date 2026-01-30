import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure memoripy can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock azure.cosmos before importing memoripy.cosmos_storage
mock_azure = MagicMock()
mock_azure.cosmos = MagicMock()
sys.modules["azure"] = mock_azure
sys.modules["azure.cosmos"] = mock_azure.cosmos

from memoripy.cosmos_storage import CosmosStorage, ShortTermMemory, LongTermMemory

class TestCosmosStorage(unittest.TestCase):
    
    @patch.dict(os.environ, {
        "MEMORIPY_COSMOS_ENDPOINT": "https://example.documents.azure.com:443/",
        "MEMORIPY_COSMOS_KEY": "fake_key",
        "MEMORIPY_COSMOS_DATABASE": "test_db",
        "MEMORIPY_COSMOS_CONTAINER": "test_container"
    })
    @patch("memoripy.cosmos_storage.CosmosClient")
    def setUp(self, MockCosmosClient):
        self.mock_client = MockCosmosClient.return_value
        self.mock_database = self.mock_client.create_database_if_not_exists.return_value
        self.mock_container = self.mock_database.create_container_if_not_exists.return_value
        
        self.storage = CosmosStorage(set_id="test_user")

    def test_init(self):
        self.mock_client.create_database_if_not_exists.assert_called_with(id="test_db")
        # Check if create_container_if_not_exists is called, args might vary based on implementation details (PartitionKey)
        self.assertTrue(self.mock_database.create_container_if_not_exists.called)
        
    def test_save_memory_to_history(self):
        mock_memory_store = MagicMock()
        mock_memory_store.short_term_memory = [{
            "id": "stm1",
            "prompt": "hello",
            "output": "hi",
            "decay_factor": 0.9
        }]
        mock_memory_store.embeddings = [MagicMock()]
        mock_memory_store.embeddings[0].flatten.return_value.tolist.return_value = [0.1, 0.2]
        mock_memory_store.timestamps = [1234567890]
        mock_memory_store.access_counts = [1]
        mock_memory_store.concepts_list = [["greeting"]]
        
        mock_memory_store.long_term_memory = [{
            "id": "ltm1",
            "prompt": "deep thought",
            "output": "42",
            "timestamp": 1234567890,
            "access_count": 5,
            "decay_factor": 0.5,
            "total_score": 10.0
        }]
        
        self.storage.save_memory_to_history(mock_memory_store)
        
        # Expect 2 upsert calls
        self.assertEqual(self.mock_container.upsert_item.call_count, 2)
        
    def test_load_history(self):
        # Mock query return
        self.mock_container.query_items.return_value = [
            {
                "id": "stm1",
                "type": "short_term",
                "prompt": "hello",
                "output": "hi",
                "timestamp": 1234567890,
                "access_count": 1,
                "decay_factor": 0.9,
                "embedding": [0.1, 0.2],
                "concepts": ["greeting"]
            },
            {
                "id": "ltm1",
                "type": "long_term",
                "prompt": "deep thought",
                "output": "42",
                "timestamp": 1234567890,
                "access_count": 5,
                "decay_factor": 0.5,
                "total_score": 10.0
            }
        ]
        
        stm, ltm = self.storage.load_history()
        
        self.assertEqual(len(stm), 1)
        self.assertEqual(len(ltm), 1)
        self.assertIsInstance(stm[0], ShortTermMemory)
        self.assertIsInstance(ltm[0], LongTermMemory)
        self.assertEqual(stm[0].id, "stm1")
        self.assertEqual(ltm[0].id, "ltm1")

if __name__ == '__main__':
    unittest.main()

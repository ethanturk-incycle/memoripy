import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure memoripy can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestCosmosStorageMSI(unittest.TestCase):
    
    def setUp(self):
        # Clean up sys.modules to ensure fresh imports
        if 'memoripy.cosmos_storage' in sys.modules:
            del sys.modules['memoripy.cosmos_storage']
        if 'azure.cosmos' in sys.modules:
            del sys.modules['azure.cosmos']
        if 'azure.identity' in sys.modules:
            del sys.modules['azure.identity']

    def test_init_with_msi(self):
        # Mock azure.cosmos and azure.identity in sys.modules
        mock_cosmos_module = MagicMock()
        mock_identity_module = MagicMock()
        
        with patch.dict(sys.modules, {
            'azure.cosmos': mock_cosmos_module,
            'azure.identity': mock_identity_module
        }):
            # Setup specific mocks
            mock_client_class = mock_cosmos_module.CosmosClient
            mock_credential_class = mock_identity_module.DefaultAzureCredential
            mock_credential_instance = mock_credential_class.return_value
            
            # Import target module inside the patch context
            import memoripy.cosmos_storage
            from memoripy.cosmos_storage import CosmosStorage
            
            # Setup env vars for this test
            with patch.dict(os.environ, {
                "MEMORIPY_COSMOS_ENDPOINT": "https://example.documents.azure.com:443/",
                # Missing KEY
                "MEMORIPY_COSMOS_DATABASE": "test_db",
                "MEMORIPY_COSMOS_CONTAINER": "test_container"
            }, clear=True):
                
                storage = CosmosStorage(set_id="test_user_msi")
                
                # Verify DefaultAzureCredential was used
                mock_credential_class.assert_called_once()
                
                # Verify CosmosClient init
                mock_client_class.assert_called_with(
                    "https://example.documents.azure.com:443/",
                    credential=mock_credential_instance
                )

    def test_init_missing_endpoint(self):
         # Mock azure.cosmos
        mock_cosmos_module = MagicMock()
        
        with patch.dict(sys.modules, {
            'azure.cosmos': mock_cosmos_module,
             # azure.identity not needed here but fine to mock
            'azure.identity': MagicMock()
        }):
            import memoripy.cosmos_storage
            from memoripy.cosmos_storage import CosmosStorage

            with patch.dict(os.environ, {
                # Missing ENDPOINT
                "MEMORIPY_COSMOS_KEY": "fake_key"
            }, clear=True):
                
                with self.assertRaises(ValueError) as cm:
                    CosmosStorage(set_id="test_fail")
                self.assertIn("Please set MEMORIPY_COSMOS_ENDPOINT", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
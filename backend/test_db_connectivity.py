"""
Unit tests for db.py MongoDB connectivity

This test file verifies that db.py can properly connect to MongoDB
using configuration from config.py in the backend directory.
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add the backend directory to Python path so we can import config from there
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Try to import config from backend directory
try:
    import config
    CONFIG_AVAILABLE = True
    print(f"✓ Successfully imported config from backend directory")
    print(f"  MONGO_URI: {config.MONGO_URI[:50]}..." if hasattr(config, 'MONGO_URI') and config.MONGO_URI else "  MONGO_URI: Not set")
    print(f"  MONGO_DB: {getattr(config, 'MONGO_DB', 'Not set')}")
    print(f"  MONGO_PRODUCTS_COLLECTION: {getattr(config, 'MONGO_PRODUCTS_COLLECTION', 'Not set')}")
except ImportError as e:
    CONFIG_AVAILABLE = False
    print(f"✗ Failed to import config from backend directory: {e}")

class TestDbConnectivity(unittest.TestCase):
    """Test cases for db.py MongoDB connectivity"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.scripts_dir = os.path.join(self.backend_dir, 'scripts')
        
    def test_config_import_from_backend(self):
        """Test that config can be imported from backend directory"""
        self.assertTrue(CONFIG_AVAILABLE, "Config should be importable from backend directory")
        
        if CONFIG_AVAILABLE:
            self.assertTrue(hasattr(config, 'MONGO_URI'), "Config should have MONGO_URI")
            self.assertTrue(hasattr(config, 'MONGO_DB'), "Config should have MONGO_DB")
            self.assertTrue(hasattr(config, 'MONGO_PRODUCTS_COLLECTION'), "Config should have MONGO_PRODUCTS_COLLECTION")
    
    def test_db_import_with_backend_config(self):
        """Test that db.py can import and use config from backend directory"""
        
        # Temporarily modify sys.path to ensure scripts can find backend config
        original_path = sys.path.copy()
        
        try:
            # Ensure backend directory is in path for scripts to find config
            if self.backend_dir not in sys.path:
                sys.path.insert(0, self.backend_dir)
            
            # Clear any cached imports
            modules_to_clear = [name for name in sys.modules.keys() if 'scripts.db' in name or 'config' in name]
            for module in modules_to_clear:
                if module != 'config':  # Don't clear our main config import
                    sys.modules.pop(module, None)
            
            # Now try to import db.py
            try:
                from scripts import db
                print("✓ Successfully imported scripts.db")
                
                # Check if db module has the expected variables
                self.assertTrue(hasattr(db, 'MONGO_URI'), "db module should have MONGO_URI")
                self.assertTrue(hasattr(db, 'MONGO_DB'), "db module should have MONGO_DB")
                self.assertTrue(hasattr(db, 'MONGO_PRODUCTS_COLLECTION'), "db module should have MONGO_PRODUCTS_COLLECTION")
                
                print(f"  db.MONGO_URI: {str(db.MONGO_URI)[:50]}..." if db.MONGO_URI else "  db.MONGO_URI: None")
                print(f"  db.MONGO_DB: {db.MONGO_DB}")
                print(f"  db.MONGO_PRODUCTS_COLLECTION: {db.MONGO_PRODUCTS_COLLECTION}")
                
            except ImportError as e:
                self.fail(f"Failed to import scripts.db: {e}")
                
        finally:
            # Restore original sys.path
            sys.path[:] = original_path
    
    @unittest.skipUnless(CONFIG_AVAILABLE and hasattr(config, 'MONGO_URI') and config.MONGO_URI, 
                        "MongoDB URI not configured")
    def test_mongodb_connection(self):
        """Test actual MongoDB connection using config from backend"""
        
        if not CONFIG_AVAILABLE:
            self.skipTest("Config not available")
            
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure
            import certifi
            
            # Use config from backend directory
            mongo_uri = config.MONGO_URI
            mongo_db = getattr(config, 'MONGO_DB', 'test_db')
            
            print(f"Testing connection to: {mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri}")
            
            # Test connection
            client = MongoClient(mongo_uri, 
                               serverSelectionTimeoutMS=5000,
                               connectTimeoutMS=5000,
                               socketTimeoutMS=5000,
                               tls=True,
                               tlsCAFile=certifi.where())
            
            # Ping to verify connection
            client.admin.command('ping')
            print("✓ MongoDB connection successful")
            
            # Test database access
            db = client[mongo_db]
            collections = db.list_collection_names()
            print(f"✓ Database '{mongo_db}' accessible, collections: {collections}")
            
            client.close()
            
        except ImportError as e:
            self.skipTest(f"Required MongoDB packages not available: {e}")
        except ConnectionFailure as e:
            self.fail(f"MongoDB connection failed: {e}")
        except Exception as e:
            self.fail(f"Unexpected error during MongoDB connection test: {e}")
    
    def test_db_module_connect_function(self):
        """Test the connect_to_db function from db.py"""
        
        # Modify sys.path for this test
        original_path = sys.path.copy()
        
        try:
            if self.backend_dir not in sys.path:
                sys.path.insert(0, self.backend_dir)
            
            # Clear cached imports
            modules_to_clear = [name for name in sys.modules.keys() if 'scripts.db' in name]
            for module in modules_to_clear:
                sys.modules.pop(module, None)
            
            from scripts.db import connect_to_db
            
            # Test the connect function
            collection = connect_to_db()
            
            if config.MONGO_URI and config.MONGO_URI.strip():
                self.assertIsNotNone(collection, "connect_to_db should return a collection when URI is configured")
                print("✓ connect_to_db returned a collection object")
            else:
                self.assertIsNone(collection, "connect_to_db should return None when URI is not configured")
                print("✓ connect_to_db correctly returned None (no URI configured)")
                
        except Exception as e:
            if config.MONGO_URI and config.MONGO_URI.strip():
                self.fail(f"connect_to_db failed with configured URI: {e}")
            else:
                print(f"✓ connect_to_db appropriately failed with no URI: {e}")
                
        finally:
            sys.path[:] = original_path

def create_backend_config_if_missing():
    """Create a basic config.py in backend directory if it doesn't exist"""
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(backend_dir, 'config.py')
    
    if not os.path.exists(config_path):
        print(f"Creating basic config.py at {config_path}")
        
        config_content = '''# MongoDB Configuration for backend
# Set MONGO_URI to empty to run without MongoDB
# Or set it to a valid connection string
MONGO_URI = ""  # Set your MongoDB URI here
MONGO_DB = "LifeHackData"
MONGO_PRODUCTS_COLLECTION = "alldata"
MONGO_COLLECTION_NAME = "alldata"  # Alias for compatibility
MONGO_TASKS_COLLECTION = "tasks"
USE_CHANGE_STREAMS = False

# LLM Configuration
GROQ_API_KEY = ""  # Set your Groq API key here

# Application Categories
APP_CATEGORIES = [
    "Electronics",
    "Fashion", 
    "Home & Kitchen",
    "Health & Beauty",
    "Sports & Outdoors",
    "Books & Media",
    "Automotive",
    "Unknown"
]
'''
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
            
        print(f"✓ Created basic config.py at {config_path}")
        print("Please edit config.py to add your MongoDB URI and Groq API key")
        return True
    
    return False

if __name__ == '__main__':
    print("=" * 60)
    print("MongoDB Connectivity Test for db.py")
    print("=" * 60)
    
    # Check if backend config exists, create if missing
    config_created = create_backend_config_if_missing()
    if config_created:
        print("\n⚠️  A basic config.py was created. Please edit it with your settings before running tests again.")
        sys.exit(0)
    
    print(f"Backend directory: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Scripts directory: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts')}")
    print()
    
    # Run the tests
    unittest.main(verbosity=2)

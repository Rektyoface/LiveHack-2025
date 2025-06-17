# db.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


# Import configuration variables from config.py
try:
    from backend.scripts.config import MONGO_URI, MONGO_DB, MONGO_PRODUCTS_COLLECTION
except ImportError:
    print("Error: config.py not found or missing required variables.")
    # Set to None so the application can gracefully handle the missing config
    MONGO_URI = None
    MONGO_DB = None
    MONGO_PRODUCTS_COLLECTION = None

# Global variable to hold the collection object
products_collection = None

def connect_to_db():
    """
    Establishes a connection to the MongoDB database and returns the collection object.
    """
    global products_collection

    if MONGO_URI and MONGO_DB and MONGO_PRODUCTS_COLLECTION:
        try:
            # Create a new client and connect to the server
            client = MongoClient(MONGO_URI)
            
            # Send a ping to confirm a successful connection
            client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")

            # Get the database and collection
            db = client[MONGO_DB]
            products_collection = db[MONGO_PRODUCTS_COLLECTION]
            
            # CRUCIAL: Create the unique index for efficient lookups
            print(f"Ensuring unique index exists on collection: '{MONGO_PRODUCTS_COLLECTION}'...")
            products_collection.create_index([("source_site", 1), ("source_product_id", 1)], unique=True)
            print("Index is ready.")

            return products_collection

        except ConnectionFailure as e:
            print(f"Could not connect to MongoDB: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    else:
        print("MongoDB configuration is missing. Running in offline mode.")
        return None

# Initialize the connection when this module is imported
products_collection = connect_to_db()
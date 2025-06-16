from pymongo import MongoClient
import ssl

# Test MongoDB connection
DB_URI = "mongodb+srv://YAROUDIO:dragonhero@cluster0.fddxx8h.mongodb.net/Testrun?retryWrites=true&w=majority&appName=Cluster0"

try:
    print("Attempting to connect to MongoDB...")
    
    # Try different connection configurations
    client = MongoClient(DB_URI, 
                        serverSelectionTimeoutMS=5000,
                        tlsAllowInvalidCertificates=True)
    
    # Test the connection
    client.admin.command('ping')
    print("✅ Connected to MongoDB successfully!")
    
    # Test database access
    db = client["LifeHackData"]
    collection = db["alldata"]
    
    # List collections
    collections = db.list_collection_names()
    print(f"Available collections: {collections}")
    
    # Count documents
    count = collection.count_documents({})
    print(f"Documents in alldata collection: {count}")
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

from pymongo import MongoClient
from datetime import datetime
import json

# Test connection and create sample data for development
def test_connection_and_setup():
    """Test MongoDB connection and create sample data."""
    
    # First, let's try without SSL verification
    try:
        # Simple connection test
        DB_URI = "mongodb+srv://YAROUDIO:dragonhero@cluster0.fddxx8h.mongodb.net/Testrun?retryWrites=true&w=majority&appName=Cluster0"
        client = MongoClient(DB_URI, 
                           serverSelectionTimeoutMS=5000,
                           connectTimeoutMS=5000)
        
        client.admin.command('ping')
        print("✅ Connected successfully!")
        
        db = client["LifeHackData"] 
        collection = db["alldata"]
        
        # Insert a test product with sustainability data
        test_product = {
            "product_name": "Sony WH-1000XM5 Headphones",
            "brand_name": "Sony",
            "url": "https://shopee.sg/product/sony-headphones",
            "description": "Premium noise-cancelling headphones",
            "specifications": {
                "color": "black",
                "battery": "30 hours",
                "weight": "250g"
            },
            "eco_info": {
                "co2e": 3.5,
                "water_usage": "medium",
                "waste_generated": "medium", 
                "labor_practices": "fair",
                "certifications": ["Energy Efficient"],
                "score": 72
            },
            "scraped_at": datetime.utcnow()
        }
        
        # Check if product already exists
        existing = collection.find_one({"product_name": test_product["product_name"]})
        if not existing:
            result = collection.insert_one(test_product)
            print(f"✅ Inserted test product with ID: {result.inserted_id}")
        else:
            print("✅ Test product already exists")
            
        # Count documents
        count = collection.count_documents({})
        print(f"Total documents in collection: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection_and_setup()

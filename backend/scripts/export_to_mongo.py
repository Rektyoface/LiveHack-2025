from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Get MongoDB URI from environment
DB_URI = os.environ.get('MONGO_URI')
DB_NAME = os.environ.get('MONGO_DB', 'LifeHackData')
COLLECTION_NAME = os.environ.get('MONGO_PRODUCTS_COLLECTION', 'alldata')

def format_product_for_mongo(product_info, sustainability_data=None):
    """
    Map product info to MongoDB document with sustainability fields.
    If a field is missing, set to 'unknown' or a sensible default.
    """
    # Extract sustainability fields, default to 'unknown' if not found
    eco_info = {
        "co2e": sustainability_data.get("co2e", "unknown") if sustainability_data else "unknown",
        "water_usage": sustainability_data.get("water_usage", "unknown") if sustainability_data else "unknown",
        "waste_generated": sustainability_data.get("waste_generated", "unknown") if sustainability_data else "unknown",
        "labor_practices": sustainability_data.get("labor_practices", "unknown") if sustainability_data else "unknown",
        "certifications": sustainability_data.get("certifications", []) if sustainability_data else [],
        "score": sustainability_data.get("score", "unknown") if sustainability_data else "unknown"
    }

    doc = {
        "product_name": product_info.get("name", "unknown"),
        "brand_name": product_info.get("brand", "unknown"),
        "url": product_info.get("url", "unknown"),
        "description": product_info.get("description", "unknown"),
        "specifications": product_info.get("specifications", {}),
        "eco_info": eco_info,
        "scraped_at": datetime.utcnow()
    }
    return doc

def clean_dict(d):
    """Remove default/unknown values before export."""
    if isinstance(d, dict):
        return {k: clean_dict(v) for k, v in d.items() if v not in (None, "", "unknown", [], {})}
    return d

def export_product_to_mongo(product_info, sustainability_data=None, wait_for_llm=False):
    """
    Export a product to MongoDB database.
    
    Args:
        product_info (dict): Product information with name, brand, url, description, specifications
        sustainability_data (dict, optional): Sustainability analysis data
        wait_for_llm (bool): Whether to wait for LLM processing (default: False for production)
        
    Returns:
        tuple: (success: bool, result: dict/str)
    """
    if not DB_URI:
        return False, "MongoDB URI not configured"
        
    try:        # Add SSL configuration for MongoDB Atlas
        client = MongoClient(DB_URI, 
                           tls=True,
                           tlsAllowInvalidCertificates=False,  # Use valid certificates
                           serverSelectionTimeoutMS=10000,
                           connectTimeoutMS=10000,
                           socketTimeoutMS=10000,
                           retryWrites=True)
        
        # Test the connection
        client.admin.command('ping')
        
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        print("Connected to MongoDB!")

        # Format document
        doc = format_product_for_mongo(product_info, sustainability_data)

        # Check for existing product by (name+brand) OR exact url, AND score must exist
        query = {
            "$or": [
                {"product_name": doc["product_name"], "brand_name": doc["brand_name"]},
                {"url": doc["url"]}
            ],
            "eco_info.score": {"$ne": "unknown", "$exists": True}
        }
        existing = collection.find_one(query)
        if existing:
            print("Product already exists with sustainability score. Skipping export.")
            return True, existing
        else:
            # Remove default/unknown values before export
            clean_doc = clean_dict(doc)
            print("Exporting to database:", clean_doc)
            result = collection.insert_one(clean_doc)
            print(f"Product inserted with ID: {result.inserted_id}")
            
            if wait_for_llm:
                print("Waiting for LLM to update the product with sustainability score...")
                import time
                updated_doc = None
                for _ in range(30):  # Wait up to 30 seconds
                    updated_doc = collection.find_one({"_id": result.inserted_id, "eco_info.score": {"$ne": "unknown", "$exists": True}})
                    if updated_doc:
                        print("Product updated by LLM:", updated_doc)
                        break
                    time.sleep(1)
                
                if not updated_doc:
                    print("LLM did not update the product within the expected time.")
                    return True, {"_id": result.inserted_id, "status": "processing"}
                return True, updated_doc
            else:
                return True, {"_id": result.inserted_id, "status": "inserted"}
                
    except Exception as e:
        print("MongoDB connection failed:", e)
        return False, f"Database connection failed: {str(e)}"

def test_export(product_info, wait_for_llm=False):
    """Test export function - can be used for unit testing."""
    success, result = export_product_to_mongo(product_info, wait_for_llm=wait_for_llm)
    return success, result

if __name__ == "__main__":
    # Example usage - this can be used for testing
    # In production, this script will be imported and used by the Flask API
    
    # Example product data for testing
    test_product_info = {
        "name": "Test Product for Export",
        "brand": "Test Brand",
        "url": "https://example.com/test-product",
        "description": "Test product description",
        "specifications": {
            "color": "blue",
            "weight": "100g"
        }
    }
    
    print("Testing MongoDB export...")
    success, result = export_product_to_mongo(test_product_info, wait_for_llm=False)
    
    if success:
        print("Export successful:", result)
    else:
        print("Export failed:", result)

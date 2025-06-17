#!/usr/bin/env python3
"""
Backend API for EcoShop sustainability data

This is a simple Flask API that serves sustainability data for the EcoShop browser extension.
Now includes MongoDB Change Streams for real-time task monitoring.
"""

from flask import Flask, jsonify, request, abort, Response, stream_with_context
from flask_cors import CORS
import json
import os
import logging
import re  # Added re import
from typing import Dict, Any, List, Optional
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
# Import the cleaned export function
from scripts.export_to_mongo import export_product_to_mongo
# Import utility functions
from scripts.utils import clean_specifications, generate_sustainability_advice

# Import new modules
from watch import stream_task_changes, create_task_document, update_task_status
import config  # Import from local config.py

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ecoshop_api')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Path to ESG data file
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'esg_scores.json')

# Cache for sustainability data
sustainability_data = None

# MongoDB client initialized once for the application
mongo_client = None

def get_mongo_client():
    """Get or initialize MongoDB client."""
    global mongo_client
    
    if not mongo_client:
        try:
            # Try to connect to MongoDB if URI is provided
            if config.MONGO_URI:
                logger.info(f"Connecting to MongoDB at {config.MONGO_URI.split('@')[-1]}")
                mongo_client = MongoClient(config.MONGO_URI, 
                                        serverSelectionTimeoutMS=5000,  # Shorter timeout for testing
                                        connectTimeoutMS=5000,
                                        socketTimeoutMS=5000,
                                        tls=True,
                                        tlsAllowInvalidCertificates=False,  # Use valid certificates
                                        retryWrites=True)
                # Validate connection is working
                mongo_client.admin.command('ping')
                logger.info("MongoDB connection successful")
            else:
                logger.warning("No MongoDB URI provided, database storage disabled")
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {str(e)[:100]}... - continuing without database")
            mongo_client = None
            
    return mongo_client

def load_sustainability_data() -> List[Dict[str, Any]]:
    """Load sustainability data from MongoDB."""
    global sustainability_data
    
    # Always return empty list as we're removing local fallback
    # All data will come from MongoDB
    sustainability_data = []
    
    # Try to fetch data from MongoDB if available
    client = get_mongo_client()
    if client:
        try:
            db = client[config.MONGO_DB_NAME]
            collection = db[config.MONGO_COLLECTION_NAME]
            # Fetch brands with sustainability data
            cursor = collection.find({}, {"brand": 1, "score": 1})
            sustainability_data = list(cursor)
            logger.info(f"Loaded {len(sustainability_data)} brand records from MongoDB")
        except Exception as e:
            logger.warning(f"Could not load sustainability data from MongoDB: {str(e)}")
    else:
        logger.warning("MongoDB client not available - unable to load sustainability data")
    
    return sustainability_data

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    mongo_status = "available" if get_mongo_client() else "unavailable"
    
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'database': mongo_status
    })

@app.route('/api/brands')
def get_all_brands():
    """Get a list of all brands with their sustainability scores."""
    data = load_sustainability_data()
    
    # Return only brand names and scores
    simplified_data = [{'brand': item['brand'], 'score': item['score']} for item in data]
    
    return jsonify({
        'success': True,
        'count': len(simplified_data),
        'data': simplified_data
    })

@app.route('/api/score')
def get_brand_score():
    """Get sustainability score for a specific brand."""
    # Log the incoming request for debugging
    logger.info(f"API request received - params: {request.args}")
    
    brand_query = request.args.get('brand')
    
    if not brand_query:
        logger.warning("Missing brand parameter in request")
        return jsonify({
            'success': False,
            'error': 'Missing brand parameter'
        }), 400
    
    # Log the brand being searched
    logger.info(f"Searching for brand: {brand_query}")
    
    data = load_sustainability_data()
    # Case-insensitive search for exact or partial match
    brand_query_lower = brand_query.lower()
    
    # Create a list of known brand aliases/variations
    brand_aliases = {
        'apple': ['apple', 'apple inc', 'apple incorporated'],
        'samsung': ['samsung', 'samsung electronics'],
        'nike': ['nike', 'nike inc'],
        'adidas': ['adidas', 'adidas ag'],
        'bose': ['bose', 'bose corporation'],
        'sony': ['sony', 'sony corporation'],
        # Add more brand aliases as needed
    }
    
    # Try exact match first
    for item in data:
        if item['brand'].lower() == brand_query_lower:
            logger.info(f"Found exact match for '{brand_query}': {item['brand']}")
            return jsonify({
                'success': True,
                'data': item
            })
            
    # Check against aliases
    for item in data:
        item_brand_lower = item['brand'].lower()
        # Check if this brand has aliases
        if item_brand_lower in brand_aliases:
            if brand_query_lower in brand_aliases[item_brand_lower]:
                logger.info(f"Found alias match for '{brand_query}': {item['brand']}")
                return jsonify({
                    'success': True,
                    'data': item
                })
                
    # Then try partial match
    for item in data:
        if brand_query_lower in item['brand'].lower() or item['brand'].lower() in brand_query_lower:
            logger.info(f"Found partial match for '{brand_query}': {item['brand']}")
            return jsonify({
                'success': True,
                'data': item
            })
            # If no match found, return error since this is a production consumer extension
    logger.info(f"No match found for brand '{brand_query}' in database")
    return jsonify({
        'success': False,
        'error': f'No sustainability data available for brand: {brand_query}',
        'message': 'Brand not found in database'    }), 404

@app.route('/api/product', methods=['POST'])
def process_product():
    """Process and store detailed product information using the cleaned export logic."""
    try:
        # Get JSON data from request
        product_data = request.json
        if not product_data:
            return jsonify({
                'success': False,
                'error': 'No product data provided'
            }), 400        # Clean specifications to remove reviews/ratings
        if 'specifications' in product_data:
            product_data['specifications'] = clean_specifications(product_data['specifications'])
        
        logger.info(f"=== PRODUCT DATA RECEIVED ===")
        logger.info(f"Product Name: {product_data.get('name', 'Unknown product')}")
        logger.info(f"Brand: {product_data.get('brand', 'Unknown brand')}")
        logger.info(f"URL: {product_data.get('url', 'No URL')}")
        logger.info(f"Specifications: {product_data.get('specifications', {})}")
        logger.info(f"Details: {product_data.get('details', {})}")
        logger.info(f"Description: {product_data.get('description', {})}")
        logger.info(f"Full raw data: {json.dumps(product_data, indent=2)}")
        logger.info(f"===============================")
        
        # For testing without MongoDB, return the scraped data for analysis
        client = get_mongo_client()
        if not client:
            logger.info("MongoDB not available - returning scraped data for testing")
            
            # Create a comprehensive response showing all scraped data
            sustainability_result = {
                'brand': product_data.get('brand', 'Unknown'),
                'score': 'scraped',  # Indicate this is scraped data
                'co2e': 'analyzing',
                'waterUsage': 'analyzing', 
                'wasteGenerated': 'analyzing',
                'laborPractices': 'analyzing',
                'certainty': 'scraped_data',
                'message': f"Scraped data for {product_data.get('brand', 'this product')} - MongoDB not connected",
                'scraped_specifications': product_data.get('specifications', {}),
                'scraped_details': product_data.get('details', {}),
                'scraped_description': product_data.get('description', {}),
                'scraping_test': True
            }
            logger.info(f"=== RESPONSE BEING SENT ===")
            logger.info(f"Response data: {json.dumps(sustainability_result, indent=2)}")  
            logger.info(f"===========================")
            return jsonify({
                'success': True,
                'data': sustainability_result,
                'status': 'test_mode'
            })
        
        # Only try MongoDB export if we have a valid connection
        logger.info("MongoDB available - using database export function")
        
        # Use the cleaned export function when MongoDB is available
        success, result = export_product_to_mongo(product_data, wait_for_llm=False)
        
        if not success:
            logger.error(f"MongoDB export failed: {result}")
            return jsonify({
                'success': False,
                'error': f'Database error: {result}'
            }), 500
            
        # Check if this is an existing product with sustainability data
        if isinstance(result, dict) and 'eco_info' in result:
            logger.info("Product already exists with sustainability score. Returning existing data.")
            # Convert MongoDB eco_info to the format expected by extension
            sustainability_result = {
                'brand': result.get('brand_name', 'Unknown'),
                'score': result['eco_info'].get('score', 50),
                'co2e': result['eco_info'].get('co2e', 3.5),
                'waterUsage': result['eco_info'].get('water_usage', 'medium'),
                'wasteGenerated': result['eco_info'].get('waste_generated', 'medium'),
                'laborPractices': result['eco_info'].get('labor_practices', 'unknown'),
                'certainty': 'high',
                'message': f"Sustainability data for {result.get('brand_name', 'this brand')}"
            }
            return jsonify({
                'success': True,
                'data': sustainability_result,
                'status': 'found'
            })
        else:
            # New product inserted, needs processing
            logger.info(f"Product inserted with ID: {result.get('_id', 'unknown')}")
            
            # TODO: Here you would trigger your LLM to analyze the product
            # For now, return a "processing" status
            return jsonify({
                'success': True,
                'data': {
                    'brand': product_data.get('brand', 'Unknown'),
                    'score': 'analyzing',
                    'co2e': 'analyzing',
                    'waterUsage': 'analyzing',
                    'wasteGenerated': 'analyzing',
                    'laborPractices': 'analyzing',
                    'certainty': 'pending',
                    'message': 'Product added to database. Analyzing sustainability...'
                },
                'status': 'processing',
                'product_id': str(result.get('_id', ''))
            })
    
    except Exception as e:
        logger.exception(f"Error processing product data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/categories')
def get_categories():
    """Get sustainability data grouped by product categories."""
    data = load_sustainability_data()
    
    # Define some product categories (you would expand this based on your data)
    categories = {
        'electronics': ['Apple', 'Samsung', 'Sony', 'Dell', 'HP', 'Lenovo', 'Asus', 'Bose'],
        'fashion': ['Nike', 'Adidas', 'H&M', 'Zara', 'Uniqlo', 'Levi\'s', 'Gap'],
        'outdoor': ['Patagonia', 'The North Face', 'REI', 'Columbia', 'Arc\'teryx'],
        'home': ['IKEA', 'Crate & Barrel', 'West Elm', 'Pottery Barn', 'Wayfair'],
        'beauty': ['L\'Oreal', 'Estee Lauder', 'Sephora', 'MAC', 'Lush']
    }
    
    # Organize brands by category
    result = {}
    for category, brands in categories.items():
        result[category] = []
        for brand_name in brands:
            # Find brand data if available
            brand_data = next((item for item in data if item['brand'].lower() == brand_name.lower()), None)
            if brand_data:
                result[category].append({
                    'brand': brand_data['brand'],
                    'score': brand_data['score']
                })
    
    return jsonify({
        'success': True,
        'data': result
    })

@app.route('/api/top_brands')
def get_top_brands():
    """Get top sustainable brands."""
    data = load_sustainability_data()
    
    # Sort by score descending
    top_brands = sorted(data, key=lambda x: x.get('score', 0), reverse=True)[:10]
    
    # Return simplified data
    simplified = [{
        'brand': item['brand'],
        'score': item['score'],
        'message': item.get('message', '')
    } for item in top_brands]
    
    return jsonify({
        'success': True,
        'data': simplified
    })

def generate_recommendations(data: List[Dict[str, Any]], count: int = 2) -> List[Dict[str, Any]]:
    """Generate random recommendations from the top sustainable brands."""
    if not data:
        return []
    
    # Sort by score and take the top 10%
    sorted_data = sorted(data, key=lambda x: x.get('score', 0), reverse=True)
    top_brands = sorted_data[:max(2, len(sorted_data) // 10)]
    
    # Return the highest scoring brands
    return [{'brand': brand['brand'], 'score': brand['score']} for brand in top_brands[:count]]

@app.route('/api/analyze_score', methods=['POST'])
def analyze_score():
    """Custom endpoint to calculate sustainability score from various factors."""
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'error': 'No data provided'
        }), 400
    
    # Extract factors from request
    factors = {
        'co2e': data.get('co2e', 5.0),  # CO2 equivalent emissions (lower is better)
        'water_usage': data.get('water_usage', 5.0),  # Water usage scale 1-10 (lower is better)
        'waste': data.get('waste', 5.0),  # Waste generation scale 1-10 (lower is better)
        'labor': data.get('labor', 5.0),  # Labor practices scale 1-10 (higher is better)
        'transparency': data.get('transparency', 5.0),  # Transparency scale 1-10 (higher is better)
        'recycled_materials': data.get('recycled_materials', 0.0),  # Percentage of recycled materials
        'renewable_energy': data.get('renewable_energy', 0.0)  # Percentage of renewable energy
    }
    
    # Calculate weighted score (customize these weights based on importance)
    weights = {
        'co2e': 0.25,
        'water_usage': 0.15,
        'waste': 0.15,
        'labor': 0.2,
        'transparency': 0.1,
        'recycled_materials': 0.1,
        'renewable_energy': 0.05
    }
    
    # Transform scores so higher is always better
    transformed_scores = {
        'co2e': max(0, 10 - factors['co2e']),  # Invert scale so lower emissions = higher score
        'water_usage': max(0, 10 - factors['water_usage']),  # Invert scale
        'waste': max(0, 10 - factors['waste']),  # Invert scale
        'labor': factors['labor'],  # Already correct scale
        'transparency': factors['transparency'],  # Already correct scale
        'recycled_materials': factors['recycled_materials'] / 10,  # Convert percentage to scale
        'renewable_energy': factors['renewable_energy'] / 10  # Convert percentage to scale
    }
    
    # Calculate weighted score
    weighted_score = sum(transformed_scores[factor] * weights[factor] for factor in weights)
    
    # Scale to 0-100
    final_score = int(weighted_score * 10)
    
    # Determine rating labels
    rating = "Poor"
    if final_score >= 80:
        rating = "Excellent"
    elif final_score >= 70:
        rating = "Very Good"
    elif final_score >= 60:
        rating = "Good"
    elif final_score >= 50:
        rating = "Fair"
    
    return jsonify({
        'success': True,
        'data': {
            'score': final_score,
            'rating': rating,
            'factors': factors,
            'weights': weights,
            'advice': generate_sustainability_advice(factors)
        }
    })

@app.route('/api/mongodb/status')
def mongodb_status():
    """Check MongoDB connection status."""
    client = get_mongo_client()
    if client:
        return jsonify({
            'success': True,
            'status': 'connected',
            'database': config.MONGO_DB_NAME,
            'collections': {
                'main': config.MONGO_COLLECTION_NAME,
                'tasks': config.MONGO_TASKS_COLLECTION
            }
        })
    else:
        return jsonify({
            'success': False,
            'status': 'disconnected',
            'message': 'MongoDB connection not available'
        })

@app.route('/api/mongodb/config', methods=['POST'])
def configure_mongodb():
    """Configure MongoDB connection (admin feature)."""
    # This would typically be protected by authentication
    data = request.json
    if not data:
        return jsonify({
            'success': False, 
            'error': 'No configuration provided'
        }), 400
    
    # Write configuration to .env file if valid
    # (In production, would have proper validation and security)
    global mongo_client
    
    try:
        mongo_uri = data.get('uri')
        if not mongo_uri:
            return jsonify({
                'success': False,
                'error': 'MongoDB URI is required'
            }), 400
        
        # Test the connection
        test_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        test_client.admin.command('ping')        # If successful, update our config
        with open('.env', 'w') as env_file:
            env_file.write(f"MONGO_URI={mongo_uri}\n")
            env_file.write(f"MONGO_DB_NAME={data.get('db', config.MONGO_DB_NAME)}\n")
            env_file.write(f"MONGO_COLLECTION_NAME={data.get('collection', config.MONGO_COLLECTION_NAME)}\n")
            env_file.write(f"MONGO_TASKS_COLLECTION={data.get('tasks_collection', config.MONGO_TASKS_COLLECTION)}\n")
        
        # Reset client so it will be reinitialized with new settings
        mongo_client = None
        
        return jsonify({
            'success': True,
            'message': 'MongoDB configuration updated'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to configure MongoDB: {str(e)}'
        }), 500

@app.route('/api/contribute', methods=['POST'])
def contribute_data():
    """Endpoint for users to contribute sustainability observations."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        # In a real app, this would validate and store the data
        logger.info(f"Received contribution: {data}")
        # Store contribution in MongoDB if available
        client = get_mongo_client()
        if client:
            try:
                db = client[config.MONGO_DB]
                collection = db['contributions']
                
                # Add timestamp
                data['timestamp'] = datetime.datetime.utcnow()
                
                # Insert the document
                result = collection.insert_one(data)
                logger.info(f"Contribution stored in MongoDB with ID: {result.inserted_id}")
            except Exception as e:
                logger.error(f"Error storing contribution in MongoDB: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your contribution!'
        })
        
    except Exception as e:
        logger.error(f"Error processing contribution: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to process contribution'
        }), 500

@app.route('/api/product/<product_id>/status', methods=['GET'])
def check_product_status(product_id):
    """Check if a product has been updated with sustainability data."""
    try:        # MongoDB connection is required for production
        client = get_mongo_client()
        if not client:
            return jsonify({
                'success': False,
                'error': 'Database connection not available'
            }), 500
            
        db = client[config.MONGO_DB]
        collection = db[config.MONGO_PRODUCTS_COLLECTION]
        
        # Handle real ObjectId
        try:
            from bson import ObjectId
            query_id = ObjectId(product_id)
        except:
            return jsonify({
                'success': False,
                'error': 'Invalid product ID format'
            }), 400
        
        # Check if product has been updated with sustainability score
        updated_doc = collection.find_one({
            "_id": query_id, 
            "eco_info.score": {"$ne": "unknown", "$exists": True}
        })
        
        if updated_doc:
            logger.info(f"Product {product_id} has been updated with sustainability data")
            # Convert MongoDB eco_info to the format expected by extension
            sustainability_result = {
                'brand': updated_doc.get('brand_name', 'Unknown'),
                'score': updated_doc['eco_info'].get('score', 50),
                'co2e': updated_doc['eco_info'].get('co2e', 3.5),
                'waterUsage': updated_doc['eco_info'].get('water_usage', 'medium'),
                'wasteGenerated': updated_doc['eco_info'].get('waste_generated', 'medium'),
                'laborPractices': updated_doc['eco_info'].get('labor_practices', 'unknown'),
                'certainty': 'high',
                'message': f"Sustainability analysis complete for {updated_doc.get('brand_name', 'this product')}"
            }
            return jsonify({
                'success': True,
                'data': sustainability_result,
                'status': 'completed'
            })
        else:
            return jsonify({
                'success': True,
                'status': 'processing',
                'message': 'Still analyzing sustainability data...'
            })
    
    except Exception as e:
        logger.exception(f"Error checking product status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task document in MongoDB and return task_id for monitoring."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # MongoDB connection is required for task management
        client = get_mongo_client()
        if not client:
            return jsonify({
                'success': False,
                'error': 'Database connection not available'
            }), 500
            
        # Create task document with standardized structure
        task_doc = create_task_document(
            task_type=data.get('task_type', 'unknown'),
            product_url=data.get('product_url'),
            additional_data=data
        )
        
        # Store task in MongoDB
        db = client[config.MONGO_DB]
        tasks_collection = db[config.MONGO_TASKS_COLLECTION]
        result = tasks_collection.insert_one(task_doc)
        
        task_id = str(result.inserted_id)
        logger.info(f"Created task {task_id} for {data.get('task_type', 'unknown')}")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'Task created successfully. Monitor at /api/watch/{task_id}'
        })
        
    except Exception as e:
        logger.exception(f"Error creating task: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/watch/<task_id>')
def watch_task(task_id):
    """Stream real-time updates for a specific task using MongoDB Change Streams."""
    try:
        # Validate MongoDB connection
        client = get_mongo_client()
        if not client:
            return jsonify({
                'success': False,
                'error': 'Database connection not available'
            }), 500
        
        # Check if change streams are enabled
        if not config.USE_CHANGE_STREAMS:
            return jsonify({
                'success': False,
                'error': 'Change Streams not enabled in configuration'
            }), 501
        
        logger.info(f"Starting SSE stream for task {task_id}")
        
        # Create SSE stream using our watch helper
        def event_stream():
            try:
                for update in stream_task_changes(client, task_id):
                    yield f"data: {json.dumps(update)}\n\n"
            except Exception as e:
                logger.error(f"Error in SSE stream for task {task_id}: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            stream_with_context(event_stream()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )
        
    except Exception as e:
        logger.exception(f"Error setting up watch for task {task_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/tasks/<task_id>/status', methods=['PUT'])
def update_task_status_endpoint(task_id):
    """Update the status of a specific task."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # MongoDB connection is required
        client = get_mongo_client()
        if not client:
            return jsonify({
                'success': False,
                'error': 'Database connection not available'
            }), 500
        
        # Update task using our helper function
        success = update_task_status(
            client, 
            task_id, 
            data.get('status'), 
            data.get('data')
        )
        
        if success:
            logger.info(f"Updated task {task_id} with status: {data.get('status')}")
            return jsonify({
                'success': True,
                'message': 'Task status updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update task status'
            }), 500
            
    except Exception as e:
        logger.exception(f"Error updating task {task_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# --- MINIMAL LOGGING FOR EXTENSION REQUESTS ---
@app.before_request
def log_extension_payload():
    if request.path.startswith('/extract_and_rate') or request.path.startswith('/rate_product') or request.path.startswith('/api/score'):
        if request.is_json:
            payload = json.dumps(request.get_json(silent=True) or {}, separators=(',', ':'))
        else:
            payload = request.get_data(as_text=True).strip()
        logger.info(f'EXT PAYLOAD {request.path}: {payload[:500]}')

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all(path):
    return jsonify({"status": "ok"}), 200

@app.route('/extract_and_rate', methods=['POST'])
def extract_and_rate_product():
    """
    Main endpoint for browser extension to extract product info and rate sustainability.
    This function coordinates with the shopee_processor module for all analysis.
    """
    try:
        # Log minimal request info 
        logger.info(f'Request received: {request.path} [{request.content_type}]')
        
        # Track processing start time
        start_time = datetime.datetime.utcnow()
        
        # Import the processor module
        try:
            from scripts.shopee_processor import process_shopee_product
            from scripts.url_parser import extract_text_from_request, extract_url_from_request
            logger.info("Successfully imported processing modules")
        except ImportError as e:
            logger.error(f"Failed to import processing modules: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Backend processing modules unavailable'
            }), 500
        
        # Step 1: Parse the incoming data using dedicated parser functions
        product_url = extract_url_from_request(request)
        raw_text_content = extract_text_from_request(request)
        
        # Extract user weights if provided
        user_weights = None
        if request.content_type == 'application/json':
            data = request.get_json()
            if data and 'user_weights' in data and isinstance(data['user_weights'], dict):
                user_weights = data['user_weights']
        
        # Step 2: Validate that we have enough data to process
        if not product_url and not raw_text_content:
            logger.warning("Missing both product URL and raw text content in request")
            return jsonify({
                'success': False, 
                'error': 'Missing required data: need either product URL or text content'
            }), 400
        
        # Step 3: Process the product using the dedicated processor
        logger.info(f"Processing product - URL: {product_url or 'Not provided'}, text length: {len(raw_text_content) if raw_text_content else 0}")
        
        processed_result = process_shopee_product(
            url=product_url,
            raw_text=raw_text_content,
            user_weights=user_weights
        )
        
        # Step 4: Check results and prepare response
        if not processed_result:
            logger.warning("Product processing failed or returned no data")
            return jsonify({
                'success': False,
                'error': 'Product analysis failed - check database connection and API keys'
            }), 500
        
        # Step 5: Prepare the response to send back to the extension
        processing_time_ms = (datetime.datetime.utcnow() - start_time).total_seconds() * 1000        
        # Create the result from the processed data
        result = {
            'url': product_url,
            'brand': processed_result.get('brand', 'Unknown'),
            'name': processed_result.get('product_name', 'Unknown'),
            'category': processed_result.get('category', 'Unknown'),
            'score': processed_result.get('sustainability_score', 0),
            'breakdown': processed_result.get('sustainability_breakdown', {}),
            'processing_time_ms': processing_time_ms,
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
        }
        
        # Return the processed result
        logger.info(f"Successfully processed product: {result.get('name', 'Unknown')}")
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        logger.error(f"Error in /extract_and_rate: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'An internal server error occurred'}), 500

@app.route('/rate_product', methods=['POST'])
def rate_product():
    """Rate a product's sustainability based on various factors."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Extract factors from request
        factors = {
            'co2e': data.get('co2e', 5.0),  # CO2 equivalent emissions (lower is better)
            'water_usage': data.get('water_usage', 5.0),  # Water usage scale 1-10 (lower is better)
            'waste': data.get('waste', 5.0),  # Waste generation scale 1-10 (lower is better)
            'labor': data.get('labor', 5.0),  # Labor practices scale 1-10 (higher is better)
            'transparency': data.get('transparency', 5.0),  # Transparency scale 1-10 (higher is better)
            'recycled_materials': data.get('recycled_materials', 0.0),  # Percentage of recycled materials
            'renewable_energy': data.get('renewable_energy', 0.0)  # Percentage of renewable energy
        }
        
        # Calculate weighted score (customize these weights based on importance)
        weights = {
            'co2e': 0.25,
            'water_usage': 0.15,
            'waste': 0.15,
            'labor': 0.2,
            'transparency': 0.1,
            'recycled_materials': 0.1,
            'renewable_energy': 0.05
        }
        
        # Transform scores so higher is always better
        transformed_scores = {
            'co2e': max(0, 10 - factors['co2e']),  # Invert scale so lower emissions = higher score
            'water_usage': max(0, 10 - factors['water_usage']),  # Invert scale
            'waste': max(0, 10 - factors['waste']),  # Invert scale
            'labor': factors['labor'],  # Already correct scale
            'transparency': factors['transparency'],  # Already correct scale
            'recycled_materials': factors['recycled_materials'] / 10,  # Convert percentage to scale
            'renewable_energy': factors['renewable_energy'] / 10  # Convert percentage to scale
        }
        
        # Calculate weighted score
        weighted_score = sum(transformed_scores[factor] * weights[factor] for factor in weights)
        
        # Scale to 0-100
        final_score = int(weighted_score * 10)
        
        # Determine rating labels
        rating = "Poor"
        if final_score >= 80:
            rating = "Excellent"
        elif final_score >= 70:
            rating = "Very Good"
        elif final_score >= 60:
            rating = "Good"
        elif final_score >= 50:
            rating = "Fair"
            
        # Prepare result data
        result_data = {
            'score': final_score,
            'rating': rating,
            'factors': factors,
            'weights': weights,
            'advice': generate_sustainability_advice(factors),
            'timestamp': datetime.datetime.utcnow()
        }
        
        # Also extract any product information if available
        product_url = data.get('url')
        product_brand = data.get('brand')
        product_name = data.get('name')
        
        if product_url or product_brand or product_name:
            result_data['url'] = product_url
            result_data['brand'] = product_brand
            result_data['name'] = product_name
          # Store in MongoDB - required for production
        client = get_mongo_client()
        if client:
            try:
                db = client[config.MONGO_DB_NAME]
                collection = db[config.MONGO_COLLECTION_NAME]
                # Create identifier based on available data
                identifier = {}
                url = result_data.get('url')
                brand = result_data.get('brand')
                name = result_data.get('name')
                
                if url:
                    identifier['url'] = url
                elif brand and name:
                    identifier['brand'] = brand
                    identifier['name'] = name
                else:
                    # If no product identifiers, use request ID or timestamp
                    identifier['request_id'] = str(datetime.datetime.utcnow().timestamp())
                
                # Store in MongoDB
                update_result = collection.update_one(
                    identifier,
                    {'$set': result_data},
                    upsert=True
                )
                logger.info(f"Rating data {'updated' if update_result.matched_count else 'inserted'} in MongoDB using identifier: {identifier}")
                
                # Try to export to unified product collection if relevant
                if product_url or product_brand or product_name:
                    try:
                        product_info = {
                            'brand': product_brand,
                            'name': product_name,
                            'url': product_url
                        }
                        sustainability_data = {
                            'score': final_score,
                            'rating': rating
                        }
                        export_product_to_mongo(product_info, sustainability_data)
                        logger.info(f"Product also exported to unified collection: {product_name or product_url}")
                    except Exception as e:
                        logger.error(f"Export to unified collection failed: {e}")
                
            except Exception as e:
                logger.error(f"MongoDB operation failed: {e}")
                return jsonify({
                    'success': False, 
                    'error': f'Database storage failed: {str(e)}',
                    'data': result_data  # Still return data even if storage failed
                }), 500
        else:
            logger.error("MongoDB client not available - data cannot be stored")
            return jsonify({
                'success': False, 
                'error': 'Database connection required but not available',
                'data': result_data  # Still return data even without DB
            }), 503
        
        return jsonify({
            'success': True,
            'data': result_data
        })
    
    except Exception as e:
        logger.error(f"Error in /rate_product: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'An internal server error occurred'}), 500

if __name__ == '__main__':
    # Load data once at startup
    load_sustainability_data()
    # Check if MongoDB is available - skip for testing
    if get_mongo_client():
        logger.info("MongoDB connection established")
    else:
        logger.warning("MongoDB connection not available - running in test mode")
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
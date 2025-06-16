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
from typing import Dict, Any, List, Optional
import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Import the cleaned export function
from scripts.export_to_mongo import export_product_to_mongo

# Import new modules
from watch import stream_task_changes, create_task_document, update_task_status
import config

# Load environment variables from .env file if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    """Load sustainability data from the JSON file."""
    global sustainability_data
    
    if sustainability_data is None:
        try:
            # In production, we don't rely on local JSON files
            # This is only used for the simple brand lookup fallback endpoint
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, 'r') as f:
                    sustainability_data = json.load(f)
                logger.info(f"Loaded {len(sustainability_data)} brand records from {DATA_FILE}")
            else:
                logger.info("No local JSON file found - using database-only mode")
                sustainability_data = []
        except Exception as e:
            logger.warning(f"Could not load JSON data file: {str(e)} - using database-only mode")
            sustainability_data = []
    
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
        'message': 'Brand not found in database'
    }), 404

@app.route('/api/product', methods=['POST'])
def process_product():
    """Process and store detailed product information using the cleaned export logic."""
    try:        # Get JSON data from request
        product_data = request.json
        if not product_data:
            return jsonify({
                'success': False,
                'error': 'No product data provided'
            }), 400
        
        logger.info(f"=== PRODUCT DATA RECEIVED ===")
        logger.info(f"Product Name: {product_data.get('name', 'Unknown product')}")
        logger.info(f"Brand: {product_data.get('brand', 'Unknown brand')}")
        logger.info(f"URL: {product_data.get('url', 'No URL')}")
        logger.info(f"Specifications: {product_data.get('specifications', {})}")
        logger.info(f"Full raw data: {json.dumps(product_data, indent=2)}")
        logger.info(f"===============================")
          # For testing without MongoDB, return mock data
        client = get_mongo_client()
        if not client:
            logger.info("MongoDB not available - returning test data")
            # Return mock sustainability data for testing
            sustainability_result = {
                'brand': product_data.get('brand', 'Unknown'),
                'score': 75,  # Mock score
                'co2e': 2.5,
                'waterUsage': 'low',
                'wasteGenerated': 'low',
                'laborPractices': 'good',
                'certainty': 'high',
                'message': f"Test data for {product_data.get('brand', 'this brand')} - MongoDB not connected"
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

def generate_sustainability_advice(factors: Dict[str, float]) -> Dict[str, str]:
    """Generate specific advice based on sustainability factors."""
    advice = {}
    
    if factors['co2e'] > 7:
        advice['co2e'] = "Consider reducing carbon emissions through supply chain optimizations and renewable energy."
    
    if factors['water_usage'] > 7:
        advice['water'] = "Implement water conservation practices in manufacturing and processing."
    
    if factors['waste'] > 7:
        advice['waste'] = "Develop circular economy practices and reduce packaging waste."
    
    if factors['labor'] < 5:
        advice['labor'] = "Improve labor conditions and ensure fair wages throughout the supply chain."
    
    if factors['recycled_materials'] < 30:
        advice['materials'] = "Increase use of recycled and sustainably sourced materials."
    
    return advice

@app.route('/api/mongodb/status')
def mongodb_status():
    """Check MongoDB connection status."""
    client = get_mongo_client()
    if client:        return jsonify({
            'success': True,
            'status': 'connected',
            'database': config.MONGO_DB,
            'collections': {
                'products': config.MONGO_PRODUCTS_COLLECTION,
                'scores': config.MONGO_SCORES_COLLECTION
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
        test_client.admin.command('ping')
          # If successful, update our config
        with open('.env', 'w') as env_file:
            env_file.write(f"MONGO_URI={mongo_uri}\n")
            env_file.write(f"MONGO_DB={data.get('db', config.MONGO_DB)}\n")
            env_file.write(f"MONGO_PRODUCTS_COLLECTION={data.get('products_collection', config.MONGO_PRODUCTS_COLLECTION)}\n")
            env_file.write(f"MONGO_SCORES_COLLECTION={data.get('scores_collection', config.MONGO_SCORES_COLLECTION)}\n")
        
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
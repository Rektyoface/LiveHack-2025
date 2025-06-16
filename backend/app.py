#!/usr/bin/env python3
"""
Backend API for EcoShop sustainability data

This is a simple Flask API that serves sustainability data for the EcoShop browser extension.
It can be expanded to include more features like user accounts, data contribution, etc.
"""

from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import json
import os
import logging
from typing import Dict, Any, List, Optional

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

def load_sustainability_data() -> List[Dict[str, Any]]:
    """Load sustainability data from the JSON file."""
    global sustainability_data
    
    if sustainability_data is None:
        try:
            with open(DATA_FILE, 'r') as f:
                sustainability_data = json.load(f)
            logger.info(f"Loaded {len(sustainability_data)} brand records from {DATA_FILE}")
        except Exception as e:
            logger.error(f"Error loading sustainability data: {str(e)}")
            sustainability_data = []
    
    return sustainability_data

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0'
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
    brand_query = request.args.get('brand')
    
    if not brand_query:
        return jsonify({
            'success': False,
            'error': 'Missing brand parameter'
        }), 400
    
    data = load_sustainability_data()
    
    # Case-insensitive search for exact or partial match
    brand_query_lower = brand_query.lower()
    
    # Try exact match first
    for item in data:
        if item['brand'].lower() == brand_query_lower:
            return jsonify({
                'success': True,
                'data': item
            })
    
    # Then try partial match
    for item in data:
        if brand_query_lower in item['brand'].lower() or item['brand'].lower() in brand_query_lower:
            return jsonify({
                'success': True,
                'data': item
            })
    
    # If no match is found, return a default response
    return jsonify({
        'success': True,
        'data': {
            'brand': brand_query,
            'score': 50,  # Neutral score
            'co2e': 3.5,  # Average value
            'waterUsage': 'medium',
            'wasteGenerated': 'medium',
            'laborPractices': 'unknown',
            'certainty': 'low',
            'message': 'Limited sustainability data available for this brand',
            'alternatives': generate_recommendations(data, 2)
        }
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

@app.route('/api/categories')
def get_categories():
    """Get product categories with sustainability information."""
    # This would ideally come from a database, but for demo purposes we'll return static data
    categories = [
        {
            'id': 'fashion',
            'name': 'Fashion & Clothing',
            'avgScore': 53,
            'topBrands': ['Patagonia', 'Reformation', 'Everlane']
        },
        {
            'id': 'electronics',
            'name': 'Electronics',
            'avgScore': 62,
            'topBrands': ['Fairphone', 'Framework', 'Microsoft']
        },
        {
            'id': 'food',
            'name': 'Food & Beverages',
            'avgScore': 48,
            'topBrands': ['Dr. Bronner\'s', 'Equal Exchange', 'Seventh Generation']
        },
        {
            'id': 'home',
            'name': 'Home & Furniture',
            'avgScore': 57,
            'topBrands': ['IKEA', 'West Elm', 'Ecobirdy']
        }
    ]
    
    return jsonify({
        'success': True,
        'count': len(categories),
        'data': categories
    })

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

if __name__ == '__main__':
    # Load data once at startup
    load_sustainability_data()
    
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
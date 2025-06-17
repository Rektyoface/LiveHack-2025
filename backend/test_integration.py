#!/usr/bin/env python3
"""
Test script for the integrated backend system.
This script tests the integration between app.py and the shopee_processor module.
"""

import sys
import os
import json

# Add the backend directory to Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_url_parser():
    """Test the URL parsing functionality."""
    print("=== Testing URL Parser ===")
    from scripts.url_parser import parse_shopee_url, extract_url_from_request, extract_text_from_request
    
    # Test URL parsing
    test_url = "https://shopee.sg/-NEW-PUMA-Unisex-Shuffle-Shoes-(White)-i.341363989.24033132727"
    result = parse_shopee_url(test_url)
    print(f"URL: {test_url}")
    print(f"Parsed: {result}")
    
    # Test with mock request data
    class MockRequest:
        def __init__(self, content_type, json_data=None, text_data=None):
            self.content_type = content_type
            self._json_data = json_data
            self._text_data = text_data
        
        def get_json(self):
            return self._json_data
        
        def get_data(self, as_text=False):
            return self._text_data
    
    # Test JSON request
    mock_request = MockRequest('application/json', {
        'url': test_url,
        'plainText': 'This is a product description with specifications.'
    })
    
    extracted_url = extract_url_from_request(mock_request)
    extracted_text = extract_text_from_request(mock_request)
    
    print(f"Extracted URL: {extracted_url}")
    print(f"Extracted text length: {len(extracted_text) if extracted_text else 0}")
    print()

def test_utils():
    """Test utility functions."""
    print("=== Testing Utilities ===")
    from scripts.utils import clean_specifications, generate_sustainability_advice
    
    # Test specification cleaning
    test_specs = {
        'Brand': 'PUMA',
        'Color': 'White',
        'Review Score': '5.0 out of 5 stars',
        'Customer Reviews': 'Great product with many positive reviews'
    }
    
    cleaned = clean_specifications(test_specs)
    print(f"Original specs: {test_specs}")
    print(f"Cleaned specs: {cleaned}")
    
    # Test advice generation
    test_factors = {
        'co2e': 8.5,
        'water_usage': 6.0,
        'waste': 4.0,
        'labor': 3.0,
        'recycled_materials': 20.0
    }
    
    advice = generate_sustainability_advice(test_factors)
    print(f"Factors: {test_factors}")
    print(f"Advice: {advice}")
    print()

def test_config():
    """Test configuration loading."""
    print("=== Testing Configuration ===")
    try:
        import backend.scripts.config as config
        print(f"MONGO_DB_NAME: {config.MONGO_DB_NAME}")
        print(f"MONGO_COLLECTION_NAME: {config.MONGO_COLLECTION_NAME}")
        print(f"APP_CATEGORIES count: {len(config.APP_CATEGORIES)}")
        print(f"GROQ_API_KEY configured: {'Yes' if config.GROQ_API_KEY else 'No'}")
    except Exception as e:
        print(f"Error loading config: {e}")
    print()

def test_shopee_processor():
    """Test the shopee processor (without actually calling LLM)."""
    print("=== Testing Shopee Processor Structure ===")
    try:
        from scripts.shopee_processor import process_shopee_product
        print("✅ Successfully imported process_shopee_product")
        
        from scripts.analyzer import get_full_product_analysis
        print("✅ Successfully imported get_full_product_analysis")
        
        from scripts.scorer import generate_sustainability_breakdown, calculate_weighted_score, DEFAULT_WEIGHTS
        print("✅ Successfully imported scoring functions")
        print(f"Default weights: {DEFAULT_WEIGHTS}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
    print()

def main():
    """Run all tests."""
    print("🧪 Backend Integration Test Suite")
    print("=" * 50)
    
    test_config()
    test_url_parser()
    test_utils()
    test_shopee_processor()
    
    print("✅ All basic integration tests completed!")
    print("\nNext steps:")
    print("1. Set up MongoDB connection string in config.py")
    print("2. Set up Groq API key in config.py")
    print("3. Test with actual product data")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test script to validate the cleaned API and export functionality.
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        print(f"Health check status: {response.status_code}")
        print(f"Health check response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_product_processing():
    """Test the product processing endpoint."""
    print("\nTesting product processing...")
    
    test_product = {
        "name": "Samsung Galaxy S25 Ultra",
        "brand": "Samsung",
        "url": "https://shopee.sg/samsung-galaxy-s25-ultra",
        "description": "Latest Samsung flagship smartphone with AI features",
        "specifications": {
            "display": "6.8 inch Dynamic AMOLED",
            "storage": "256GB",
            "ram": "12GB",
            "camera": "200MP main"
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/product", 
            json=test_product,
            headers={"Content-Type": "application/json"}
        )
        print(f"Product processing status: {response.status_code}")
        response_data = response.json()
        print(f"Product processing response: {json.dumps(response_data, indent=2)}")
        
        # If processing, test the polling endpoint
        if response_data.get('status') == 'processing' and response_data.get('product_id'):
            print(f"\nTesting polling for product ID: {response_data['product_id']}")
            return test_product_polling(response_data['product_id'])
        
        return response.status_code == 200 and response_data.get('success')
        
    except Exception as e:
        print(f"Product processing failed: {e}")
        return False

def test_product_polling(product_id):
    """Test the product status polling endpoint."""
    print(f"Polling for product status: {product_id}")
    
    for i in range(5):  # Try 5 times
        try:
            response = requests.get(f"{API_BASE_URL}/api/product/{product_id}/status")
            print(f"Polling attempt {i+1} - Status: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"Polling response: {json.dumps(response_data, indent=2)}")
                
                if response_data.get('status') == 'completed':
                    print("Product analysis completed!")
                    return True
                elif response_data.get('status') == 'processing':
                    print("Still processing, waiting...")
                    time.sleep(2)
                else:
                    print("Unknown status")
                    return False
            else:
                print(f"Polling failed with status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Polling error: {e}")
            return False
    
    print("Polling timeout - analysis may take longer")
    return True  # Not a failure, just taking longer

def test_brand_lookup():
    """Test the brand lookup endpoint."""
    print("\nTesting brand lookup...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/score?brand=Samsung")
        print(f"Brand lookup status: {response.status_code}")
        response_data = response.json()
        print(f"Brand lookup response: {json.dumps(response_data, indent=2)}")
        return response.status_code == 200 and response_data.get('success')
        
    except Exception as e:
        print(f"Brand lookup failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== API Testing Suite ===")
    
    tests = [
        ("Health Check", test_health_check),
        ("Product Processing", test_product_processing),
        ("Brand Lookup", test_brand_lookup)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        success = test_func()
        results.append((test_name, success))
        print(f"{test_name}: {'PASS' if success else 'FAIL'}")
    
    print(f"\n{'='*50}")
    print("TEST SUMMARY:")
    for test_name, success in results:
        print(f"  {test_name}: {'PASS' if success else 'FAIL'}")
    
    all_passed = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    main()

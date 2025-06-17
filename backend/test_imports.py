#!/usr/bin/env python3
"""
Test script to identify which import is failing
"""

print("Testing imports...")

try:
    print("Testing db.py import...")
    from scripts.db import products_collection
    print("✓ scripts.db imported successfully")
except Exception as e:
    print(f"✗ scripts.db failed: {e}")

try:
    print("Testing analyzer.py import...")
    from scripts.analyzer import get_full_product_analysis
    print("✓ scripts.analyzer imported successfully")
except Exception as e:
    print(f"✗ scripts.analyzer failed: {e}")

try:
    print("Testing scorer.py import...")
    from scripts.scorer import generate_sustainability_breakdown
    print("✓ scripts.scorer imported successfully")
except Exception as e:
    print(f"✗ scripts.scorer failed: {e}")

try:
    print("Testing url_parser.py import...")
    from scripts.url_parser import parse_shopee_url
    print("✓ scripts.url_parser imported successfully")
except Exception as e:
    print(f"✗ scripts.url_parser failed: {e}")

try:
    print("Testing shopee_processor.py import...")
    from scripts.shopee_processor import process_shopee_product
    print("✓ scripts.shopee_processor imported successfully")
except Exception as e:
    print(f"✗ scripts.shopee_processor failed: {e}")

print("Import testing complete.")

#!/usr/bin/env python3
"""
Fetch ESG (Environmental, Social, and Governance) data from various sources
and convert it to a JSON format for the EcoShop browser extension.

This script can be run manually or scheduled to keep the sustainability data up to date.
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
import csv
from io import StringIO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fetch_esg_data')

# Default paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUTPUT_PATH = os.path.join(os.path.dirname(SCRIPT_DIR), 'data', 'esg_scores.json')
DEFAULT_BACKUP_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'data', 'backups')

# Sample data sources - replace with actual APIs in production
DATA_SOURCES = {
    'msci_esg': 'https://example.com/api/msci-esg-ratings',
    'sustainalytics': 'https://example.com/api/sustainalytics-ratings', 
    'cdp': 'https://example.com/api/cdp-climate-scores',
    'open_esg': 'https://example.com/api/open-esg-data'
}

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Fetch ESG data and convert to JSON format')
    parser.add_argument('-o', '--output', type=str, default=DEFAULT_OUTPUT_PATH,
                        help='Output path for JSON data (default: data/esg_scores.json)')
    parser.add_argument('-b', '--backup', action='store_true',
                        help='Create a backup of the existing data before overwriting')
    parser.add_argument('-s', '--source', choices=DATA_SOURCES.keys(), default=None,
                        help='Specific data source to use (default: all sources)')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Enable debug logging')
    return parser.parse_args()

def create_backup(file_path: str) -> Optional[str]:
    """Create a backup of the existing data file."""
    if not os.path.exists(file_path):
        logger.warning(f"No existing file to back up: {file_path}")
        return None
    
    os.makedirs(DEFAULT_BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(DEFAULT_BACKUP_DIR, f"esg_scores_{timestamp}.json")
    
    try:
        with open(file_path, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Backup created: {backup_file}")
        return backup_file
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return None

def fetch_data_from_source(source_name: str, api_url: str) -> List[Dict[str, Any]]:
    """Fetch data from a specific source."""
    logger.info(f"Fetching data from {source_name}...")
    
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        
        # Different handling depending on expected response format
        if source_name == 'open_esg':
            # For CSV data
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)
            return list(reader)
        else:
            # For JSON data
            return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching data from {source_name}: {str(e)}")
        return []

def generate_mock_data() -> List[Dict[str, Any]]:
    """Generate mock data for testing when APIs are unavailable."""
    logger.info("Generating mock data...")
    
    # Return the current data file if it exists
    if os.path.exists(DEFAULT_OUTPUT_PATH):
        try:
            with open(DEFAULT_OUTPUT_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading existing data: {str(e)}")
    
    # If we can't load existing data, return an empty list
    return []

def merge_and_normalize_data(data_sources: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Merge and normalize data from different sources into a unified format."""
    logger.info("Merging and normalizing data...")
    
    # Dictionary to store merged data by brand name
    merged_data = {}
    
    # Process each data source
    for source_name, source_data in data_sources.items():
        for item in source_data:
            # Skip items without brand information
            if not item.get('brand'):
                continue
            
            brand_name = item['brand'].strip()
            
            # Initialize entry if this is the first time seeing this brand
            if brand_name not in merged_data:
                merged_data[brand_name] = {
                    'brand': brand_name,
                    'score': 0,
                    'co2e': 0,
                    'waterUsage': 'unknown',
                    'wasteGenerated': 'unknown',
                    'laborPractices': 'unknown',
                    'certainty': 'low',
                    'sources': [],
                    'alternatives': []
                }
            
            # Update with source-specific data
            merged_data[brand_name]['sources'].append(source_name)
            
            # Normalize and merge each field
            if source_name == 'msci_esg' and 'rating' in item:
                # MSCI ESG ratings are from AAA to CCC
                rating_map = {'AAA': 100, 'AA': 90, 'A': 80, 'BBB': 70, 
                              'BB': 60, 'B': 50, 'CCC': 40}
                merged_data[brand_name]['score'] = rating_map.get(item['rating'], 50)
                
            elif source_name == 'sustainalytics' and 'esg_risk' in item:
                # Sustainalytics: lower risk score is better (0-40+)
                risk = float(item['esg_risk'])
                # Convert to 0-100 scale (inverted)
                score = max(0, min(100, 100 - (risk * 2.5)))
                merged_data[brand_name]['score'] = int(score)
            
            # Carbon footprint data
            if 'carbon_footprint' in item:
                merged_data[brand_name]['co2e'] = float(item['carbon_footprint'])
            
            # Water usage
            if 'water_usage' in item:
                merged_data[brand_name]['waterUsage'] = item['water_usage'].lower()
            
            # Waste
            if 'waste' in item:
                merged_data[brand_name]['wasteGenerated'] = item['waste'].lower()
            
            # Labor practices
            if 'labor_score' in item:
                labor_score = float(item['labor_score'])
                if labor_score >= 80:
                    merged_data[brand_name]['laborPractices'] = 'good'
                elif labor_score >= 50:
                    merged_data[brand_name]['laborPractices'] = 'fair'
                else:
                    merged_data[brand_name]['laborPractices'] = 'poor'
            
            # Data certainty
            if len(merged_data[brand_name]['sources']) >= 2:
                merged_data[brand_name]['certainty'] = 'high'
            elif len(merged_data[brand_name]['sources']) == 1:
                merged_data[brand_name]['certainty'] = 'medium'
    
    # Convert dictionary to list
    result = list(merged_data.values())
    
    # Sort by score in descending order
    result.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Generate alternatives based on similar product categories
    generate_alternatives(result)
    
    # Clean up internal fields
    for item in result:
        if 'sources' in item:
            del item['sources']
    
    return result

def generate_alternatives(data: List[Dict[str, Any]]) -> None:
    """Generate alternative recommendations for each brand."""
    # For a real implementation, this would consider product categories
    # For this demo, we'll just recommend higher-scoring brands
    
    # Create a copy of the data sorted by score
    sorted_data = sorted(data, key=lambda x: x.get('score', 0), reverse=True)
    
    # For each brand, suggest 2 higher-scoring alternatives
    for item in data:
        item['alternatives'] = []
        current_score = item.get('score', 0)
        
        # Find brands with higher scores
        better_alternatives = [alt for alt in sorted_data 
                               if alt.get('score', 0) > current_score 
                               and alt.get('brand') != item.get('brand')]
        
        # Take the first 2 better alternatives
        for alt in better_alternatives[:2]:
            item['alternatives'].append({
                'brand': alt.get('brand'),
                'score': alt.get('score', 0)
            })

def save_data(data: List[Dict[str, Any]], output_path: str) -> None:
    """Save the processed data to a JSON file."""
    logger.info(f"Saving data to {output_path}...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Successfully saved data: {len(data)} brand records")
    except Exception as e:
        logger.error(f"Error saving data: {str(e)}")

def main():
    """Main function to orchestrate the data fetching process."""
    args = parse_args()
    
    # Set log level
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Create a backup if requested
    if args.backup:
        create_backup(args.output)
    
    # Initialize data collections
    collected_data = {}
    
    try:
        # Determine which sources to fetch from
        sources_to_fetch = [args.source] if args.source else DATA_SOURCES.keys()
        
        # Fetch data from each source
        for source_name in sources_to_fetch:
            source_url = DATA_SOURCES.get(source_name)
            if source_url:
                source_data = fetch_data_from_source(source_name, source_url)
                if source_data:
                    collected_data[source_name] = source_data
        
        # If no data was successfully fetched, use mock data
        if not collected_data:
            logger.warning("No data fetched from sources, using mock data")
            mock_data = generate_mock_data()
            if mock_data:
                collected_data['mock'] = mock_data
        
        # Merge and normalize the collected data
        final_data = merge_and_normalize_data(collected_data)
        
        # Save the processed data
        save_data(final_data, args.output)
        
        logger.info("Data processing completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
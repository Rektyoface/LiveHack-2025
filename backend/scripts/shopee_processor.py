# ==============================================================================
# This file is the central "brain" for processing Shopee products.
# It orchestrates the entire workflow from receiving raw data to returning a
# final, scored product object.
# ==============================================================================

# --- Step 1: Import all necessary modules ---
# We import the database connection, the URL parser, the LLM analyzer,
# and all the necessary functions and constants from the scorer.

import sys
import os
import json
import logging

# Configure logging for shopee_processor
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('shopee_processor')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.db import products_collection
from scripts.url_parser import parse_shopee_url
from scripts.analyzer import get_full_product_analysis
from scripts.scorer import generate_sustainability_breakdown, calculate_weighted_score, DEFAULT_WEIGHTS


# --- Step 2: Define the main processing function ---

def process_shopee_product(url: str, raw_text: str, user_weights: dict | None = None) -> dict | None:
    """
    Orchestrates the entire process for a single Shopee product.

    Workflow:
    1. Parses the URL to get a stable, unique identifier (`listing_id`).
    2. Checks the MongoDB collection (our cache) for this `listing_id`.
    3. If CACHE HIT:
       - Retrieves the stored `sustainability_breakdown`.
       - Quickly recalculates the score using the new `user_weights`.
       - Returns the complete, personalized product document.
    4. If CACHE MISS:
       - Calls the LLM (`analyzer`) to get a structured analysis of the raw text.
       - Calls the `scorer` to generate the `sustainability_breakdown` object.
       - Calculates a `default_sustainability_score` for database storage.
       - Saves the new, lean product document to the database.
       - Returns the complete, personalized product document to the user.

    Args:
        url: The full Shopee product URL from the frontend.
        raw_text: The raw text dump of the product page from the frontend scraper.
        user_weights: An optional dictionary of the user's personalized weights.

    Returns:
        A dictionary representing the final product document, including the
        personalized score, or None if the process fails at any step.
    """
    
    logger.info("=== SHOPEE_PROCESSOR: STARTING PROCESSING ===")
    logger.info(f"Input URL: {url}")
    logger.info(f"Raw text length: {len(raw_text) if raw_text else 0}")
    logger.info(f"User weights provided: {user_weights is not None}")
    logger.info(f"Products collection available: {products_collection is not None}")
      # --- Guard Clause: Ensure database is connected ---
    if products_collection is None:
        logger.error("CRITICAL: Database is not connected. Cannot process URL.")
        return None

    # --- Step 2a: Parse URL to get unique identifiers ---
    logger.info("=== STEP 2A: PARSING URL ===")
    parsed_info = parse_shopee_url(url)
    if not parsed_info:
        logger.error(f"FAILED: Invalid or unparsable Shopee URL: {url}")
        return None
    
    logger.info(f"SUCCESS: Parsed URL -> {json.dumps(parsed_info, indent=2)}")

    # --- Step 2b: Check the database (cache) for an existing product ---
    logger.info("=== STEP 2B: CHECKING DATABASE CACHE ===")
    logger.info(f"Looking for existing product with:")
    logger.info(f"  source_site: '{parsed_info['source_site']}'")
    logger.info(f"  listing_id: '{parsed_info['listing_id']}'")
    
    existing_product = products_collection.find_one({
        "source_site": parsed_info['source_site'],
        "listing_id": parsed_info['listing_id'],
    })
    if existing_product:
        logger.info(f"CACHE HIT: Found existing product with _id: {existing_product.get('_id')}")
        logger.info(f"Existing product data: {json.dumps({k: v for k, v in existing_product.items() if k != '_id'}, indent=2, default=str)}")
    else:
        logger.info("CACHE MISS: No existing product found. Running LLM analysis...")
        
    # --- Step 3: Handle Cache Hit (The Fast Path) ---
    if existing_product:
        logger.info("=== STEP 3: CACHE HIT - FAST PATH ===")
        
        # Use the stored breakdown to perform a very fast recalculation
        logger.info("Recalculating score with user weights...")
        personalized_score = calculate_weighted_score(
            existing_product['sustainability_breakdown'], 
            user_weights
        )
        logger.info(f"Personalized score calculated: {personalized_score}")
        
        # Update the score in the document we are about to return to the user
        existing_product['sustainability_score'] = personalized_score
        
        # Clean up the document before sending it back to the API
        # The user doesn't need to see the default score or the internal _id
        if 'default_sustainability_score' in existing_product:
            del existing_product['default_sustainability_score']
        
        logger.info("SUCCESS: Process completed (CACHE HIT)")
        logger.info(f"Returning product: {json.dumps(existing_product, indent=2, default=str)}")
        return existing_product

    # --- Step 4: Handle Cache Miss (The Full Pipeline) ---
    logger.info("=== STEP 4: CACHE MISS - FULL ANALYSIS PIPELINE ===")

    # 4a. Call the LLM to analyze the raw text
    logger.info("=== STEP 4A: CALLING LLM ANALYZER ===")
    logger.info(f"Sending raw text to analyzer (length: {len(raw_text)})")
    logger.info(f"Raw text preview (first 500 chars): {raw_text[:500]}...")
    
    analysis_json = get_full_product_analysis(raw_text)
    if not analysis_json:
        logger.error("FAILED: LLM analysis returned no data")
        return None

    logger.info("SUCCESS: LLM analysis completed")
    # Safe logging with error handling for non-serializable objects
    try:
        logger.info(f"Analysis result: {json.dumps(analysis_json, indent=2)}")
    except (TypeError, ValueError) as e:
        logger.warning(f"Could not serialize analysis_json for logging: {e}")
        logger.info(f"Analysis result keys: {list(analysis_json.keys()) if isinstance(analysis_json, dict) else 'Not a dict'}")
        logger.info(f"Analysis result type: {type(analysis_json)}")

    # 4b. Convert the LLM's text analysis into our rich breakdown object    logger.info("=== STEP 4B: GENERATING SUSTAINABILITY BREAKDOWN ===")
    sustainability_breakdown = generate_sustainability_breakdown(analysis_json)
    # Safe logging with error handling for non-serializable objects
    try:
        logger.info(f"Sustainability breakdown: {json.dumps(sustainability_breakdown, indent=2)}")
    except (TypeError, ValueError) as e:
        logger.warning(f"Could not serialize sustainability_breakdown for logging: {e}")
        logger.info(f"Sustainability breakdown keys: {list(sustainability_breakdown.keys()) if isinstance(sustainability_breakdown, dict) else 'Not a dict'}")
        logger.info(f"Sustainability breakdown type: {type(sustainability_breakdown)}")

    # 4c. Calculate the default score that will be stored permanently in the database
    logger.info("=== STEP 4C: CALCULATING DEFAULT SCORE ===")
    default_score_for_db = calculate_weighted_score(sustainability_breakdown, DEFAULT_WEIGHTS)
    logger.info(f"Default score calculated: {default_score_for_db}")
    
    # 4d. Assemble the new, lean document to be inserted into MongoDB
    logger.info("=== STEP 4D: ASSEMBLING DOCUMENT FOR DATABASE ===")
    product_document = {
        "listing_id": parsed_info['listing_id'],
        "source_site": parsed_info['source_site'],
        "product_name": analysis_json.get('product_name', 'N/A'),
        "brand": analysis_json.get('brand', 'N/A'),
        "category": analysis_json.get('category', 'Unknown'),
        "sustainability_breakdown": sustainability_breakdown,
        "default_sustainability_score": default_score_for_db,    }
    # Safe logging with error handling for non-serializable objects
    try:
        logger.info(f"Document to insert: {json.dumps(product_document, indent=2)}")
    except (TypeError, ValueError) as e:
        logger.warning(f"Could not serialize product_document for logging: {e}")
        logger.info(f"Document keys: {list(product_document.keys()) if isinstance(product_document, dict) else 'Not a dict'}")
        logger.info(f"Document type: {type(product_document)}")

    # 4e. Save the new document to the database
    logger.info("=== STEP 4E: SAVING TO DATABASE ===")
    try:
        logger.info("Attempting to insert document into MongoDB...")
        result = products_collection.insert_one(product_document)
        logger.info(f"SUCCESS: Document inserted with _id: {result.inserted_id}")
        
        # Create a new dictionary for the response to the user.
        # This avoids modifying the original document we want to test.
        response_document = product_document.copy()
        
        # Add the new _id from the database result
        response_document['_id'] = result.inserted_id
        
        # Calculate the personalized score for the user
        logger.info("Calculating personalized score for response...")
        personalized_score = calculate_weighted_score(sustainability_breakdown, user_weights)
        response_document['sustainability_score'] = personalized_score
        logger.info(f"Personalized score: {personalized_score}")
        
        # Clean up the response document by removing the default score
        del response_document['default_sustainability_score']
        
        logger.info("SUCCESS: Process completed (CACHE MISS)")
        logger.info(f"Returning product: {json.dumps(response_document, indent=2, default=str)}")
        return response_document
    
    except Exception as e:
        # Check if this is a duplicate key error
        if "E11000 duplicate key error" in str(e):
            logger.warning(f"DUPLICATE KEY: Product already exists in database. Treating as cache hit.")
            logger.info("Fetching existing product from database...")
              # Extract the duplicate key information and fetch the existing document
            existing_doc = products_collection.find_one({
                "source_site": parsed_info['source_site'],
                "listing_id": parsed_info['listing_id']
            })
            
            if existing_doc:
                # Calculate personalized score using the existing sustainability breakdown
                logger.info("Calculating personalized score for existing product...")
                personalized_score = calculate_weighted_score(
                    existing_doc['sustainability_breakdown'], 
                    user_weights
                )
                
                # Prepare response document
                existing_doc['sustainability_score'] = personalized_score
                
                # Clean up the document before returning
                if 'default_sustainability_score' in existing_doc:
                    del existing_doc['default_sustainability_score']
                
                logger.info("SUCCESS: Process completed (DUPLICATE -> CACHE HIT)")
                logger.info(f"Returning existing product with personalized score: {personalized_score}")
                return existing_doc
            else:
                logger.error("FAILED: Could not fetch existing product after duplicate key error")
                return None
        else:
            # Handle other database errors
            logger.error(f"FAILED: Could not insert document into MongoDB: {e}")
            # Safe logging with error handling for non-serializable objects
            try:
                logger.error(f"Document that failed to insert: {json.dumps(product_document, indent=2)}")
            except (TypeError, ValueError) as json_error:
                logger.warning(f"Could not serialize product_document for logging: {json_error}")
                logger.error(f"Document keys: {list(product_document.keys()) if isinstance(product_document, dict) else 'Not a dict'}")
                logger.error(f"Document type: {type(product_document)}")
            return None
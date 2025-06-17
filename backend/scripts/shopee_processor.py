# ==============================================================================
# This file is the central "brain" for processing Shopee products.
# It orchestrates the entire workflow from receiving raw data to returning a
# final, scored product object.
# ==============================================================================

# --- Step 1: Import all necessary modules ---
# We import the database connection, the URL parser, the LLM analyzer,
# and all the necessary functions and constants from the scorer.

from db import products_collection
from url_parser import parse_shopee_url
from analyzer import get_full_product_analysis
from scorer import generate_sustainability_breakdown, calculate_weighted_score, DEFAULT_WEIGHTS


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
    # --- Guard Clause: Ensure database is connected ---
    if products_collection is None:
        print("Error: Database is not connected. Cannot process URL.")
        return None

    # --- Step 2a: Parse URL to get unique identifiers ---
    parsed_info = parse_shopee_url(url)
    if not parsed_info:
        print(f"Error: Invalid or unparsable Shopee URL: {url}")
        return None

    # --- Step 2b: Check the database (cache) for an existing product ---
    print(f"\nChecking cache for product -> site: '{parsed_info['source_site']}', listing_id: '{parsed_info['listing_id']}'")
    existing_product = products_collection.find_one({
        "source_site": parsed_info['source_site'],
        "listing_id": parsed_info['listing_id']
    })

    # --- Step 3: Handle Cache Hit (The Fast Path) ---
    if existing_product:
        print("✅ Cache HIT! Recalculating score with user weights.")
        
        # Use the stored breakdown to perform a very fast recalculation
        personalized_score = calculate_weighted_score(
            existing_product['sustainability_breakdown'], 
            user_weights
        )
        
        # Update the score in the document we are about to return to the user
        existing_product['sustainability_score'] = personalized_score
        
        # Clean up the document before sending it back to the API
        # The user doesn't need to see the default score or the internal _id
        if 'default_sustainability_score' in existing_product:
            del existing_product['default_sustainability_score']
        
        return existing_product

    # --- Step 4: Handle Cache Miss (The Full Pipeline) ---
    print("❌ Cache MISS. Starting full analysis pipeline...")

    # 4a. Call the LLM to analyze the raw text
    analysis_json = get_full_product_analysis(raw_text)
    if not analysis_json:
        print("Processing failed: LLM analysis returned no data.")
        return None

    # 4b. Convert the LLM's text analysis into our rich breakdown object
    sustainability_breakdown = generate_sustainability_breakdown(analysis_json)

    # 4c. Calculate the default score that will be stored permanently in the database
    default_score_for_db = calculate_weighted_score(sustainability_breakdown, DEFAULT_WEIGHTS)
    
    # 4d. Assemble the new, lean document to be inserted into MongoDB
    product_document = {
        "listing_id": parsed_info['listing_id'],
        "source_site": parsed_info['source_site'],
        "product_name": analysis_json.get('product_name', 'N/A'),
        "brand": analysis_json.get('brand', 'N/A'),
        "category": analysis_json.get('product_category', 'Unknown'),
        "sustainability_breakdown": sustainability_breakdown,
        "default_sustainability_score": default_score_for_db,
    }

    # 4e. Save the new document to the database
    try:
        result = products_collection.insert_one(product_document)
        # Add the new MongoDB _id to our local document object
        product_document['_id'] = result.inserted_id
        
        # 4f. Prepare the final document to be returned to the user
        # Calculate the score based on their specific weights
        personalized_score = calculate_weighted_score(sustainability_breakdown, user_weights)
        product_document['sustainability_score'] = personalized_score
        
        # Clean up the document for the final response
        del product_document['default_sustainability_score']
        
        print(f"✔️ New product saved to database with _id: {result.inserted_id}")
        return product_document
    except Exception as e:
        # This can happen if two requests for the same new product arrive at the same time
        print(f"Error: Could not insert document into MongoDB. It might be a duplicate race condition. {e}")
        return None
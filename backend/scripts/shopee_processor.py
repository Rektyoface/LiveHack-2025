from db import products_collection
from url_parser import parse_shopee_url
from scraper import scrape_shopee_page
from analyzer import get_sustainability_analysis
from scorer import calculate_score_from_analysis

def process_shopee_url(url: str) -> dict | None:
    """
    Orchestrates the entire process for a single Shopee URL.

    1. Parses the URL to get unique IDs.
    2. Checks the database (cache) for an existing product.
    3. If not cached, it scrapes, analyzes, scores, and saves the new product.
    4. Returns the final product document (from cache or newly created).

    Args:
        url: The Shopee product URL to process.

    Returns:
        A dictionary representing the product document from the database, or None on failure.
    """
    # 1. Check for database connection
    if not products_collection:
        print("Error: Database is not connected. Cannot process URL.")
        return None

    # 2. Parse the URL to get clean, unique identifiers
    parsed_info = parse_shopee_url(url)
    if not parsed_info:
        print(f"Error: Invalid or unparsable Shopee URL: {url}")
        return None

    # 3. Check the database (our cache) first
    print(f"\nChecking cache for product -> site: '{parsed_info['source_site']}', id: '{parsed_info['source_product_id']}'")
    existing_product = products_collection.find_one({
        "source_site": parsed_info['source_site'],
        "source_product_id": parsed_info['source_product_id']
    })

    if existing_product:
        print(f"✅ Cache HIT! Found product '{existing_product['product_name']}' in the database.")
        return existing_product

    # 4. If not in cache, begin the full processing pipeline
    print("❌ Cache MISS. Starting full processing pipeline...")

    # 4a. Scrape the live page
    scraped_data = scrape_shopee_page(url)
    if not scraped_data:
        print("Processing failed: Could not scrape the product page.")
        return None

    # 4b. Analyze with LLM and calculate the score
    print("Analyzing scraped text with LLM...")
    analysis_json = get_sustainability_analysis(scraped_data['raw_text'])
    print("Scoring the analysis...")
    final_score = calculate_score_from_analysis(analysis_json)

    # 4c. Assemble the complete document for insertion
    product_document = {
        "product_name": scraped_data['product_name'],
        "brand": scraped_data['brand'],
        "source_site": parsed_info['source_site'],
        "source_product_id": parsed_info['source_product_id'],
        "source_url": url,
        "raw_scraped_text": scraped_data['raw_text'],
        "llm_analysis": analysis_json,
        "sustainability_score": final_score,
        "last_analyzed_at": datetime.now(timezone.utc)
    }

    # 4d. Insert the new document into the database
    try:
        result = products_collection.insert_one(product_document)
        print(f"✔️ New product saved to database with _id: {result.inserted_id}")
        # We need to add the `_id` to our document to return the full object
        product_document['_id'] = result.inserted_id
        return product_document
    except Exception as e:
        print(f"Error: Could not insert document into MongoDB. It might be a duplicate race condition. {e}")
        return None
# url_parser.py (Simple, No-Import Version)

def parse_shopee_url(url: str) -> dict | None:
    """
    Parses a Shopee product URL using basic string manipulation, without any libraries.

    It looks for the 'i.shopId.itemId' pattern which is the stable, unique
    identifier for a product on Shopee.

    Args:
        url: The full Shopee product URL.

    Returns:
        A dictionary with parsed components:
        {
            "source_site": "shopee.sg",
            "source_product_id": "shopId_itemId",
        }
        Returns None if the URL format is not as expected.
    """
    try:
        # 1. Basic check to ensure it's a potential Shopee URL
        if 'shopee' not in url or 'i.' not in url:
            return None

        # 2. Extract the hostname (e.g., 'shopee.sg')
        # We split by '//' to get the part after 'https://'
        # Then we split by '/' to get the first part, which is the host
        domain_part = url.split('//')[1]
        source_site = domain_part.split('/')[0]

        # 3. Extract the unique ID part (i.shopId.itemId)
        # We find the last occurrence of 'i.' to be safe
        id_start_index = url.rfind('i.')
        # The identifier string is everything after that
        identifier_str = url[id_start_index:]

        # 4. Split the identifier string to get the shop and item IDs
        id_parts = identifier_str.split('.')
        # Expected parts: ['i', 'shopId', 'itemId']
        if len(id_parts) == 3:
            shop_id = id_parts[1]
            item_id = id_parts[2]
            
            # 5. Create our clean, composite ID for the database
            composite_product_id = f"{shop_id}_{item_id}"
            
            return {
                "source_site": source_site,
                "listing_id": composite_product_id,
            }
        
        # If the format wasn't 'i.shopId.itemId', it's invalid
        return None

    except (IndexError, AttributeError):
        # This will catch errors if the URL is malformed and split() doesn't work as expected
        return None

# This block allows you to test the file directly by running `python url_parser.py`
if __name__ == '__main__':
    print("--- Testing simple url_parser.py ---")
    
    test_urls = [
        "https://shopee.sg/-NEW-PUMA-Unisex-Shuffle-Shoes-(White)-i.341363989.24033132727",
        "https://shopee.ph/product/12345/67890", # A different format, should fail gracefully
        "https://shopee.co.id/Some-Product-Name-i.987654321.1234567890",
        "https://www.google.com" # Not a shopee url
    ]
    
    for url in test_urls:
        print(f"\nParsing URL: {url}")
        result = parse_shopee_url(url)
        if result:
            print("  ✅ Success:", result)
        else:
            print("  ❌ Failed or Invalid Format")
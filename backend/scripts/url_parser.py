# url_parser.py (Simple, No-Import Version)
import re

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

def extract_url_from_request(request) -> str | None:
    """
    Extract product URL from various request formats.
    
    Args:
        request: Flask request object
        
    Returns:
        Product URL if found, None otherwise
    """
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
            if data and 'url' in data:
                return data['url']
        elif 'text/plain' in request.content_type:
            raw_data = request.get_data(as_text=True)
            # Try to extract URL from the text
            url_match = re.search(r"URL: (https?://.*?)(\s|$|\n)", raw_data)
            if url_match:
                return url_match.group(1).strip()
        return None
    except Exception:
        return None

def extract_text_from_request(request) -> str | None:
    """
    Extract product text content from various request formats.
    
    Args:
        request: Flask request object
        
    Returns:
        Product text content if found, None otherwise
    """
    try:
        if request.content_type == 'application/json':
            data = request.get_json()
            if not data:
                return None
                
            # If plainText is provided, use it directly
            if 'plainText' in data:
                return data['plainText']
            
            # Otherwise construct from various fields
            elif 'name' in data or 'brand' in data or 'specifications' in data or 'description' in data:
                text_parts = []
                
                if 'url' in data:
                    text_parts.append(f"URL: {data['url']}")
                
                if 'brand' in data:
                    text_parts.append(f"Product Brand: {data['brand']}")
                    
                if 'name' in data:
                    text_parts.append(f"Product Name: {data['name']}")
                
                # Add specifications
                if 'specifications' in data and data['specifications']:
                    specs = data['specifications']
                    spec_parts = ["Product Specifications:"]
                    
                    for spec in specs:
                        if isinstance(spec, dict) and 'header' in spec and 'text' in spec:
                            spec_parts.append(f"{spec['header']}: {spec['text']}")
                        elif isinstance(spec, str):
                            spec_parts.append(spec)
                    
                    text_parts.append('\n'.join(spec_parts))
                
                # Add description
                if 'description' in data and data['description']:
                    desc = data['description']
                    desc_parts = ["Product Description:"]
                    
                    for d in desc:
                        if isinstance(d, dict) and 'text' in d:
                            desc_parts.append(d['text'])
                        elif isinstance(d, str):
                            desc_parts.append(d)
                    
                    text_parts.append('\n'.join(desc_parts))
                
                return '\n'.join(text_parts)
                
        elif 'text/plain' in request.content_type:
            return request.get_data(as_text=True)
        
        return None
    except Exception:
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
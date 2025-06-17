# analyzer.py
import json
from groq import Groq
import sys
import os
import logging
import config

# Configure logging for analyzer
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('analyzer')

# If config.py is in the same directory (scripts) as analyzer.py:
from config import GROQ_API_KEY, APP_CATEGORIES
# The sys.path manipulations for finding config in a parent directory are removed,
# as config.py is stated to be in the same 'scripts' directory.
# The shopee_processor.py (which imports analyzer.py) should already handle 
# adding the 'backend' directory to sys.path if necessary for other imports 
# that analyzer.py might make (though currently it doesn't seem to make other local ones).

client = Groq(api_key=GROQ_API_KEY)

def get_full_product_analysis(raw_text: str) -> dict | None:
    logger.info("=== ANALYZER: STARTING LLM ANALYSIS ===")
    logger.info(f"Input text length: {len(raw_text) if raw_text else 0}")
    logger.info(f"GROQ API key configured: {bool(GROQ_API_KEY)}")
    
    if not raw_text or not raw_text.strip():
        logger.error("FAILED: No raw text provided for analysis")
        return None
    
    # Convert the list of categories into a comma-separated string for the prompt
    category_list_str = ", ".join(f'"{cat}"' for cat in APP_CATEGORIES)
    logger.info(f"Using categories: {category_list_str}")
    
    system_prompt = f"""
    You are a powerful data extraction engine. Your task is to parse a raw text dump from a product page and convert it into a structured JSON object.

    CRITICAL RULES:
    1.  **Extract Everything:** You must extract all fields defined in the schema below.
    2.  **Handle Missing Data:** If a factor is not mentioned, use 'Not Mentioned' or 'Unknown'.
    3.  **Strict JSON Output:** Your response MUST be a valid JSON object only.

    The JSON object must follow this exact schema:
    {{
      "product_name": "The main title of the product.",
      "brand": "The brand name of the product.",
      "product_category": "A standardized product category chosen ONLY from this list: [{category_list_str}]. To determine the category, follow these steps in order: PRIORITY 1: Look for a structured 'Category' path (e.g., 'Category > Men's Shoes > Sneakers'). Use the most descriptive term from the path to choose from the list. PRIORITY 2: If no structured path exists, analyze the product title and description for keywords (e.g., 'shoes', 'shirt', 'headphones'). IGNORE all text related to shipping, store policies, ratings, and especially size charts when determining the category. If no category can be determined, use 'Unknown'.",
      "materials": {{
        "analysis": "Summary of materials.",
        "type": "Categorize primary material.",
        "reasoning": "Why you chose this."
      }},
      "manufacturing_and_origin": {{
        "country_of_origin": "Country of manufacture, if mentioned. Else 'Not Mentioned'.",
        "reasoning": "Explain your assessment."
      }},
      "logistics_and_shipping": {{
        "ships_from_location": "Location product ships from.",
        "shipping_distance_implication": "Categorize as 'Local', 'Regional', or 'International'.",
        "reasoning": "Explain."
      }},
      "packaging": {{
        "mentioned": "boolean",
        "description": "Describe packaging or 'Not Mentioned'.",
        "reasoning": "Quote text or state why not mentioned."
      }},
      "durability_and_longevity": {{
        "assessment": "Assess as 'Low', 'Medium', 'High', 'Unknown'.",
        "reasoning": "Explain based on text."
      }},
      "certifications": {{
        "has_certifications": "boolean",
        "list": ["List any specific claims."]
      }}
    }}
    """
    
    logger.info("Sending request to Groq LLM...")
    logger.info(f"Raw text preview (first 1000 chars): {raw_text[:1000]}...")
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please parse the following text dump:\n\n{raw_text}"},
            ],
            model="llama3-70b-8192",
            temperature=0.0, # Set to 0 for maximum fact-based adherence
            response_format={"type": "json_object"},
        )
        
        logger.info("SUCCESS: Received response from Groq LLM")
        
        # Parse the JSON response
        response_content = chat_completion.choices[0].message.content
        logger.info(f"Raw LLM response: {response_content}")
        
        parsed_response = json.loads(response_content)
        logger.info(f"Parsed LLM response: {json.dumps(parsed_response, indent=2)}")
        
        return parsed_response
        
    except json.JSONDecodeError as e:
        logger.error(f"FAILED: Invalid JSON response from LLM: {e}")
        logger.error(f"Raw response was: {chat_completion.choices[0].message.content if 'chat_completion' in locals() else 'No response received'}")
        return None
        
    except Exception as e:
        logger.error(f"FAILED: An error occurred during LLM analysis: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        return None
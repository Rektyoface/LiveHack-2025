import os
import json
from groq import Groq

# --- MODIFICATION START ---
# Import the API key from your config.py file
try:
    from config import GROQ_API_KEY
except ImportError:
    print("Error: Could not import GROQ_API_KEY from config.py.")
    print("Please make sure a 'config.py' file exists in the same directory and contains your API key.")
    exit()

if not GROQ_API_KEY:
    print("Error: GROQ_API_KEY is empty in config.py.")
    print("Please add your Groq API key to the config.py file.")
    exit()

# Initialize the Groq client by passing the API key directly
try:
    client = Groq(api_key=GROQ_API_KEY)
except Exception as e:
    print(f"Error initializing Groq client: {e}")
    exit()
# --- MODIFICATION END ---


def get_sustainability_factors_from_text(scraped_data: dict) -> dict:
    """
    Analyzes scraped e-commerce product data using an LLM to extract sustainability factors.

    Args:
        scraped_data: A dictionary containing the product's text data.
                      Expected keys: 'title', 'description', 'specifications'.

    Returns:
        A dictionary containing the structured sustainability analysis,
        or an error dictionary if the analysis fails.
    """
    
    # Combine the scraped data into a single block for the LLM
    product_text = f"""
    Product Title: {scraped_data.get('title', 'N/A')}

    Product Description: {scraped_data.get('description', 'N/A')}

    Product Specifications: {scraped_data.get('specifications', 'N/A')}
    """

    system_prompt = """
    You are an expert sustainability analyst for an e-commerce platform. Your task is to analyze web-scraped text from a product page and extract key factors that influence its environmental and social sustainability score.

    Your response MUST be a valid JSON object only, with no additional text or explanations outside the JSON structure.

    Analyze the provided text based on the following dimensions. For each factor, provide a brief `reasoning` based ONLY on the text provided. If information is not available, state 'Not Mentioned' or use a neutral assessment.

    The JSON object must follow this exact schema:
    {
      "product_category": "A best-guess category for the product (e.g., 'Apparel', 'Kitchenware', 'Electronics').",
      "materials": {
        "analysis": "A summary of the product's materials.",
        "type": "Categorize the primary material as 'Natural', 'Synthetic', 'Recycled', 'Metal', 'Wood', 'Mixed', or 'Unknown'.",
        "reasoning": "Why you chose this categorization based on the text."
      },
      "manufacturing_and_origin": {
        "country_of_origin": "The country where the product was made, if mentioned.",
        "labor_implications": "Infer potential labor practice implications ('Positive', 'Neutral', 'Negative', 'Unknown') based on country of origin or certifications. State 'Unknown' if no data.",
        "reasoning": "Explain your assessment."
      },
      "logistics_and_shipping": {
        "ships_from_location": "The location the product ships from (city or country).",
        "shipping_distance_implication": "Categorize the shipping distance as 'Local', 'Regional', or 'International' based on the 'ships_from' location relative to a global consumer.",
        "reasoning": "Explain the shipping distance implication."
      },
      "packaging": {
        "mentioned": "A boolean (true/false) indicating if packaging was mentioned.",
        "description": "Describe the packaging if mentioned (e.g., 'Eco-friendly', 'Plastic-free', 'Standard'). State 'Not Mentioned' otherwise.",
        "reasoning": "Quote the part of the text that mentions packaging, or state why it's not mentioned."
      },
      "durability_and_longevity": {
        "assessment": "Assess the likely durability as 'Low', 'Medium', 'High', or 'Unknown'.",
        "reasoning": "Explain your assessment based on materials or descriptive words like 'heavy-duty', 'long-lasting', 'disposable', etc."
      },
      "certifications": {
        "has_certifications": "A boolean (true/false).",
        "list": ["List any sustainability certifications mentioned (e.g., 'FSC Certified', 'Fair Trade', 'GOTS Organic'). An empty list if none."]
      },
      "overall_summary": "A brief, one-sentence summary of the product's sustainability profile based on the available data."
    }
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f"Please analyze the following product data:\n\n{product_text}",
                },
            ],
            model="llama3-70b-8192", # Llama 3 70B is excellent for complex instructions and JSON
            temperature=0.1,         # Low temperature for factual, deterministic output
            response_format={"type": "json_object"},
        )
        
        response_content = chat_completion.choices[0].message.content
        return json.loads(response_content)

    except Exception as e:
        print(f"An error occurred while calling the Groq API: {e}")
        return {"error": "Failed to analyze sustainability factors.", "details": str(e)}

def calculate_score(report: dict) -> int:
    """Calculates a sustainability score based on the LLM's analysis."""
    if "error" in report:
        return 0 # Return a score of 0 if analysis failed

    score = 50  # Start with a neutral score
    
    # Material scoring
    material_scores = {'Natural': 15, 'Wood': 15, 'Recycled': 20, 'Metal': 5, 'Mixed': -5, 'Synthetic': -15, 'Unknown': 0}
    score += material_scores.get(report.get('materials', {}).get('type'), 0)
    
    # Durability scoring
    durability_scores = {'High': 10, 'Medium': 5, 'Low': -15, 'Unknown': 0}
    score += durability_scores.get(report.get('durability_and_longevity', {}).get('assessment'), 0)
    
    # Logistics scoring
    distance_scores = {'Local': 10, 'Regional': 0, 'International': -10}
    score += distance_scores.get(report.get('logistics_and_shipping', {}).get('shipping_distance_implication'), 0)
    
    # Packaging scoring
    packaging_info = report.get('packaging', {})
    if packaging_info.get('mentioned') and 'plastic-free' in packaging_info.get('description', '').lower():
        score += 15
    
    # Certification scoring
    cert_info = report.get('certifications', {})
    if cert_info.get('has_certifications'):
        score += 20 * len(cert_info.get('list', []))
        
    # Clamp the score between 0 and 100
    return max(0, min(100, int(score)))


if __name__ == '__main__':
    # --- Example 1: A product with good sustainability signals ---
    print("--- Analyzing Example 1: Bamboo Cutting Board ---")
    scraped_data_good = {
        'title': "Premium Organic Bamboo Cutting Board for Kitchen - Extra Large",
        'description': "Our heavy-duty chopping board is made from 100% natural Moso bamboo. A sustainable and renewable resource. It's built to last and won't dull your knives. Shipped in plastic-free, recyclable packaging. A great eco-friendly gift!",
        'specifications': "Material: Organic Bamboo\nCountry of Origin: China\nShips From: Metro Manila, PH\nCertifications: FSC Certified"
    }
    
    sustainability_report_good = get_sustainability_factors_from_text(scraped_data_good)
    print("LLM Analysis:")
    print(json.dumps(sustainability_report_good, indent=2))
    
    final_score_good = calculate_score(sustainability_report_good)
    print(f"\nCalculated Sustainability Score: {final_score_good}/100")


    # --- Example 2: A product with poor or missing sustainability signals ---
    print("\n\n--- Analyzing Example 2: Cheap Plastic Phone Case ---")
    scraped_data_bad = {
        'title': "Clear Soft TPU Phone Case for Model X - Ultra Thin Cover",
        'description': "Protect your new phone! This case is super slim and lightweight. Comes in 10 different colors. #phonecase #accessory #style",
        'specifications': "Material: TPU (Thermoplastic Polyurethane)\nShips From: Shenzhen, China"
    }
    
    sustainability_report_bad = get_sustainability_factors_from_text(scraped_data_bad)
    print("LLM Analysis:")
    print(json.dumps(sustainability_report_bad, indent=2))
    
    final_score_bad = calculate_score(sustainability_report_bad)
    print(f"\nCalculated Sustainability Score: {final_score_bad}/100")
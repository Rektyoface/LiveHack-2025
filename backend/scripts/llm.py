import json
from groq import Groq
import backend.scripts.config as config

client = Groq(
    api_key= config.API_KEY
)


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
    
    # Check if LLM client is available
    if not client:
        return {
            "error": "LLM client not initialized. Please check GROQ_API_KEY configuration.",
            "details": "Groq API key not set or invalid"
        }
    
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


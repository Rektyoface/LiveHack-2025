# scripts/analyzer.py (Advanced: Using the correct gemini-1.5-flash-latest model)

import json
import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
import sys
import os

# --- Path Correction and Config Import ---
try:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from config import GOOGLE_API_KEY, APP_CATEGORIES
except ImportError:
    print("CRITICAL: Could not import from config.py.")
    sys.exit(1)

# --- Configure Google AI Client ---
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"CRITICAL: Failed to configure Google AI. Error: {e}")
    sys.exit(1)

# --- Define the Tools ---

# Tool 1: Google Search (for information gathering)
google_search_tool = FunctionDeclaration(
    name="google_search",
    description="Performs a Google search to find public information about a company's sustainability practices or product materials.",
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "A specific search query."}},
        "required": ["query"]
    }
)

# Tool 2: The Final Answer Formatter (for structured output)
analysis_submission_tool = FunctionDeclaration(
    name="submit_sustainability_analysis",
    description="Submits the complete, final sustainability analysis once all information has been gathered and synthesized.",
    parameters={
        "type": "object",
        "properties": {
            "product_name": {"type": "string", "description": "The main title of the product, from the provided text."},
            "brand": {"type": "string", "description": "The brand name of the product, from the provided text."},
            "category": {"type": "string", "enum": APP_CATEGORIES, "description": "The standardized product category."},
            "sustainability_analysis": {
                "type": "object",
                "properties": {
                    "material_composition": {
                        "type": "object",
                        "properties": {
                            "analysis": {"type": "string"}, "rating": {"type": "string", "enum": ["Excellent", "Good", "Neutral", "Poor", "Unknown"]}, "reasoning": {"type": "string"}
                        },
                        "required": ["analysis", "rating", "reasoning"]
                    },
                    "production_and_brand": {
                        "type": "object",
                        "properties": {
                            "analysis": {"type": "string"}, "rating": {"type": "string", "enum": ["Excellent", "Good", "Neutral", "Poor", "Unknown"]}, "reasoning": {"type": "string"}
                        },
                        "required": ["analysis", "rating", "reasoning"]
                    },
                    "circularity_and_end_of_life": {
                        "type": "object",
                        "properties": {
                            "analysis": {"type": "string"}, "rating": {"type": "string", "enum": ["Excellent", "Good", "Neutral", "Poor", "Unknown"]}, "reasoning": {"type": "string"}
                        },
                        "required": ["analysis", "rating", "reasoning"]
                    }
                },
                "required": ["material_composition", "production_and_brand", "circularity_and_end_of_life"]
            }
        },
        "required": ["product_name", "brand", "category", "sustainability_analysis"]
    }
)

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-preview-05-20', 
    tools=[google_search_tool, analysis_submission_tool]
)


def get_full_product_analysis(raw_text: str) -> dict | None:
    # Convert the list of categories into a comma-separated string for the prompt
    category_list_str = ", ".join(f'"{cat}"' for cat in APP_CATEGORIES)
    
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
        return json.loads(chat_completion.choices[0].message.content)
    except Exception as e:
        print(f"An error occurred during LLM analysis: {e}")
        # Return a structured error dictionary instead of None
        return {
            "error": "LLM analysis failed.",
            "details": str(e)
        }
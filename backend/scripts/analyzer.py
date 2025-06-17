# scripts/analyzer.py (Google Gemini with Google Search Grounding)

import json
import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration
import sys
import os

# --- Path Correction ---
# Ensures that the script can find the 'config.py' file in the parent directory.
try:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    from config import GOOGLE_API_KEY, APP_CATEGORIES
except ImportError:
    print("CRITICAL: Could not import GOOGLE_API_KEY or APP_CATEGORIES from config.py.")
    print("Please ensure config.py exists in the project root and contains the necessary variables.")
    sys.exit(1)

# --- Configure the Google AI Client ---
# This uses the API key from your config file.
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"CRITICAL: Failed to configure Google AI. Is GOOGLE_API_KEY valid in config.py? Error: {e}")
    # We exit here because the analyzer cannot function without a valid configuration.
    sys.exit(1)

# --- Define the Google Search Tool ---
# This object describes the "Google Search" capability that we give to the LLM.
# The model will use this tool when it determines it needs external information.
google_search_tool = Tool(
    function_declarations=[
        FunctionDeclaration(
            name="google_search",
            description="Performs a Google search to find public information about a company's sustainability practices, controversies, or official reports. Use this to verify claims or find missing information about a brand's overall reputation.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A specific and targeted search query for Google. For example: 'Patagonia sustainability report 2023' or 'Shein labor practices controversy'."
                    }
                },
                "required": ["query"]
            }
        )
    ]
)

# --- Load the Gemini Model ---
# 'gemini-2.5-flash-latest' is a great, fast choice for this task.
# We also enable the google_search_tool for it globally here.
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash-latest',
    tools=[google_search_tool]
)


def get_full_product_analysis(raw_text: str) -> dict | None:
    """
    Analyzes raw text from a product page using Google's Gemini Flash model,
    with Google Search enabled for grounding and external information retrieval.
    """
    category_list_str = ", ".join(f'"{cat}"' for cat in APP_CATEGORIES)
    
    # This prompt is our grounding mechanism. It strictly defines the model's behavior
    # and explicitly tells it when and how to use its Google Search tool.
    system_prompt = f"""
    You are a precise and diligent sustainability data extraction engine. Your task is to analyze a user-provided text dump from a product page and combine it with targeted Google searches to create a comprehensive, grounded, and structured JSON object.

    **CRITICAL RULES FOR GROUNDING:**
    1.  **Source of Truth:** Your primary source is the user-provided text. Extract as much as possible from it first.
    2.  **TOOL USE - GOOGLE SEARCH:** You have a tool named `google_search`. You MUST use it to find information that is **not available in the provided text**, especially regarding the brand's overall reputation, specific material information, or labor practices. Be specific and targeted in your search queries.
    3.  **Synthesize and Justify:** In your 'reasoning' fields, you must state whether the information came from the 'Provided Text' or 'Google Search'.
    4.  **Strict JSON Output:** Your entire response MUST be a single, raw, valid JSON object. Do not include any introductory text, explanations, or markdown formatting like ```json.

    **JSON Schema:**
    {{
      "product_name": "Extract the main title of the product from the provided text.",
      "brand": "Extract the brand name from the provided text.",
      "product_category": "A standardized product category chosen ONLY from this list: [{category_list_str}]. Base this ONLY on the provided text.",
      "materials": {{
        "analysis": "Summary of materials. If the text is vague (e.g., 'synthetic'), use Google Search to find more details about the brand's common materials.",
        "type": "Categorize the primary material. Use your search findings to be more specific.",
        "reasoning": "Justify your choice, stating if it's from 'Provided Text' or 'Google Search'."
      }},
      "manufacturing_and_origin": {{
        "country_of_origin": "Country of manufacture from the provided text. If not present, state 'Not Mentioned'.",
        "labor_implications": "Assess the brand's labor practices. **This is a key area for Google Search.** Look for reports on fair labor, controversies, or certifications.",
        "reasoning": "Justify your assessment (e.g., 'Positive', 'Negative', 'Mixed', 'Unknown'), citing your source (text or search)."
      }},
      "logistics_and_shipping": {{
        "ships_from_location": "Extract this ONLY from the provided text.",
        "shipping_distance_implication": "Categorize as 'Local', 'Regional', or 'International'.",
        "reasoning": "Explain based on the 'ships_from' information."
      }},
      "packaging": {{
        "mentioned": "boolean (true if mentioned in text, false otherwise)",
        "description": "Describe the packaging or state 'Not Mentioned'.",
        "reasoning": "Quote the text about packaging."
      }},
      "durability_and_longevity": {{
        "assessment": "Assess as 'Low', 'Medium', 'High', 'Unknown', based only on the provided text.",
        "reasoning": "Explain based on words like 'heavy-duty', 'long-lasting', etc."
      }},
      "certifications": {{
        "has_certifications": "boolean (true if claims are made, false otherwise)",
        "list": ["List any specific sustainability claims from the text. Use Google Search to verify or find other known certifications for the brand."]
      }}
    }}
    """
    
    full_prompt = f"{system_prompt}\n\nParse the following text dump:\n\n---\n\n{raw_text}"

    try:
        # Call the Google Gemini API
        response = model.generate_content(
            full_prompt,
            # Configuration to ensure JSON output and deterministic behavior
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.0
            }
        )
        
        # The response text should already be a clean JSON string
        return json.loads(response.text)
        
    except Exception as e:
        print(f"An error occurred during Google Gemini API analysis: {e}")
        return {
            "error": "LLM analysis failed.",
            "details": str(e)
        }
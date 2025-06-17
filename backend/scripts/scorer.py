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
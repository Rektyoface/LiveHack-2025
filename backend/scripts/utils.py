# utils.py - Utility functions for the EcoShop backend

def clean_specifications(specs):
    """Remove review and rating text from product specifications."""
    if isinstance(specs, dict):
        cleaned = {}
        for k, v in specs.items():
            # Remove keys that are obviously reviews/ratings
            if any(word in k.lower() for word in ["review", "rating", "comment", "report abuse", "5.0 out of 5", "star", "media", "helpful?"]):
                continue
            # Remove values that contain review/rating patterns
            if isinstance(v, str):
                lower_v = v.lower()
                if any(word in lower_v for word in ["review", "ratings", "comments", "report abuse", "5.0 out of 5", "star", "media", "helpful?"]):
                    # Truncate at the first review keyword
                    for word in ["review", "ratings", "comments", "report abuse", "5.0 out of 5", "star", "media", "helpful?"]:
                        idx = lower_v.find(word)
                        if idx != -1:
                            v = v[:idx]
                            break
                cleaned[k] = v.strip()
            else:
                cleaned[k] = v
        return cleaned
    elif isinstance(specs, str):
        # Remove review/rating text from a string
        lower_s = specs.lower()
        for word in ["review", "ratings", "comments", "report abuse", "5.0 out of 5", "star", "media", "helpful?"]:
            idx = lower_s.find(word)
            if idx != -1:
                return specs[:idx].strip()
        return specs
    return specs

def generate_sustainability_advice(factors: dict) -> dict:
    """Generate specific advice based on sustainability factors."""
    advice = {}
    
    if factors.get('co2e', 0) > 7:
        advice['co2e'] = "Consider reducing carbon emissions through supply chain optimizations and renewable energy."
    
    if factors.get('water_usage', 0) > 7:
        advice['water'] = "Implement water conservation practices in manufacturing and processing."
    
    if factors.get('waste', 0) > 7:
        advice['waste'] = "Develop circular economy practices and reduce packaging waste."
    
    if factors.get('labor', 10) < 5:
        advice['labor'] = "Improve labor conditions and ensure fair wages throughout the supply chain."
    
    if factors.get('recycled_materials', 0) < 30:
        advice['materials'] = "Increase use of recycled and sustainably sourced materials."
    
    return advice

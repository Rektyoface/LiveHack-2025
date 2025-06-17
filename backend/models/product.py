from dataclasses import dataclass, field

@dataclass
class Product:
    default_sustainability_score: int
    brand_name: str
    product_name: str
    sustainability_breakdown: str
    listing_id: int 
    source_site: str
    category: str

    def to_dict(self):
        return {
            "default_sustainability_score": self.default_sustainability_score,
            "brand_name": self.brand_name,
            "product_name": self.product_name,
            "sustainability_breakdown": self.sustainability_breakdown,
            "listing_id": self.listing_id,
            "sourceSite": self.source_site,
            "category": self.category
        }

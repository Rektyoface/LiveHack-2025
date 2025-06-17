from dataclasses import dataclass

@dataclass
class Product:
    productName: str
    brandName: str
    description: str
    ecoScore: int
    additionalInfo: str

    def to_dict(self):
        return {
            "productName": self.productName,
            "brandName": self.brandName,
            "description": self.description,
            "ecoScore": self.ecoScore,
            "additionalInfo": self.additionalInfo
        }

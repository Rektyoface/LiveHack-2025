from dataclasses import dataclass

@dataclass
class Product:
    productID: int
    brandID: int
    ecoScore: int
    additionalInfo: str
    itemIdentifier: int

    def to_dict(self):
        return {
            "productID": self.productID,
            "brandID": self.brandID,
            "itemIdentifier": self.itemIdentifier,
            "ecoScore": self.ecoScore,
            "additionalInfo": self.additionalInfo
        }

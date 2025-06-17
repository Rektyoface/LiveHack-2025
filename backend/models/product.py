from dataclasses import dataclass, field

@dataclass
class Product:
    productID: int
    brandID: int
    ecoScore: int
    additionalInfo: str
    itemIdentifier: int = field(init=False)  # prevent manual setting

    def __post_init__(self):
        # Automatically set itemIdentifier as concatenation of brandID and productID
        self.itemIdentifier = int(f"{self.brandID}{self.productID}")

    def to_dict(self):
        return {
            "productID": self.productID,
            "brandID": self.brandID,
            "itemIdentifier": self.itemIdentifier,
            "ecoScore": self.ecoScore,
            "additionalInfo": self.additionalInfo
        }

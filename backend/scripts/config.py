# MongoDB Configuration
# Set MONGO_URI to empty to run without MongoDB
# Or set it to a valid connection string (e.g., mongodb://localhost:27017)
MONGO_URI="mongodb+srv://YAROUDIO:dragonhero@cluster0.fddxx8h.mongodb.net/Testrun?retryWrites=true&w=majority&appName=Cluster0"
MONGO_DB="LifeHackData"
MONGO_PRODUCTS_COLLECTION="alldata"
MONGO_SCORES_COLLECTION="scores"

# LLM Configuration for Groq API
GROQ_API_KEY="your_groq_api_key_here"

# The master list of categories for your application
APP_CATEGORIES = [
    "Footwear",
    "Apparel",
    "Electronics",
    "Home & Kitchen",
    "Health & Beauty",
    "Sports & Outdoors",
    "Toys & Games",
    "Books & Media",
    "Groceries",
    "Automotive",
    "Unknown"
]
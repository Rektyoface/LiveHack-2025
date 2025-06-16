# EcoShop - Sustainability Shopping Companion

**Production-Ready Consumer Browser Extension**

EcoShop is a browser extension that provides real-time sustainability scores for products as you browse Shopee. This extension requires a database connection to function and displays sustainability data sourced from a centralized MongoDB database.

## 🌱 How It Works

1. **Product Detection**: Automatically detects products on Shopee pages
2. **Database Lookup**: Checks our MongoDB database for existing sustainability scores
3. **New Product Processing**: Sends new products to the database for LLM analysis (runs on separate machine)
4. **Score Display**: Shows sustainability scores directly on product pages

## 🚀 Installation

### Browser Extension

1. Download or clone this repository
2. Open Chrome/Edge and go to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select the `extension` folder
5. Configure the API endpoint in extension options (Settings → Database Connection)

### Backend API (Required)

The extension requires a running backend API with MongoDB connection:

```bash
cd backend
pip install -r requirements.txt

# Configure MongoDB connection in .env file
MONGO_URI=your_mongodb_connection_string
MONGO_DB=LifeHackData
MONGO_PRODUCTS_COLLECTION=alldata
MONGO_SCORES_COLLECTION=scores

python app.py
```

## ⚙️ Configuration

### Database Connection

This extension **requires** a MongoDB database connection. Configure the API endpoint in:
- Extension Options → Database Connection → Backend API Endpoint
- Default: `http://localhost:5000/api/score`

### Architecture

```
Browser Extension (Consumer) ←→ Flask API ←→ MongoDB Database
                                     ↑
                              LLM Service (Separate Machine)
```

- **Browser Extension**: Detects products and displays scores
- **Flask API**: Handles database queries and product submissions
- **MongoDB**: Stores products and sustainability scores
- **LLM Service**: Runs separately, analyzes new products, updates database

## 🛠 Features

- **Real-time Product Detection**: Automatically identifies products on Shopee
- **Sustainability Scoring**: Shows comprehensive environmental impact scores
- **Database-Driven**: All data sourced from centralized MongoDB database
- **Polling System**: Waits for LLM analysis of new products
- **Dark/Light Mode**: Customizable UI preferences
- **Badge Positioning**: Adjustable on-page badge placement

## 📊 Sustainability Metrics

- **Overall Score**: 0-100 sustainability rating
- **CO2 Emissions**: Carbon footprint per unit
- **Water Usage**: Water consumption rating
- **Waste Generated**: Waste production assessment
- **Labor Practices**: Ethical sourcing evaluation

## 🔧 Production Deployment

### Database Requirements

- MongoDB Atlas or self-hosted MongoDB instance
- Collections: `alldata` (products), `scores` (sustainability data)
- Network access configured for API server

### API Server

- Flask application with MongoDB connectivity
- Environment variables for database configuration
- CORS enabled for browser extension communication

### Extension Distribution

Ready for browser extension stores:
- No local data dependencies
- Graceful error handling for database connectivity issues
- Production-ready manifest and permissions

## 🚫 No Offline Mode

This is a **production consumer extension** that requires database connectivity. Unlike development versions:
- No local data fallbacks
- No hardcoded brand databases
- No offline functionality
- Requires active internet connection and database access

## 🛡️ Error Handling

The extension provides clear feedback for:
- Database connection failures
- Missing sustainability data
- Network connectivity issues
- API endpoint configuration problems

## 📝 Usage

1. Navigate to any Shopee product page
2. Extension automatically detects the product
3. Sustainability badge appears on the page
4. Click badge or extension icon for detailed information
5. For new products, the system polls for LLM analysis completion

## 🔍 Testing

Run the test suite to verify API functionality:

```bash
cd backend
python test_api.py
```

Tests cover:
- Health check endpoint
- Product processing workflow
- Brand lookup functionality
- Database connectivity

## 📋 Requirements

- **Browser**: Chrome/Edge with extension support
- **Internet**: Active connection required
- **Database**: MongoDB with sustainability data
- **API**: Running Flask backend service

## 🎯 Production Checklist

✅ Removed all mock/fallback databases  
✅ Database connection required for all operations  
✅ Graceful error handling for connectivity issues  
✅ Production-ready manifest and permissions  
✅ Clear user feedback for database requirements  
✅ No local data dependencies  
✅ Ready for extension store distribution

## 📁 Project Structure

```
├── extension/                 # Browser extension files
│   ├── manifest.json         # Extension configuration  
│   ├── content.js            # Product detection & UI
│   ├── service_worker.js     # Background processing
│   ├── popup/                # Extension popup interface
│   └── options/              # Settings page
├── backend/                  # Flask API server
│   ├── app.py               # Main API application
│   ├── scripts/             # Database utilities
│   └── test_api.py          # API testing suite
└── README.md                # This file
```

## 🔗 API Endpoints

- `GET /api/health` - System health check
- `GET /api/score?brand=Nike` - Brand sustainability lookup
- `POST /api/product` - Submit product for analysis
- `GET /api/product/{id}/status` - Check analysis status
- `GET /api/mongodb/status` - Database connection status

## 🚀 Next Steps

1. **Configure MongoDB**: Set up database with product collections
2. **Deploy API**: Host Flask application with database access
3. **Install Extension**: Load extension and configure API endpoint
4. **Set up LLM**: Deploy separate LLM service for product analysis
5. **Test Workflow**: Verify end-to-end functionality

---

*Created for LiveHack 2025 - Making sustainable shopping accessible to everyone*

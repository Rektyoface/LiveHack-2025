# EcoShop - Sustainability Shopping Companion

🌱 **A smart browser extension that provides real-time sustainability analysis for products on Shopee, helping you make eco-conscious shopping decisions.**

![EcoShop Extension](icon.png)

## 🚀 Quick Start Guide

### 1. **Install the Extension**

#### **Requirements:**
- **Chromium-based browser** (Chrome, Edge, Brave, Opera, etc.)
- **Developer mode** enabled

#### **Installation Steps:**

1. **Download the Extension**
   - Download or clone this repository to your computer
   - Locate the `extension` folder in the project directory

2. **Enable Developer Mode**
   - Open your Chromium browser (Chrome, Edge, etc.)
   - Navigate to Extensions: `chrome://extensions/` (or `edge://extensions/` for Edge)
   - Toggle **"Developer mode"** switch in the top-right corner

3. **Load the Extension**
   - Click **"Load unpacked"** button
   - Navigate to and select the `extension` folder from this project
   - The EcoShop extension icon should appear in your browser toolbar

4. **Verify Installation**
   - Look for the EcoShop leaf icon 🌱 in your browser toolbar
   - If hidden, click the puzzle piece icon and pin EcoShop for easy access

### 2. **Ready to Use!**

The extension connects to a remote backend API automatically - no additional setup required. Simply visit any Shopee product page to start getting sustainability insights!

---

## 📱 How to Use EcoShop

### **Basic Usage:**

1. **Visit Shopee**: Navigate to any Shopee product page (shopee.sg or shopee.com)
2. **Automatic Analysis**: EcoShop automatically detects product pages and starts analysis
3. **View Results**: 
   - **Floating Badge**: Appears on the page with sustainability score
   - **Extension Popup**: Click the toolbar icon for detailed breakdown
   - **Browser Badge**: Small score indicator on the extension icon

### **Extension Interface:**

#### **📊 Main Popup** (Click extension icon)
- **Sustainability Score**: Overall rating out of 100
- **Brand Information**: Product brand and certainty level
- **Breakdown Metrics**: Three key sustainability factors:
  - **Production and Brand**: Manufacturing practices, certifications
  - **Circularity and End of Life**: Recycling, disposal impact
  - **Material Composition**: Raw materials sustainability
- **Action Buttons**:
  - **Show Details**: Deep dive into each metric
  - **View Recommendations**: Alternative sustainable products
  - **Settings**: Customize your experience
  - **Learn More**: Project information

#### **🔍 Details Page**
- **Detailed Analysis**: In-depth breakdown of each sustainability factor
- **Scoring Rationale**: Why each metric received its score
- **Raw Data**: Specifications and analysis used for scoring

#### **💡 Recommendations Page**
- **Alternative Products**: More sustainable options in similar categories
- **Comparative Scores**: Side-by-side sustainability ratings
- **Direct Links**: Navigate to recommended products

---

## ⚙️ Settings & Customization

Access settings by clicking **"Settings"** in the extension popup or right-clicking the extension icon → **"Options"**.

### **🎯 Sustainability Metrics Weights**

Customize how much each factor impacts the overall score:

- **Production and Brand** (1-5 scale)
  - Brand sustainability practices
  - Manufacturing certifications
  - Supply chain transparency

- **Circularity and End of Life** (1-5 scale)
  - Product recyclability
  - Packaging sustainability
  - Disposal impact

- **Material Composition** (1-5 scale)
  - Raw material sustainability
  - Renewable resource usage
  - Environmental impact of materials

**How it works**: Higher weights (5) make that factor more important in the final score. Lower weights (1) reduce its impact.

### **🎨 Display Settings**

#### **Show Sustainability Badge on Product Pages**
- **Enabled**: Floating badge appears on Shopee product pages
- **Disabled**: Only extension popup shows data (cleaner browsing)

#### **Badge Position**
Choose where the floating badge appears:
- **Bottom Right** (default) - Positioned above Shopee's chat button
- **Bottom Left** - Left side of screen
- **Top Right** - Upper right corner
- **Top Left** - Upper left corner

#### **Show Alternative Product Recommendations**
- **Enabled**: "View Recommendations" button appears in popup
- **Disabled**: Recommendations feature hidden (faster loading)

#### **Dark Mode**
- **Enabled** (default) - Dark theme for better readability
- **Disabled** - Light theme

#### **Senior Mode (Large Font)**
- **Enabled** - Larger text and UI elements for accessibility
- **Disabled** (default) - Standard sizing

### **💾 Settings Management**

- **Save Settings**: Apply changes and refresh all EcoShop interfaces
- **Restore Defaults**: Reset all settings to original values
- **Auto-sync**: Settings automatically sync across browser sessions

---

## 🏗️ How EcoShop Works

### **Frontend Architecture**

#### **Content Script** (`content.js`)
- **Product Detection**: Automatically identifies Shopee product pages
- **Data Extraction**: Pulls product information (brand, name, specifications)
- **Floating Badge**: Creates and positions the on-page sustainability indicator
- **Anti-Spam Protection**: Prevents duplicate requests for the same product

#### **Service Worker** (`service_worker.js`)
- **Background Processing**: Handles API communication with backend
- **Badge Management**: Updates extension icon with scores
- **Data Caching**: Optimizes performance with intelligent caching
- **Error Handling**: Graceful fallbacks when backend is unavailable

#### **Popup Interface** (`popup/`)
- **Real-time Scoring**: Calculates weighted scores based on user preferences
- **Progressive Loading**: Smooth loading experience with status updates
- **Navigation**: Seamless movement between summary, details, and recommendations
- **Settings Integration**: Live updates when preferences change

#### **Options Page** (`options/`)
- **Weight Adjustment**: Real-time sliders for metric importance
- **Display Preferences**: Toggle features and appearance settings
- **Accessibility**: Senior mode for improved readability

### **Backend Architecture**

#### **Flask API** (`app.py`)
- **RESTful Endpoints**: Clean API for product analysis requests
- **Error Handling**: Comprehensive error responses and logging
- **CORS Support**: Secure cross-origin requests from extension

#### **Analysis Pipeline** (`scripts/`)
- **Product Processing**: `shopee_processor.py` handles product data analysis
- **Scoring Engine**: `scorer.py` calculates sustainability metrics
- **Database Integration**: `db.py` manages data persistence
- **URL Parsing**: `url_parser.py` handles product URL extraction

### **Data Flow**

1. **Page Visit**: User navigates to Shopee product page
2. **Detection**: Content script identifies product information
3. **Analysis Request**: Data sent to backend API
4. **Processing**: Backend analyzes product using AI/ML models
5. **Score Calculation**: Sustainability metrics computed
6. **Display**: Results shown in floating badge and popup
7. **User Interaction**: Detailed views and recommendations available

### **Scoring Algorithm**

EcoShop uses a weighted scoring system:

```
Final Score = (P×Wp + C×Wc + M×Wm) / (Wp + Wc + Wm) × 10
```

Where:
- **P** = Production and Brand score (0-10)
- **C** = Circularity and End of Life score (0-10) 
- **M** = Material Composition score (0-10)
- **Wp, Wc, Wm** = User-defined weights (1-5)

**Score Ranges:**
- **70-100**: Excellent sustainability (Green)
- **40-69**: Good sustainability (Orange)
- **0-39**: Needs improvement (Red)

---

## 🎯 Features Overview

### **✅ Core Features**
- **Real-time Analysis**: Instant sustainability scoring on product pages
- **Customizable Weights**: Adjust scoring criteria to your values
- **Multi-view Interface**: Summary, detailed analysis, and recommendations
- **Floating Badge**: Unobtrusive on-page sustainability indicator
- **Settings Sync**: Preferences saved across browser sessions

### **🎨 User Experience**
- **Progressive Loading**: Smooth loading with status messages
- **Responsive Design**: Works on all screen sizes
- **Theme Support**: Dark/light mode options
- **Accessibility**: Senior mode for improved readability
- **Intuitive Navigation**: Easy movement between features

### **🔧 Technical Features**
- **Anti-Spam Protection**: Single request per product page
- **Intelligent Caching**: Optimized performance
- **Error Handling**: Graceful degradation when services unavailable
- **Cross-browser Support**: Works on all Chromium browsers
- **Secure Communication**: HTTPS API endpoints with CORS

### **📊 Data & Analytics**
- **Three-Factor Analysis**: Comprehensive sustainability assessment
- **Detailed Breakdowns**: Understand why products score as they do
- **Comparative Data**: See how products stack up against alternatives
- **Transparency**: Clear data sources and analysis methodology

---

## 🚀 Development & Architecture

### **Project Structure**
```
EcoShop/
├── extension/                 # Browser extension files
│   ├── manifest.json         # Extension configuration
│   ├── content.js            # Product page interaction
│   ├── service_worker.js     # Background processing
│   ├── popup/                # Main interface
│   │   ├── popup.html        # Main popup UI
│   │   ├── popup.js          # Popup logic
│   │   ├── details.html      # Detailed analysis view
│   │   ├── recommendations.html # Alternative products
│   │   └── popup.css         # Styling
│   ├── options/              # Settings page
│   │   ├── options.html      # Settings UI
│   │   ├── options.js        # Settings logic
│   │   └── options.css       # Settings styling
│   └── icons/                # Extension icons
├── backend/                  # Analysis API
│   ├── app.py               # Flask web server
│   ├── requirements.txt     # Python dependencies
│   └── scripts/             # Analysis modules
└── data/                    # Sample data files
```

### **Technology Stack**
- **Frontend**: JavaScript (ES6+), HTML5, CSS3
- **Backend**: Python, Flask, REST API
- **Browser**: Chrome Extension Manifest V3
- **Storage**: Chrome Storage API, Local Storage
- **Communication**: HTTP/HTTPS, Chrome Messaging API

---

## 🌍 Environmental Impact

EcoShop helps users make more sustainable shopping choices by:

- **Transparency**: Revealing the environmental impact of products
- **Education**: Teaching users about sustainability factors
- **Alternatives**: Suggesting eco-friendly product options
- **Awareness**: Highlighting sustainable brands and practices

**Every sustainable choice matters. EcoShop makes it easier to shop with the planet in mind.** 🌱

---

## 📞 Support & Contributing

- **Issues**: Report bugs or request features via GitHub Issues
- **Documentation**: This README covers all features and usage
- **Development**: See code comments for technical implementation details

**Happy sustainable shopping!** 🛒🌱
Server runs on `http://localhost:5000` with detailed logging.

### 2. **Extension Installation**
1. Open Chrome → `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" → Select `extension/` folder
4. Visit any Shopee product page to test

### 3. **Test the Current System**
Visit any Shopee product page (e.g., Sony headphones) and check:
- ✅ Console logs show product extraction
- ✅ Backend logs show received data
- ✅ Sustainability badge appears (test score: 75)
- ✅ No request spamming

## 📊 **Data Flow Example**

**Current Working Example (Sony WH-1000XM5 on Shopee):**
```json
{
  "brand": "Sony",
  "name": "Sony WH-1000XM5 Wireless Noise Cancelling Headphones",
  "specifications": {
    "category": "Audio > Headphones",
    "brand": "Sony", 
    "connection type": "Wireless",
    "warranty duration": "12 Months",
    "product ratings": "4.9 out of 5 (719 ratings)"
  }
}
```

**Backend Response (Test Mode):**
```json
{
  "success": true,
  "data": {
    "brand": "Sony",
    "score": 75,
    "co2e": 2.5,
    "waterUsage": "low",
    "wasteGenerated": "low", 
    "laborPractices": "good",
    "certainty": "high",
    "message": "Test data for Sony - MongoDB not connected"
  },
  "status": "test_mode"
}
```

## 🔗 **LLM Integration Requirements**

### **Phase 1: Basic LLM Integration**

**Required:** An LLM service that can process the task queue and update MongoDB.

**Implementation Approach:**
1. **Monitor Tasks Collection:**
   ```python
   # backend/llm_processor.py (to be created)
   import pymongo
   from backend.config import *
   
   def process_pending_tasks():
       client = MongoClient(MONGO_URI)
       db = client[MONGO_DB]
       tasks = db[MONGO_TASKS_COLLECTION]
       
       # Find tasks with status 'new'
       pending = tasks.find({"status": "new"})
       
       for task in pending:
           # Update status to 'processing'
           update_task_status(client, str(task["_id"]), "processing")
           
           # Call your LLM API
           result = analyze_product_sustainability(task)
           
           # Update with final results
           update_task_status(client, str(task["_id"]), "done", 
                            score=result["score"], 
                            summary=result["summary"])
   ```

2. **LLM Analysis Function:**
   ```python
   def analyze_product_sustainability(task):
       product_data = {
           "brand": task.get("brand", ""),
           "name": task.get("productName", ""),
           "specs": task.get("metadata", {})
       }
       
       # Your LLM prompt/API call here
       prompt = f"""
       Analyze sustainability for: {product_data['brand']} - {product_data['name']}
       Specifications: {product_data['specs']}
       
       Return JSON with:
       - score (0-100)
       - co2e (estimated CO2 impact)
       - waterUsage (low/medium/high)
       - wasteGenerated (low/medium/high) 
       - laborPractices (poor/fair/good/excellent)
       - summary (brief explanation)
       """
       
       # Process with your LLM and return structured result
       return llm_response
   ```

### **Phase 2: Real-Time Change Streams**

**When LLM integration is complete:**

1. **Start the LLM processor:**
   ```powershell
   python backend/llm_processor.py
   ```

2. **Extension automatically switches to real-time mode:**
   - Creates tasks via `/api/tasks`
   - Monitors via `/api/watch/<task_id>` 
   - Receives live updates as LLM processes

3. **Change Streams push updates:**
   ```javascript
   // Extension receives real-time updates
   eventSource.onmessage = function(event) {
       const update = JSON.parse(event.data);
       if (update.status === 'done') {
           displaySustainabilityBadge(update.data);
       }
   };
   ```

## 🛠️ **Configuration**

**MongoDB Setup (`backend/config.py`):**
```python
MONGO_URI = "your_mongodb_atlas_connection_string"
MONGO_DB = "LifeHackData"
MONGO_PRODUCTS_COLLECTION = "alldata"  
MONGO_TASKS_COLLECTION = "tasks"
USE_CHANGE_STREAMS = True  # Enable for real-time mode
```

**Feature Flags:**
- `USE_CHANGE_STREAMS=false` → Falls back to test mode
- `DEBUG=true` → Enhanced logging
- `CHANGE_STREAM_TIMEOUT=300` → 5-minute SSE timeout

## 📁 **File Structure**

```
├── backend/
│   ├── app.py                    # 🚀 Main Flask API server
│   ├── config.py                 # ⚙️ Centralized configuration  
│   ├── watch.py                  # 📡 MongoDB Change Streams helper
│   ├── requirements.txt          # 📦 Python dependencies
│   └── scripts/
│       └── export_to_mongo.py    # 💾 Database operations
├── extension/
│   ├── content.js                # 🔍 Shopee page parsing + anti-spam
│   ├── service_worker.js         # 🔄 SSE client + API communication  
│   ├── manifest.json             # 📋 Extension configuration
│   └── popup/                    # 🎨 User interface
├── data/
│   └── esg_scores.json           # 📊 Fallback sustainability data
└── README.md                     # 📖 This documentation
```

## 🔧 **API Endpoints**

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/api/product` | POST | Submit product for analysis | ✅ Working |
| `/api/tasks` | POST | Create analysis task | ✅ Ready |
| `/api/watch/<task_id>` | GET | SSE stream for updates | ✅ Ready |
| `/api/health` | GET | System health check | ✅ Working |

## 🐛 **Current Limitations & Next Steps**

### **Immediate Priorities:**

1. **LLM Integration** - The missing piece for production deployment
2. **MongoDB Connection** - Currently using test mode due to SSL issues
3. **Error Handling** - Improve offline/connection failure scenarios

### **Advanced Features (Future):**

- Multi-site support (Amazon, eBay, etc.)
- User preference learning
- Sustainability trend analysis
- Carbon footprint tracking

## 📝 **Development Notes**

**Current Logging Output Example:**
```
2025-06-17 03:40:36,194 - ecoshop_api - INFO - === PRODUCT DATA RECEIVED ===
2025-06-17 03:40:36,194 - ecoshop_api - INFO - Product Name: Sony WH-1000XM5 Wireless Noise Cancelling Headphones
2025-06-17 03:40:36,194 - ecoshop_api - INFO - Brand: Sony
2025-06-17 03:40:36,194 - ecoshop_api - INFO - Specifications: {category: "Audio", brand: "Sony", ...}
```
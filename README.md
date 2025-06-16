# EcoShop - Real-Time Sustainability Shopping Companion

EcoShop is a production-ready browser extension that provides real-time sustainability analysis for products on e-commerce sites. It leverages MongoDB Change Streams for push-based updates and LLM integration for intelligent sustainability scoring.

## 🏗️ **Current Architecture Status**

### ✅ **Completed Components**

**Extension Frontend:**
- ✅ Robust Shopee page parsing with fallback selectors
- ✅ Anti-spam protection (single request per page)
- ✅ Rich product data extraction (specifications, reviews, pricing)
- ✅ Real-time sustainability badge display
- ✅ Error handling and user feedback

**Backend API:**
- ✅ Flask server with comprehensive logging
- ✅ MongoDB Change Streams infrastructure (`backend/watch.py`)
- ✅ Task-based architecture for async processing
- ✅ SSE (Server-Sent Events) endpoints for real-time updates
- ✅ Test mode fallback (works without MongoDB)
- ✅ CORS and production-ready configuration

**Infrastructure:**
- ✅ Centralized configuration (`backend/config.py`)
- ✅ MongoDB Atlas connection setup
- ✅ Real-time task monitoring system
- ✅ Error handling and graceful degradation

### 🔄 **Integration Points (Ready for LLM)**

The system is designed for seamless LLM integration with the following workflow:

```
1. User visits Shopee product page
2. Extension extracts product data → Backend (/api/product)
3. Backend creates task in MongoDB → Returns task_id
4. Extension subscribes to SSE stream (/api/watch/<task_id>)
5. [LLM INTEGRATION POINT] → LLM analyzes product data
6. LLM updates task status → MongoDB Change Stream triggers
7. SSE pushes real-time update → Extension updates badge
```

## 🚀 **Quick Start**

### 1. **Backend Setup**
```powershell
cd backend
pip install -r requirements.txt
python app.py
```
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
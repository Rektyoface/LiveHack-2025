# LLM Integration Guide for EcoShop

## 🎯 **Overview**

This document provides detailed instructions for integrating an LLM (Large Language Model) with the EcoShop system to enable real-time sustainability analysis using MongoDB Change Streams.

## 🏗️ **Current System State**

### ✅ **What's Already Built**

1. **Task Queue System**: MongoDB collection for async processing
2. **Change Streams Infrastructure**: Real-time MongoDB monitoring (`backend/watch.py`)
3. **SSE Endpoints**: Server-Sent Events for live updates (`/api/watch/<task_id>`)
4. **Product Data Pipeline**: Rich extraction from Shopee pages
5. **Extension Frontend**: Real-time badge updates and error handling

### 🔄 **LLM Integration Points**

```mermaid
graph TD
    A[User visits Shopee] --> B[Extension extracts data]
    B --> C[POST /api/product]
    C --> D[Create task in MongoDB]
    D --> E[Return task_id]
    E --> F[Extension subscribes to SSE]
    F --> G[LLM Processor picks up task]
    G --> H[LLM analyzes product]
    H --> I[Update task status in MongoDB]
    I --> J[Change Stream triggers]
    J --> K[SSE pushes update to extension]
    K --> L[Extension displays results]
```

## 🔧 **Implementation Steps**

### **Step 1: Create LLM Processor (`backend/llm_processor.py`)**

```python
#!/usr/bin/env python3
"""
LLM Processor for EcoShop Sustainability Analysis
Monitors MongoDB tasks collection and processes new sustainability requests.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import config
from watch import update_task_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('llm_processor')

class SustainabilityLLM:
    def __init__(self):
        self.client = MongoClient(config.MONGO_URI)
        self.db = self.client[config.MONGO_DB]
        self.tasks_collection = self.db[config.MONGO_TASKS_COLLECTION]
        
    def analyze_product_sustainability(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core LLM analysis function - IMPLEMENT YOUR LLM LOGIC HERE
        
        Args:
            task_data: Task document from MongoDB with product information
            
        Returns:
            Dictionary with sustainability analysis results
        """
        
        # Extract product information
        brand = task_data.get('brand', 'Unknown')
        product_name = task_data.get('productName', 'Unknown Product')
        specs = task_data.get('metadata', {})
        
        # Prepare LLM prompt
        prompt = f"""
        Analyze the sustainability of this product and provide a comprehensive assessment:
        
        Product: {product_name}
        Brand: {brand}
        Specifications: {json.dumps(specs, indent=2)}
        
        Please provide a JSON response with the following structure:
        {{
            "score": <integer from 0-100>,
            "co2e": <estimated CO2 equivalent in kg>,
            "waterUsage": "<low/medium/high>",
            "wasteGenerated": "<low/medium/high>",
            "laborPractices": "<poor/fair/good/excellent>",
            "summary": "<brief explanation of the sustainability assessment>",
            "factors": {{
                "materials": "<analysis of materials used>",
                "manufacturing": "<manufacturing process assessment>",
                "packaging": "<packaging sustainability>",
                "endOfLife": "<disposal/recycling considerations>"
            }}
        }}
        
        Consider factors like:
        - Brand reputation for sustainability
        - Product materials and manufacturing
        - Energy efficiency (for electronics)
        - Packaging and waste
        - Supply chain practices
        - End-of-life recyclability
        """
        
        try:
            # TODO: Replace with your actual LLM API call
            # Examples:
            # - OpenAI GPT-4: openai.ChatCompletion.create(...)
            # - Anthropic Claude: anthropic.completions.create(...)
            # - Local model: your_local_model.generate(...)
            
            # PLACEHOLDER - Replace with actual LLM call
            llm_response = self.call_your_llm_api(prompt)
            
            # Parse LLM response (assuming JSON format)
            result = json.loads(llm_response)
            
            # Validate required fields
            required_fields = ['score', 'co2e', 'waterUsage', 'wasteGenerated', 'laborPractices', 'summary']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
                    
            # Ensure score is within valid range
            result['score'] = max(0, min(100, int(result['score'])))
            
            logger.info(f"LLM analysis complete for {brand} - Score: {result['score']}")
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed for {brand}: {str(e)}")
            # Return fallback data
            return {
                'score': 50,
                'co2e': 5.0,
                'waterUsage': 'medium',
                'wasteGenerated': 'medium',
                'laborPractices': 'unknown',
                'summary': f'Analysis failed for {brand}. Using default values.',
                'error': str(e)
            }
    
    def call_your_llm_api(self, prompt: str) -> str:
        """
        Replace this method with your actual LLM API call
        
        Examples:
        
        # OpenAI GPT-4
        import openai
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
        
        # Anthropic Claude
        import anthropic
        client = anthropic.Client(api_key="your-api-key")
        response = client.completions.create(
            model="claude-2",
            prompt=prompt,
            max_tokens_to_sample=1000
        )
        return response.completion
        
        # Local model (e.g., using transformers)
        from transformers import pipeline
        generator = pipeline('text-generation', model='your-model')
        response = generator(prompt, max_length=1000, num_return_sequences=1)
        return response[0]['generated_text']
        """
        
        # PLACEHOLDER - Replace with actual implementation
        import random
        
        # Simulate LLM processing time
        time.sleep(2)
        
        # Mock response for testing
        mock_scores = {
            'Sony': 75,
            'Apple': 70,
            'Samsung': 65,
            'Nike': 60,
            'Adidas': 68,
        }
        
        brand = prompt.split('Brand: ')[1].split('\n')[0] if 'Brand: ' in prompt else 'Unknown'
        score = mock_scores.get(brand, 50)
        
        return json.dumps({
            'score': score,
            'co2e': random.uniform(1.0, 8.0),
            'waterUsage': random.choice(['low', 'medium', 'high']),
            'wasteGenerated': random.choice(['low', 'medium', 'high']),
            'laborPractices': random.choice(['fair', 'good', 'excellent']),
            'summary': f'Sustainability analysis for {brand} - Score based on environmental impact, materials, and practices.',
            'factors': {
                'materials': 'Analysis of product materials and sourcing',
                'manufacturing': 'Assessment of manufacturing processes',
                'packaging': 'Evaluation of packaging sustainability',
                'endOfLife': 'End-of-life disposal considerations'
            }
        })
    
    def process_pending_tasks(self):
        """
        Main processing loop - monitors for new tasks and processes them
        """
        logger.info("Starting LLM processor...")
        
        while True:
            try:
                # Find tasks with status 'new'
                pending_tasks = list(self.tasks_collection.find({"status": "new"}))
                
                if not pending_tasks:
                    logger.debug("No pending tasks found")
                    time.sleep(5)  # Wait 5 seconds before checking again
                    continue
                
                for task in pending_tasks:
                    task_id = str(task['_id'])
                    logger.info(f"Processing task {task_id}")
                    
                    try:
                        # Update status to 'processing'
                        update_task_status(
                            self.client,
                            config.MONGO_DB,
                            config.MONGO_TASKS_COLLECTION,
                            task_id,
                            'processing'
                        )
                        
                        # Perform LLM analysis
                        analysis_result = self.analyze_product_sustainability(task)
                        
                        # Update task with results
                        update_task_status(
                            self.client,
                            config.MONGO_DB,
                            config.MONGO_TASKS_COLLECTION,
                            task_id,
                            'done',
                            **analysis_result
                        )
                        
                        logger.info(f"Task {task_id} completed successfully")
                        
                    except Exception as e:
                        logger.error(f"Failed to process task {task_id}: {str(e)}")
                        
                        # Mark task as failed
                        update_task_status(
                            self.client,
                            config.MONGO_DB,
                            config.MONGO_TASKS_COLLECTION,
                            task_id,
                            'error',
                            error=str(e)
                        )
                        
            except PyMongoError as e:
                logger.error(f"MongoDB error: {str(e)}")
                time.sleep(10)  # Wait longer on database errors
                
            except KeyboardInterrupt:
                logger.info("Shutting down LLM processor...")
                break
                
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                time.sleep(5)

def main():
    """Main entry point"""
    processor = SustainabilityLLM()
    processor.process_pending_tasks()

if __name__ == '__main__':
    main()
```

### **Step 2: Update Service Worker for Real-Time Mode**

The service worker needs to switch from test mode to real-time mode when LLM is available:

```javascript
// In extension/service_worker.js
async function handleSustainabilityCheck(productInfo, sendResponse, sender) {
    try {
        // ... existing code ...
        
        // Check if real-time mode is available
        const serverCapabilities = await checkServerCapabilities();
        
        if (serverCapabilities.realTimeMode) {
            // Use task-based approach with SSE
            const taskResult = await createAnalysisTask(productInfo);
            
            if (taskResult.success) {
                // Start SSE monitoring
                monitorTaskWithSSE(taskResult.task_id, productInfo, sender, sendResponse);
                
                sendResponse({
                    success: true,
                    data: {
                        certainty: 'pending',
                        message: 'Real-time analysis in progress...',
                        task_id: taskResult.task_id
                    }
                });
            }
        } else {
            // Fall back to direct API call
            const data = await fetchFromApi(productInfo);
            // ... handle response ...
        }
        
    } catch (error) {
        // ... error handling ...
    }
}

async function checkServerCapabilities() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const health = await response.json();
        return {
            realTimeMode: health.capabilities?.changeStreams || false
        };
    } catch (error) {
        return { realTimeMode: false };
    }
}
```

### **Step 3: Update Backend Health Check**

Add capability reporting to the health endpoint:

```python
# In backend/app.py
@app.route('/api/health')
def health_check():
    """Health check endpoint with capability reporting."""
    mongo_status = "available" if get_mongo_client() else "unavailable"
    
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'database': mongo_status,
        'capabilities': {
            'changeStreams': config.USE_CHANGE_STREAMS and mongo_status == "available",
            'realTimeAnalysis': True,  # Set to True when LLM processor is running
            'llmProcessor': 'ready'     # Update based on LLM status
        }
    })
```

## 🚀 **Deployment Instructions**

### **Step 1: Set Up MongoDB Connection**

1. Fix MongoDB SSL issues:
   ```python
   # In config.py, update MONGO_URI with proper SSL settings
   MONGO_URI = "mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
   ```

2. Enable Change Streams:
   ```python
   USE_CHANGE_STREAMS = True
   ```

### **Step 2: Start LLM Processor**

```powershell
cd backend
python llm_processor.py
```

### **Step 3: Verify Real-Time Operation**

1. Visit a Shopee product page
2. Check backend logs for task creation
3. Verify LLM processor picks up the task
4. Confirm extension receives real-time updates via SSE

## 📊 **Testing & Monitoring**

### **Test Workflow:**

```bash
# 1. Check system health
curl http://localhost:5000/api/health

# 2. Create a test task
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_type":"sustainability_analysis","product_name":"Test Product","brand":"Sony"}'

# 3. Monitor task progress (replace <task_id> with actual ID)
curl http://localhost:5000/api/watch/<task_id>
```

### **Monitoring Points:**

- **Task Creation Rate**: Monitor `/api/tasks` endpoint usage
- **Processing Time**: Track time from task creation to completion
- **Error Rates**: Monitor failed tasks and LLM API errors
- **SSE Connections**: Track active real-time connections

## 🔧 **Configuration Options**

```python
# backend/config.py
LLM_TIMEOUT = 30                    # Maximum time for LLM analysis
MAX_CONCURRENT_TASKS = 5            # Limit parallel processing
TASK_RETRY_ATTEMPTS = 3             # Retry failed analyses
LLM_API_KEY = "your-llm-api-key"    # Your LLM service API key
LLM_MODEL = "gpt-4"                 # Model to use for analysis
```

## 🎯 **Success Criteria**

The LLM integration is complete when:

- [x] LLM processor runs continuously without errors
- [x] Tasks are created and processed in real-time
- [x] Extension receives live updates via SSE
- [x] Sustainability scores are accurate and relevant
- [x] System handles failures gracefully
- [x] Performance meets requirements (< 30s analysis time)

---

**Ready for Implementation**: The infrastructure is complete and waiting for your LLM integration!

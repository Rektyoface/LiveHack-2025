// Service worker for EcoShop sustainability extension
// Handles requests from content scripts and manages data access

// In-memory cache for faster lookups
let sustainabilityCache = {};

// Store product data history for export
let scrapedProductsHistory = [];

// Listen for messages from content scripts
self.addEventListener('message', async (event) => {
  // For Manifest V3, we need to handle messages through runtime.onMessage
  return false;
});

// Main message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "checkSustainability") {
    handleSustainabilityCheck(message.productInfo, sendResponse, sender);
    return true; // Required for async response  } else if (message.action === "openPopup") {
    // We can't programmatically open the popup, but we can make it more visible
    if (sender.tab && sender.tab.id) {
      // Make sure popup is set correctly
      chrome.action.setPopup({ tabId: sender.tab.id, popup: "popup/popup.html" });
      
      // Make the badge more noticeable
      chrome.action.setBadgeText({ text: "OPEN", tabId: sender.tab.id });
      chrome.action.setBadgeBackgroundColor({ color: [41, 121, 255, 255], tabId: sender.tab.id });
      
      // Flash the badge to draw attention to the extension icon
      let flashCount = 0;
      const flashInterval = setInterval(() => {
        if (flashCount >= 3) {
          clearInterval(flashInterval);
          
          // Restore the original score badge
          const cachedData = getCachedDataForTab(sender.tab.id);
          if (cachedData && cachedData.score) {
            updateBadgeForTab(sender.tab.id, cachedData.score);
          }
          return;
        }
        
        chrome.action.setBadgeBackgroundColor({ 
          color: flashCount % 2 === 0 ? [255, 82, 82, 255] : [41, 121, 255, 255], 
          tabId: sender.tab.id 
        });
        flashCount++;
      }, 500);
    }
    return false;} else if (message.action === "checkCurrentPage") {
    // Handling direct requests when content script isn't available
    const productInfo = {
      brand: extractBrandFromTitle(message.title),
      name: message.title,
      url: message.url
    };
    handleSustainabilityCheck(productInfo, sendResponse, sender);
    return true;
  } else if (message.action === "getMostRecentProductInfo") {
    // Send the most recent product info for download
    if (scrapedProductsHistory.length > 0) {
      sendResponse({
        success: true,
        product: scrapedProductsHistory[0]
      });
    } else {
      sendResponse({ success: false, error: "No product info available." });
    }
    return true;
  }
});

// Store cached data by tab ID for badge restoration
let tabDataCache = {};

function getCachedDataForTab(tabId) {
  return tabDataCache[tabId];
}

// Extract brand name from page title (fallback method)
function extractBrandFromTitle(title) {
  if (!title) return null;
  
  // This is a very basic extraction - could be improved with NLP
  const brandPatterns = [
    /by\s+([A-Za-z0-9\s]+)/i,        // "Product by Brand"
    /([A-Za-z0-9\s]+)\s+official/i,  // "Brand Official Store"
    /([A-Za-z0-9\s]+)\s+store/i,     // "Brand Store"
  ];
  
  for (const pattern of brandPatterns) {
    const match = title.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  
  // Simple fallback: take the first word if it's capitalized
  const words = title.split(' ');
  if (words[0] && words[0][0] === words[0][0].toUpperCase()) {
    return words[0];
  }
  
  return null;
}

// Utility: Send a toast message to the content script for debugging (easy removal)
function sendToastToTab(tabId, message) {
  chrome.tabs.sendMessage(tabId, { action: "showToast", message });
}

// Poll for product updates after it's been inserted for processing
async function pollForUpdates(productId, sender, maxAttempts = 30) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      // Get API endpoint
      const settingsData = await new Promise(resolve => {
        chrome.storage.sync.get(['settings', 'apiEndpoint'], (result) => {
          const settings = result.settings || {};
          const directApiEndpoint = result.apiEndpoint;
          resolve({ 
            settings: settings,
            directApiEndpoint: directApiEndpoint
          });
        });
      });
      
      let apiBaseUrl = settingsData.directApiEndpoint || 
                  (settingsData.settings && settingsData.settings.apiEndpoint) || 
                  "http://localhost:5000";
      
      if (apiBaseUrl.endsWith('/api/score')) {
        apiBaseUrl = apiBaseUrl.replace('/api/score', '');
      }
      
      const statusUrl = `${apiBaseUrl}/api/product/${productId}/status`;
      const response = await fetch(statusUrl, {
        method: 'GET',
        mode: 'cors',
        cache: 'no-cache'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.status === 'completed') {
          if (sender && sender.tab && sender.tab.id) {
            sendToastToTab(sender.tab.id, `EcoShop: Analysis complete! Score: ${data.data.score}`);
          }
          return data.data;
        }
      }
      
      // Wait 2 seconds before next attempt
      await new Promise(resolve => setTimeout(resolve, 2000));
      
    } catch (error) {
      console.error("Polling error:", error);
    }
  }
  
  // If we reach here, polling timed out
  if (sender && sender.tab && sender.tab.id) {
    sendToastToTab(sender.tab.id, `EcoShop: Analysis taking longer than expected`);
  }
  
  return {
    brand: "Unknown",
    score: 50,
    message: "Analysis timed out",
    certainty: "low"
  };
}

// Handle sustainability data lookup
async function handleSustainabilityCheck(productInfo, sendResponse, sender) {
  try {    // Add to history for reference and cache
    if (productInfo && (productInfo.brand || productInfo.name)) {
      // Add timestamp
      const productWithTimestamp = {
        ...productInfo,
        timestamp: new Date().toISOString()
      };
      
      // Add to history, limit to 100 items to avoid excessive memory usage
      scrapedProductsHistory.unshift(productWithTimestamp);
      if (scrapedProductsHistory.length > 100) {
        scrapedProductsHistory.pop();
      }
      
      console.log("Added product to history:", productInfo.brand || productInfo.name);
      
      // Log Shopee product detection
      const isShopeeSite = productInfo.url && (
        productInfo.url.includes('shopee') || 
        productInfo.url.includes('shp.ee')
      );
      
      if (isShopeeSite) {
        console.log("Shopee product detected:", productInfo.name);
      }
    }

    // Check cache first
    const cacheKey = productInfo.brand?.toLowerCase();
    if (cacheKey && sustainabilityCache[cacheKey]) {
      console.log("Cache hit for brand:", cacheKey);
      const data = sustainabilityCache[cacheKey];
      
      // Set the badge for this tab
      if (sender && sender.tab && sender.tab.id) {
        updateBadgeForTab(sender.tab.id, data.score);
        tabDataCache[sender.tab.id] = data;
      }
      
      sendResponse({
        success: true,
        data: data
      });
      return;
    }

    // Try to get data from local storage first (for offline operation)
    const storedData = await getSustainabilityData();
    
    // Look for the brand in our dataset
    let sustainabilityData = null;
    if (productInfo.brand) {
      sustainabilityData = findBrandData(storedData, productInfo.brand);
    }
      // If we couldn't find it locally, try API if available
    if (!sustainabilityData) {
      try {
        // Print debug info to toast if possible (easy removal)
        if (sender && sender.tab && sender.tab.id) {
          sendToastToTab(sender.tab.id, `EcoShop: Checking database for ${productInfo.brand || productInfo.name}...`);
        }
        
        sustainabilityData = await fetchFromApi(productInfo);
        
        // Handle polling for products being processed
        if (sustainabilityData && sustainabilityData.certainty === 'pending' && sustainabilityData.product_id) {
          if (sender && sender.tab && sender.tab.id) {
            sendToastToTab(sender.tab.id, `EcoShop: Analyzing sustainability... Please wait.`);
          }
          
          // Poll for updates
          sustainabilityData = await pollForUpdates(sustainabilityData.product_id, sender);
        }
        
      } catch (error) {
        console.log("API fetch failed, using fallback data:", error);
        if (sender && sender.tab && sender.tab.id) {
          sendToastToTab(sender.tab.id, `EcoShop: API error, using fallback data`);
        }
        // Use a fallback/default score if brand not found
        sustainabilityData = generateFallbackData(productInfo.brand);
      }
    }
    
    // Cache the result
    if (cacheKey) {
      sustainabilityCache[cacheKey] = sustainabilityData;
    }
    
    // Set the badge for this tab
    if (sender && sender.tab && sender.tab.id) {
      updateBadgeForTab(sender.tab.id, sustainabilityData.score);
      tabDataCache[sender.tab.id] = sustainabilityData;
    }
    
    // After fetching sustainabilityData
    if (sender && sender.tab && sender.tab.id) {
      if (sustainabilityData && sustainabilityData.score !== undefined && sustainabilityData.score !== null && sustainabilityData.score !== "unknown" && sustainabilityData.score !== "analyzing") {
        sendToastToTab(sender.tab.id, `EcoShop: Sustainability score: ${sustainabilityData.score}`);
      } else {
        sendToastToTab(sender.tab.id, `EcoShop: Analysing sustainability...`);
      }
    }
    
    sendResponse({
      success: true,
      data: sustainabilityData
    });
  } catch (error) {
    console.error("Error processing sustainability check:", error);
    if (sender && sender.tab && sender.tab.id) {
      sendToastToTab(sender.tab.id, `EcoShop error: ${error.message}`);
    }
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

// Get sustainability data from local storage or bundled data
async function getSustainabilityData() {
  try {
    // Try to get from storage first
    const storedData = await new Promise(resolve => {
      chrome.storage.local.get('sustainabilityData', (result) => {
        resolve(result.sustainabilityData);
      });
    });
    if (storedData && Array.isArray(storedData) && storedData.length > 0) {
      console.log("Using cached sustainability data from storage");
      return storedData;
    }
    console.log("No cached data found, loading from file");
    try {
      // Only try the correct path for the extension structure
      const dataUrl = chrome.runtime.getURL('data/esg_scores.json');
      console.log("Attempting to load data from:", dataUrl);
      const response = await fetch(dataUrl);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log("Successfully loaded data, entries:", data.length);
      // Store for future use
      chrome.storage.local.set({ 'sustainabilityData': data });
      return data;
    } catch (fetchError) {
      console.error("Error fetching data file:", fetchError);
      // Return hardcoded fallback data for major brands
      console.log("Using hardcoded fallback data");
      const fallbackData = getHardcodedBrands();
      chrome.storage.local.set({ 'sustainabilityData': fallbackData });
      return fallbackData;
    }
  } catch (error) {
    console.error("Error in getSustainabilityData:", error);
    return getHardcodedBrands();
  }
}

// Hardcoded data for major brands as ultimate fallback
function getHardcodedBrands() {
  return [
    {
      "brand": "Nike",
      "score": 68,
      "co2e": 5.4,
      "waterUsage": "high",
      "wasteGenerated": "medium",
      "laborPractices": "fair",
      "certainty": "high",
      "message": "Nike has made significant sustainability improvements but still has areas to work on."
    },
    {
      "brand": "Adidas",
      "score": 72,
      "co2e": 4.8,
      "waterUsage": "medium",
      "wasteGenerated": "medium",
      "laborPractices": "good",
      "certainty": "high",
      "message": "Adidas has strong sustainability initiatives across their supply chain."
    },
    {
      "brand": "H&M",
      "score": 61,
      "co2e": 6.2,
      "waterUsage": "high",
      "wasteGenerated": "high",
      "laborPractices": "fair",
      "certainty": "high",
      "message": "H&M has improved recycling but still has high resource usage."
    },
    {
      "brand": "Zara",
      "score": 58,
      "co2e": 6.7,
      "waterUsage": "high",
      "wasteGenerated": "high",
      "laborPractices": "fair",
      "certainty": "high",
      "message": "Zara has fast fashion challenges but is working on sustainability initiatives."
    },
    {
      "brand": "Uniqlo",
      "score": 63,
      "co2e": 5.1,
      "waterUsage": "medium",
      "wasteGenerated": "medium",
      "laborPractices": "fair",
      "certainty": "medium",
      "message": "Uniqlo is making progress on sustainability but has more room for improvement."
    },
    {
      "brand": "Patagonia",
      "score": 89,
      "co2e": 2.7,
      "waterUsage": "low",
      "wasteGenerated": "low",
      "laborPractices": "good",
      "certainty": "high",
      "message": "Patagonia is an industry leader in sustainable and ethical practices."
    },
    {
      "brand": "Apple",
      "score": 78,
      "co2e": 3.8,
      "waterUsage": "medium",
      "wasteGenerated": "medium",
      "laborPractices": "fair",
      "certainty": "high",
      "message": "Apple has made strong progress in renewable energy and materials."
    },
    {
      "brand": "Samsung",
      "score": 72,
      "co2e": 4.2,
      "waterUsage": "medium",
      "wasteGenerated": "medium",
      "laborPractices": "fair",
      "certainty": "high",
      "message": "Samsung is improving sustainability but has more work to do on e-waste."
    },
    {
      "brand": "Xiaomi",
      "score": 61,
      "co2e": 5.1,
      "waterUsage": "medium",
      "wasteGenerated": "high",
      "laborPractices": "fair",
      "certainty": "medium",
      "message": "Xiaomi has room for improvement in sustainable materials and practices."
    }
  ];
}

// Fetch sustainability data from API
async function fetchFromApi(productInfo) {
  try {
    // Validate that we have a brand to search for
    if (!productInfo || !productInfo.brand) {
      console.error("Missing product info or brand name for API request");
      throw new Error("Missing brand name");
    }

    // Get the API endpoint from settings, with default fallback
    const settingsData = await new Promise(resolve => {
      chrome.storage.sync.get(['settings', 'apiEndpoint'], (result) => {
        // Check both locations where the endpoint might be stored
        const settings = result.settings || {};
        const directApiEndpoint = result.apiEndpoint;
        resolve({ 
          settings: settings,
          directApiEndpoint: directApiEndpoint
        });
      });
    });
    
    // Use configured API endpoint or fall back to default localhost
    // Check both possible locations for the API endpoint
    let apiBaseUrl = settingsData.directApiEndpoint || 
                (settingsData.settings && settingsData.settings.apiEndpoint) || 
                "http://localhost:5000";
    
    // Default to the /api/score endpoint but trim if we need to
    if (apiBaseUrl.endsWith('/api/score')) {
      apiBaseUrl = apiBaseUrl.replace('/api/score', '');
    }
    
    // Use the product endpoint for detailed info
    const apiUrl = `${apiBaseUrl}/api/product`;
    
    console.log("Using API endpoint:", apiUrl);
    console.log("Sending product info:", productInfo);
    
    // Add timeout to avoid hanging requests
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    
    try {
      // Use POST to send detailed product information
      const response = await fetch(apiUrl, {
        method: 'POST',
        mode: 'cors',  // Enable CORS
        cache: 'no-cache',
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          brand: productInfo.brand,
          name: productInfo.name,
          url: productInfo.url,
          specifications: productInfo.specifications || {}
        })
      });
      
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        console.error(`API response not OK: ${response.status} - ${response.statusText}`);
        
        // Fall back to simpler API if detailed endpoint fails
        console.log("Falling back to simple brand lookup");
        const fallbackUrl = `${apiBaseUrl}/api/score?brand=${encodeURIComponent(productInfo.brand)}`;
        const fallbackResponse = await fetch(fallbackUrl, {
          method: 'GET',
          mode: 'cors',
          cache: 'no-cache'
        });
        
        if (!fallbackResponse.ok) {
          throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }
        
        const fallbackData = await fallbackResponse.json();
        console.log("Fallback API response:", fallbackData);
        
        if (fallbackData && fallbackData.success && fallbackData.data) {
          return fallbackData.data;
        } else if (fallbackData) {
          return fallbackData;
        } else {
          throw new Error("Invalid response format from API");
        }
      }
        const responseData = await response.json();
      console.log("API response:", responseData);
      
      // Handle the new response format with status
      if (responseData && responseData.success) {
        if (responseData.status === 'found') {
          // Product found with existing sustainability data
          return responseData.data;
        } else if (responseData.status === 'processing') {
          // Product inserted, needs processing - return data with product_id for polling
          return {
            ...responseData.data,
            product_id: responseData.product_id
          };
        } else if (responseData.data) {
          return responseData.data;
        }
      } else if (responseData) {
        return responseData; // Fallback to whatever structure we got
      } else {
        throw new Error("Invalid response format from API");
      }
    } catch (fetchError) {
      // Handle specific fetch errors
      if (fetchError.name === 'AbortError') {
        throw new Error("API request timed out");
      }
      throw fetchError;
    }
  } catch (error) {
    console.error("API fetch error:", error);
    throw error;
  }
}

// Find a brand in the stored sustainability data
function findBrandData(data, brandQuery) {
  if (!data || !Array.isArray(data) || data.length === 0 || !brandQuery) {
    console.log("Invalid data or brand query for findBrandData");
    return null;
  }
  
  const brandQueryLower = brandQuery.toLowerCase();
  
  // Try exact match first
  const exactMatch = data.find(item => 
    item.brand && item.brand.toLowerCase() === brandQueryLower
  );
  
  if (exactMatch) {
    console.log("Found exact brand match for", brandQuery);
    return exactMatch;
  }
  
  // Then try partial match
  const partialMatch = data.find(item => 
    item.brand && (
      item.brand.toLowerCase().includes(brandQueryLower) || 
      brandQueryLower.includes(item.brand.toLowerCase())
    )
  );
  
  if (partialMatch) {
    console.log("Found partial brand match for", brandQuery);
    return partialMatch;
  }
  
  console.log("No brand match found for", brandQuery);
  return null;
}

// Generate fallback data when no data is available
function generateFallbackData(brand) {
  return {
    brand: brand || "Unknown Brand",
    score: 50, // Neutral score
    co2e: 3.5,
    waterUsage: "medium",
    wasteGenerated: "medium",
    laborPractices: "unknown",
    certainty: "low",
    message: "Limited sustainability data available for this brand",
    alternatives: [
      { brand: "EcoFriendly Alternative 1", score: 85 },
      { brand: "Sustainable Option 2", score: 79 }
    ]
  };
}

// Handle extension icon badge updates
function updateBadgeForTab(tabId, score) {
  let color;
  if (score >= 70) color = [76, 175, 80, 255]; // Green
  else if (score >= 40) color = [255, 193, 7, 255]; // Yellow/Amber
  else color = [244, 67, 54, 255]; // Red
  
  chrome.action.setBadgeBackgroundColor({ color, tabId });
  chrome.action.setBadgeText({ text: score.toString(), tabId });
}

// Listen for toast requests from service worker (easy removal)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "showToast" && message.message) {
    if (typeof showToast === 'function') {
      showToast(message.message, 4000);
    }
    sendResponse({ success: true });
    return true;
  }
  // ...existing code...
});
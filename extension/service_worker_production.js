// Service worker for EcoShop sustainability extension - Production Version
// This extension requires database connectivity - no offline fallbacks

// In-memory cache for faster lookups
let sustainabilityCache = {};

// Store product data history for reference
let scrapedProductsHistory = [];

// Store cached data by tab ID for badge restoration
let tabDataCache = {};

// Main message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "checkSustainability") {
    handleSustainabilityCheck(message.productInfo, sendResponse, sender);
    return true; // Required for async response
  } else if (message.action === "openPopup") {
    // Make the badge more noticeable
    if (sender.tab && sender.tab.id) {
      chrome.action.setPopup({ tabId: sender.tab.id, popup: "popup/popup.html" });
      chrome.action.setBadgeText({ text: "OPEN", tabId: sender.tab.id });
      chrome.action.setBadgeBackgroundColor({ color: [41, 121, 255, 255], tabId: sender.tab.id });
      
      // Flash the badge to draw attention
      let flashCount = 0;
      const flashInterval = setInterval(() => {
        if (flashCount >= 3) {
          clearInterval(flashInterval);
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
    return false;
  } else if (message.action === "checkCurrentPage") {
    const productInfo = {
      brand: extractBrandFromTitle(message.title),
      name: message.title,
      url: message.url
    };
    handleSustainabilityCheck(productInfo, sendResponse, sender);
    return true;
  } else if (message.action === "getMostRecentProductInfo") {
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

function getCachedDataForTab(tabId) {
  return tabDataCache[tabId];
}

// Extract brand name from page title (fallback method)
function extractBrandFromTitle(title) {
  if (!title) return null;
  
  const brandPatterns = [
    /by\\s+([A-Za-z0-9\\s]+)/i,
    /([A-Za-z0-9\\s]+)\\s+official/i,
    /([A-Za-z0-9\\s]+)\\s+store/i,
  ];
  
  for (const pattern of brandPatterns) {
    const match = title.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }
  
  const words = title.split(' ');
  if (words[0] && words[0][0] === words[0][0].toUpperCase()) {
    return words[0];
  }
  
  return null;
}

// Send toast message to content script
function sendToastToTab(tabId, message) {
  chrome.tabs.sendMessage(tabId, { action: "showToast", message });
}

// Poll for product updates after it's been inserted for processing
async function pollForUpdates(productId, sender, maxAttempts = 30) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
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
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
    } catch (error) {
      console.error("Polling error:", error);
    }
  }
  
  if (sender && sender.tab && sender.tab.id) {
    sendToastToTab(sender.tab.id, `EcoShop: Analysis taking longer than expected`);
  }
  
  // Return error instead of fallback data
  throw new Error("Analysis timed out - database connection may be unavailable");
}

// Handle sustainability data lookup - Production version requires database connection
async function handleSustainabilityCheck(productInfo, sendResponse, sender) {
  try {
    console.log("Product info received:", productInfo);
    
    // Add to history for reference
    if (productInfo && (productInfo.brand || productInfo.name)) {
      const productWithTimestamp = {
        ...productInfo,
        timestamp: new Date().toISOString()
      };
      
      scrapedProductsHistory.unshift(productWithTimestamp);
      if (scrapedProductsHistory.length > 100) {
        scrapedProductsHistory.pop();
      }
      
      console.log("Added product to history:", productInfo.brand || productInfo.name);
    }
    
    // Check cache first
    const cacheKey = productInfo.brand?.toLowerCase();
    if (cacheKey && sustainabilityCache[cacheKey]) {
      console.log("Cache hit for brand:", cacheKey);
      const data = sustainabilityCache[cacheKey];
      
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

    // Production extension requires database connection - no local fallbacks
    let sustainabilityData = null;
    
    try {
      if (sender && sender.tab && sender.tab.id) {
        sendToastToTab(sender.tab.id, `EcoShop: Checking database for ${productInfo.brand || productInfo.name}...`);
      }
      
      sustainabilityData = await fetchFromApi(productInfo);
      
      // Handle polling for products being processed
      if (sustainabilityData && sustainabilityData.certainty === 'pending' && sustainabilityData.product_id) {
        if (sender && sender.tab && sender.tab.id) {
          sendToastToTab(sender.tab.id, `EcoShop: Analyzing sustainability... Please wait.`);
        }
        
        sustainabilityData = await pollForUpdates(sustainabilityData.product_id, sender);
      }
      
    } catch (error) {
      console.log("Database connection failed:", error);
      if (sender && sender.tab && sender.tab.id) {
        sendToastToTab(sender.tab.id, `EcoShop: Database connection failed. Please check your internet connection.`);
      }
      
      sendResponse({
        success: false,
        error: "Database connection required for sustainability data",
        message: "This extension requires an active database connection. Please ensure you have internet connectivity and the database is available."
      });
      return;
    }
    
    // Cache the result if we got valid data
    if (sustainabilityData && cacheKey) {
      sustainabilityCache[cacheKey] = sustainabilityData;
    }
    
    // Set the badge for this tab
    if (sender && sender.tab && sender.tab.id && sustainabilityData) {
      updateBadgeForTab(sender.tab.id, sustainabilityData.score);
      tabDataCache[sender.tab.id] = sustainabilityData;
      
      const message = `EcoShop: ${sustainabilityData.brand} - Score: ${sustainabilityData.score}/100`;
      sendToastToTab(sender.tab.id, message);
    }
    
    sendResponse({
      success: !!sustainabilityData,
      data: sustainabilityData,
      error: sustainabilityData ? null : "No sustainability data available"
    });
    
  } catch (error) {
    console.error("Error in handleSustainabilityCheck:", error);
    sendResponse({
      success: false,
      error: "Internal error occurred"
    });
  }
}

// Fetch sustainability data from API - Production version only
async function fetchFromApi(productInfo) {
  try {
    if (!productInfo || !productInfo.brand) {
      console.error("Missing product info or brand name for API request");
      throw new Error("Missing brand name");
    }

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
    
    const apiUrl = `${apiBaseUrl}/api/product`;
    
    console.log("Using API endpoint:", apiUrl);
    console.log("Sending product info:", productInfo);
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    
    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        mode: 'cors',
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
        
        // Try simpler brand lookup endpoint
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
        } else {
          throw new Error("No data available for this brand");
        }
      }
      
      const responseData = await response.json();
      console.log("API response:", responseData);
      
      if (responseData && responseData.success) {
        if (responseData.status === 'found') {
          return responseData.data;
        } else if (responseData.status === 'processing') {
          return {
            ...responseData.data,
            product_id: responseData.product_id
          };
        } else if (responseData.data) {
          return responseData.data;
        }
      }
      
      throw new Error("Invalid response format from API");
      
    } catch (fetchError) {
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

// Handle extension icon badge updates
function updateBadgeForTab(tabId, score) {
  let color;
  if (score >= 70) color = [76, 175, 80, 255]; // Green
  else if (score >= 40) color = [255, 193, 7, 255]; // Yellow/Amber
  else color = [244, 67, 54, 255]; // Red
  
  chrome.action.setBadgeBackgroundColor({ color, tabId });
  chrome.action.setBadgeText({ text: score.toString(), tabId });
}

// Listen for toast requests
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "showToast" && message.message) {
    if (typeof showToast === 'function') {
      showToast(message.message, 4000);
    }
    sendResponse({ success: true });
    return true;
  }
});

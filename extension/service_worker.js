// Service worker for EcoShop sustainability extension
// Handles requests from content scripts and manages data access

// In-memory cache for faster lookups
let sustainabilityCache = {};

// Listen for messages from content scripts
self.addEventListener('message', async (event) => {
  // For Manifest V3, we need to handle messages through runtime.onMessage
  return false;
});

// Main message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "checkSustainability") {
    handleSustainabilityCheck(message.productInfo, sendResponse, sender);
    return true; // Required for async response
  } else if (message.action === "openPopup") {
    // We can't programmatically open the popup, but we can make sure the badge is visible
    // and let the user know they need to click the extension icon
    if (sender.tab && sender.tab.id) {
      chrome.action.setPopup({ tabId: sender.tab.id, popup: "popup/popup.html" });
      // Make the badge more noticeable by briefly changing the text
      chrome.action.setBadgeText({ text: "OPEN", tabId: sender.tab.id });
      setTimeout(() => {
        // Restore the original score badge after a brief moment
        const cachedData = getCachedDataForTab(sender.tab.id);
        if (cachedData && cachedData.score) {
          updateBadgeForTab(sender.tab.id, cachedData.score);
        }
      }, 1500);
    }
    return false;
  } else if (message.action === "checkCurrentPage") {
    // Handling direct requests when content script isn't available
    const productInfo = {
      brand: extractBrandFromTitle(message.title),
      name: message.title,
      url: message.url
    };
    handleSustainabilityCheck(productInfo, sendResponse, sender);
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

// Handle sustainability data lookup
async function handleSustainabilityCheck(productInfo, sendResponse, sender) {
  try {
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
        sustainabilityData = await fetchFromApi(productInfo);
      } catch (error) {
        console.log("API fetch failed, using fallback data:", error);
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
    
    sendResponse({
      success: true,
      data: sustainabilityData
    });
  } catch (error) {
    console.error("Error processing sustainability check:", error);
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
      // First try with the correct path for the extension structure
      const dataUrl = chrome.runtime.getURL('data/esg_scores.json');
      console.log("Attempting to load data from:", dataUrl);
      
      const response = await fetch(dataUrl);
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Successfully loaded data, entries:", data.length);
      
      // Store for future use
      chrome.storage.local.set({ 'sustainabilityData': data });
      
      return data;
    } catch (fetchError) {
      console.error("Error fetching data file:", fetchError);
      
      // Try with alternative path as fallback
      try {
        console.log("Trying alternative path");
        const alternativeUrl = chrome.runtime.getURL('../data/esg_scores.json');
        const altResponse = await fetch(alternativeUrl);
        
        if (!altResponse.ok) {
          throw new Error(`Alternative path failed: ${altResponse.status}`);
        }
        
        const altData = await altResponse.json();
        chrome.storage.local.set({ 'sustainabilityData': altData });
        return altData;
      } catch (altError) {
        console.error("Alternative path also failed:", altError);
        
        // Return hardcoded fallback data for major brands
        console.log("Using hardcoded fallback data");
        const fallbackData = getHardcodedBrands();
        chrome.storage.local.set({ 'sustainabilityData': fallbackData });
        return fallbackData;
      }
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
  // URL to your backend API (can be configured in options)
  let apiUrl = "https://api.ecoshop.example/score"; // Replace with actual API URL
  
  try {
    const response = await fetch(`${apiUrl}?brand=${encodeURIComponent(productInfo.brand)}`);
    
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error("API fetch error:", error);
    throw error;
  }
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
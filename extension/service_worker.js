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
    handleSustainabilityCheck(message.productInfo, sendResponse);
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
    handleSustainabilityCheck(productInfo, sendResponse);
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
async function handleSustainabilityCheck(productInfo, sendResponse) {
  try {
    // Check cache first
    const cacheKey = productInfo.brand?.toLowerCase();
    if (cacheKey && sustainabilityCache[cacheKey]) {
      console.log("Cache hit for brand:", cacheKey);
      const data = sustainabilityCache[cacheKey];
      
      // Set the badge for this tab
      if (sender.tab && sender.tab.id) {
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
      return storedData;
    }
    
    // If not in storage, get from bundled data file
    // Fix the path to the data file - use direct path without ".."
    const response = await fetch(chrome.runtime.getURL('data/esg_scores.json'));
    const data = await response.json();
    
    // Store for future use
    chrome.storage.local.set({ 'sustainabilityData': data });
    
    return data;
  } catch (error) {
    console.error("Error loading sustainability data:", error);
    // Return empty array as fallback
    return [];
  }
}

// Find brand data in the sustainability dataset
function findBrandData(dataset, brandName) {
  if (!dataset || !Array.isArray(dataset) || !brandName) return null;
  
  // Normalize brand name for comparison
  const normalizedBrand = brandName.toLowerCase().trim();
  
  // Try exact match first
  let match = dataset.find(item => 
    item.brand.toLowerCase() === normalizedBrand
  );
  
  // If no exact match, try partial match
  if (!match) {
    match = dataset.find(item => 
      normalizedBrand.includes(item.brand.toLowerCase()) || 
      item.brand.toLowerCase().includes(normalizedBrand)
    );
  }
  
  return match;
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
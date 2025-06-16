// Content script that runs on supported e-commerce pages
(function() {
  // Extract product information based on the current website
  function extractProductInfo() {
    const url = window.location.hostname;
    let productInfo = {
      brand: null,
      name: null,
      url: window.location.href
    };
    
    // Focus only on Shopee as requested
    if (url.includes('shopee.sg') || url.includes('shopee.com')) {
      // Extract from Shopee
      productInfo.brand = document.querySelector('.qPNIqx')?.textContent?.trim();
      productInfo.name = document.querySelector('.YPqix5')?.textContent?.trim();
    }
    
    // Fallback method if specific selectors fail
    if (!productInfo.brand || !productInfo.name) {
      // Try meta tags
      const metaBrand = document.querySelector('meta[property="product:brand"]')?.content ||
                        document.querySelector('meta[property="og:brand"]')?.content;
      const metaName = document.querySelector('meta[property="og:title"]')?.content;
      
      if (metaBrand) productInfo.brand = metaBrand;
      if (metaName) productInfo.name = metaName;
    }
    
    console.log("EcoShop extracted product info:", productInfo);
    return productInfo;
  }
  
  // Send product info to the service worker
  function sendToServiceWorker(productInfo) {
    chrome.runtime.sendMessage({ 
      action: "checkSustainability", 
      productInfo: productInfo 
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error("Error sending message:", chrome.runtime.lastError);
        return;
      }
      
      if (response && response.success) {
        displaySustainabilityBadge(response.data);
      } else {
        console.error("Error getting sustainability data:", response);
      }
    });
  }
  
  // Get user preference for badge position and dark mode
  async function getUserPreferences() {
    return new Promise(resolve => {
      chrome.storage.sync.get(
        { 
          'darkMode': true, // Default to dark mode
          'settings': { badgePosition: 'bottom-right' } // Default position
        }, 
        (result) => resolve({
          darkMode: result.darkMode,
          badgePosition: result.settings?.badgePosition || 'bottom-right'
        })
      );
    });
  }
  
  // Display a sustainability badge on the page
  async function displaySustainabilityBadge(sustainabilityData) {
    // Check if there's already a badge
    let badge = document.getElementById('ecoshop-sustainability-badge');
    if (badge) {
      document.body.removeChild(badge);
    }
    
    // Get user preferences
    const preferences = await getUserPreferences();
    const darkMode = preferences.darkMode;
    
    // Create floating badge
    badge = document.createElement('div');
    badge.id = 'ecoshop-sustainability-badge';
    
    // Apply position based on user preference
    let positionStyles = '';
    switch (preferences.badgePosition) {
      case 'bottom-right':
        positionStyles = 'bottom: 40px; right: 20px;'; // Moved up by 20px to avoid Shopee chat button
        break;
      case 'bottom-left':
        positionStyles = 'bottom: 40px; left: 20px;';
        break;
      case 'top-right':
        positionStyles = 'top: 20px; right: 20px;';
        break;
      case 'top-left':
        positionStyles = 'top: 20px; left: 20px;';
        break;
      default:
        positionStyles = 'bottom: 40px; right: 20px;';
    }
    
    badge.style.cssText = `
      position: fixed;
      ${positionStyles}
      background-color: ${darkMode ? '#222' : 'white'};
      color: ${darkMode ? '#fff' : '#333'};
      border: 2px solid #${getColorForScore(sustainabilityData.score)};
      border-radius: 8px;
      padding: 15px;
      z-index: 10000;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
      font-family: Arial, sans-serif;
      cursor: pointer;
      transition: all 0.3s ease;
    `;
    
    badge.innerHTML = `
      <h3 style="margin: 0 0 10px 0; color: ${darkMode ? '#fff' : '#333'};">Sustainability Score</h3>
      <div style="font-size: 32px; font-weight: bold; color: #${getColorForScore(sustainabilityData.score)};">
        ${sustainabilityData.score}/100
      </div>
      <p style="margin: 10px 0 0 0;">
        Click for details
      </p>
      <div style="margin-top: 8px; font-size: 12px; color: ${darkMode ? '#ccc' : '#666'};">
        Or click the extension icon in the toolbar
      </div>
    `;
    
    document.body.appendChild(badge);
    
    // Add hover effect
    badge.addEventListener('mouseenter', () => {
      badge.style.transform = 'translateY(-5px)';
      badge.style.boxShadow = '0 5px 15px rgba(0,0,0,0.4)';
    });
    
    badge.addEventListener('mouseleave', () => {
      badge.style.transform = 'translateY(0)';
      badge.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
    });
    
    // Make badge open extension popup when clicked
    badge.addEventListener('click', () => {
      // Send message to open popup and highlight the extension icon
      chrome.runtime.sendMessage({ action: "openPopup" }, (response) => {
        if (chrome.runtime.lastError) {
          console.warn("Note: You need to click the extension icon in the toolbar to see details");
        }
      });
      
      // Also show a toast notification explaining how to see details
      showToast("Please click the EcoShop icon in your browser toolbar to see sustainability details");
    });
  }
  
  // Show a toast notification
  function showToast(message, duration = 3500) {
    // Check if a toast already exists
    let toast = document.getElementById('ecoshop-toast');
    if (toast) {
      document.body.removeChild(toast);
    }
    
    // Create the toast
    toast = document.createElement('div');
    toast.id = 'ecoshop-toast';
    toast.style.cssText = `
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background-color: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 12px 24px;
      border-radius: 4px;
      z-index: 10001;
      font-family: Arial, sans-serif;
      font-size: 14px;
      text-align: center;
      opacity: 0;
      transition: opacity 0.3s ease;
    `;
    
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Fade in
    setTimeout(() => {
      toast.style.opacity = '1';
    }, 10);
    
    // Fade out and remove
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => {
        if (toast.parentNode) {
          document.body.removeChild(toast);
        }
      }, 300);
    }, duration);
  }
  
  // Get color based on sustainability score
  function getColorForScore(score) {
    if (score >= 70) return '4CAF50'; // Green
    if (score >= 40) return 'FFC107'; // Yellow/Amber
    return 'F44336'; // Red
  }
  
  // Handle messages from background script or popup
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "getProductInfo") {
      const productInfo = extractProductInfo();
      sendResponse({ productInfo });
    }
    return true;
  });
  
  // Wait for the page to fully load
  window.addEventListener('load', () => {
    // Give the page a moment to fully render dynamic content
    setTimeout(() => {
      const productInfo = extractProductInfo();
      if (productInfo.brand || productInfo.name) {
        sendToServiceWorker(productInfo);
      }
    }, 2000);
  });
})();
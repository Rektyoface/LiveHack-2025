// Content script that runs on supported e-commerce pages
(function() {
  // Flag to prevent repeated error toasts
  let hasShownErrorToast = false;
    // Flag to prevent multiple requests for the same page
  let hasRequestedData = false;
  
  // Reset flag when page URL changes (for single-page apps)
  let currentUrl = window.location.href;
  setInterval(() => {
    if (window.location.href !== currentUrl) {
      currentUrl = window.location.href;
      hasRequestedData = false;
      hasShownErrorToast = false;
      console.log("EcoShop: Page URL changed, resetting flags");
    }
  }, 1000);
  
  // Extract product information based on the current website
  function extractProductInfo() {
    const url = window.location.hostname;
    let productInfo = {
      brand: null,
      name: null,
      url: window.href,
      specifications: {} // New field for detailed specifications
    };
    
    // Focus only on Shopee as requested
    if (url.includes('shopee.sg') || url.includes('shopee.com')) {
      console.log("EcoShop: Detected Shopee website");
      
      // Updated selectors for Shopee (more comprehensive)
      // Try various potential selectors that might contain brand information
      const brandSelectors = [
        '.qPNIqx', // Original selector
        '[data-testid="shopBrandName"]',
        '.shop-name',
        '.seller-name',
        '.brand-name',
        '.qPNIqx span', // Child elements
        '.item-brand',
        '.product-brand'
      ];
      
      // Try various selectors for product name
      const nameSelectors = [
        '.YPqix5', // Original selector
        '.product-name',
        '.product-title',
        '.item-name',
        '.product-detail__name',
        'h1', // Often product names are in h1 tags
        '[data-testid="productTitle"]'
      ];
      
      // Try each potential brand selector
      for (const selector of brandSelectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent?.trim()) {
          productInfo.brand = element.textContent.trim();
          console.log("EcoShop: Found brand using selector", selector, productInfo.brand);
          break;
        }
      }
      
      // Try each potential name selector
      for (const selector of nameSelectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent?.trim()) {
          productInfo.name = element.textContent.trim();
          console.log("EcoShop: Found product name using selector", selector, productInfo.name);
          break;
        }
      }
      
      // NEW: Extract detailed product specifications
      extractProductSpecifications(productInfo);
    }
    
    // Fallback method if specific selectors fail
    if (!productInfo.brand || !productInfo.name) {
      // Try meta tags
      const metaBrand = document.querySelector('meta[property="product:brand"]')?.content ||
                        document.querySelector('meta[property="og:brand"]')?.content;
      const metaName = document.querySelector('meta[property="og:title"]')?.content;
      
      if (metaBrand) {
        productInfo.brand = metaBrand;
        console.log("EcoShop: Found brand using meta tags", productInfo.brand);
      }
      if (metaName) {
        productInfo.name = metaName;
        console.log("EcoShop: Found name using meta tags", productInfo.name);
      }
        // If brand is still not found but we have a name, try to extract brand from title
      if (!productInfo.brand && productInfo.name) {
        // Check for known brands in the product name
        const knownBrands = ["Bose", "Sony", "Apple", "Samsung", "Nike", "Adidas", "Xiaomi", "Huawei", "Dell", "HP", "Asus", "Acer"];
        
        for (const brand of knownBrands) {
          if (productInfo.name.includes(brand)) {
            productInfo.brand = brand;
            console.log("EcoShop: Found known brand in name", productInfo.brand);
            break;
          }
        }
        
        // If still no brand found, try to handle bracket format like "[Brand] Product"
        if (!productInfo.brand) {
          const bracketMatch = productInfo.name.match(/\[(.*?)\]/);
          if (bracketMatch && bracketMatch[1]) {
            const bracketContent = bracketMatch[1].trim();
            // Avoid using phrases like "New", "Sale", etc. as brand names
            if (bracketContent.length < 15 && !["New", "new", "NEW", "Hot", "Sale", "Latest"].includes(bracketContent)) {
              productInfo.brand = bracketContent;
              console.log("EcoShop: Extracted brand from brackets", productInfo.brand);
            }
          }
        }
        
        // If still not found, fall back to first word if capitalized
        if (!productInfo.brand) {
          const words = productInfo.name.split(' ');
          if (words[0] && words[0][0] === words[0][0].toUpperCase() && words[0].length > 2) {
            productInfo.brand = words[0];
            console.log("EcoShop: Extracted brand from name", productInfo.brand);
          }
        }
      }
    }
    
    console.log("EcoShop extracted product info:", productInfo);
    return productInfo;
  }
  
  // NEW FUNCTION: Extract product specifications
  function extractProductSpecifications(productInfo) {
    console.log("EcoShop: Attempting to extract product specifications");
    
    // Look for the product specifications section
    const specSectionSelectors = [
      'div.product-detail',
      '.product-specs',
      '.product-specifications',
      '.product-info',
      // The section often has 'specifications' in the heading
      'div:has(> div:contains("Product Specifications"))',
      'div:has(> div:contains("Specifications"))',
      'section:has(> h2:contains("Specifications"))'
    ];
    
    let specSection = null;
    for (const selector of specSectionSelectors) {
      try {
        const element = document.querySelector(selector);
        if (element) {
          console.log("EcoShop: Found spec section using selector", selector);
          specSection = element;
          break;
        }
      } catch (e) {
        console.log("EcoShop: Error with selector", selector, e);
      }
    }
    
    if (!specSection) {
      // Try finding spec tables directly
      const specTableSelectors = [
        'table.product-info-table', 
        '.specification-table',
        'table.specs',
        // Shopee often has spec rows as div pairs
        '.product-detail div.flex'
      ];
      
      for (const selector of specTableSelectors) {
        try {
          const elements = document.querySelectorAll(selector);
          if (elements && elements.length > 0) {
            console.log("EcoShop: Found spec elements using selector", selector);
            processSpecElements(elements, productInfo);
            break;
          }
        } catch (e) {
          console.log("EcoShop: Error with table selector", selector, e);
        }
      }
    } else {
      // Process the found spec section
      const rows = specSection.querySelectorAll('tr, .flex, .row, div.flex');
      processSpecElements(rows, productInfo);
    }
    
    // If we still don't have brand in our specs but have it in the main product info, add it
    if (productInfo.brand && !productInfo.specifications.brand) {
      productInfo.specifications.brand = productInfo.brand;
    }
    
    // Also try looking for key-value pairs directly in the DOM
    const allElements = document.querySelectorAll('div, section, article');
    for (const element of allElements) {
      const text = element.textContent?.trim();
      // Check if this might be a spec label
      if (text && (text.includes(':') || text.includes('Brand') || text.includes('Category'))) {
        const children = element.children;
        if (children && children.length === 2) {
          const label = children[0].textContent?.trim();
          const value = children[1].textContent?.trim();
          
          if (label && value) {
            const key = label.toLowerCase().replace(':', '').trim();
            if (key && !['', 'undefined'].includes(key)) {
              productInfo.specifications[key] = value;
              console.log("EcoShop: Found key-value spec", key, value);
            }
          }
        }
      }
    }
  }
  
  // Helper to process specification elements
  function processSpecElements(elements, productInfo) {
    if (!elements || elements.length === 0) return;
    
    for (const element of elements) {
      // Handle table rows
      const cells = element.querySelectorAll('td, th, div');
      if (cells && cells.length >= 2) {
        const key = cells[0].textContent?.trim().toLowerCase();
        const value = cells[1].textContent?.trim();
        
        if (key && value && !['', 'undefined'].includes(key)) {
          const cleanKey = key.replace(':', '').trim();
          productInfo.specifications[cleanKey] = value;
          console.log("EcoShop: Found specification", cleanKey, value);
          
          // If this is the brand and we didn't already find it, use it
          if ((cleanKey === 'brand' || cleanKey === 'make') && !productInfo.brand) {
            productInfo.brand = value;
          }
        }
      }
      
      // Handle div pairs (Shopee often uses this pattern)
      const text = element.textContent?.trim();
      if (text && text.includes(':')) {
        const [key, value] = text.split(':').map(part => part.trim());
        if (key && value) {
          productInfo.specifications[key.toLowerCase()] = value;
          console.log("EcoShop: Found div spec", key, value);
        }
      }
    }
  }  // Send product info to the service worker
  function sendToServiceWorker(productInfo) {
    // Prevent multiple requests for the same page
    if (hasRequestedData) {
      console.log("EcoShop: Already requested data for this page, skipping");
      return;
    }
    
    hasRequestedData = true;
    console.log("EcoShop: Sending to service worker", productInfo);
    chrome.runtime.sendMessage({ 
      action: "checkSustainability", 
      productInfo: productInfo 
    }, (response) => {
      if (chrome.runtime.lastError) {
        console.error("Error sending message:", chrome.runtime.lastError);
        showToast("EcoShop: Extension error - please try refreshing the page", 5000);
        return;
      }
      
      if (response && response.success) {
        displaySustainabilityBadge(response.data);      } else if (response && response.error) {
        console.error("Error getting sustainability data:", response.error);
        if (response.error.includes("Database connection") && !hasShownErrorToast) {
          hasShownErrorToast = true;
          showToast("EcoShop: Database connection required. Please check your internet connection.", 5000);
        } else if (!hasShownErrorToast && !response.error.includes("Database connection")) {
          hasShownErrorToast = true;
          showToast(`EcoShop: ${response.message || response.error}`, 4000);
        }
      } else {
        console.error("Unknown error getting sustainability data:", response);
        if (!hasShownErrorToast) {
          hasShownErrorToast = true;
          showToast("EcoShop: Unable to load sustainability data", 4000);
        }
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
    badge.id = 'ecoshop-sustainability-badge';    // Apply position based on user preference
    let positionStyles = '';
    switch (preferences.badgePosition) {
      case 'bottom-right':
        positionStyles = 'bottom: 50px; right: 5px;'; // Moved up by 50px to avoid Shopee chat button
        break;
      case 'bottom-left':
        positionStyles = 'bottom: 50px; left: 5px;'; // Also moved up for consistency
        break;
      case 'top-right':
        positionStyles = 'top: 20px; right: 5px;';
        break;
      case 'top-left':
        positionStyles = 'top: 20px; left: 5px;';
        break;
      default:
        positionStyles = 'bottom: 50px; right: 5px;';
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
      transition: opacity 0.4s cubic-bezier(0.4,0,0.2,1), transform 0.4s cubic-bezier(0.4,0,0.2,1);
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
    console.log("EcoShop: Badge displayed");

    // Disconnect the observer so the badge doesn't reappear after removal
    if (window.ecoshopObserver && typeof window.ecoshopObserver.disconnect === 'function') {
      window.ecoshopObserver.disconnect();
    }

    // Add hover effect
    badge.addEventListener('mouseenter', () => {
      badge.style.transform = 'translateY(-5px) scale(1.04)';
      badge.style.boxShadow = '0 5px 15px rgba(0,0,0,0.4)';
    });
    badge.addEventListener('mouseleave', () => {
      badge.style.transform = 'translateY(0) scale(1)';
      badge.style.boxShadow = '0 2px 10px rgba(0,0,0,0.3)';
    });

    // Only allow one click to remove the badge
    let badgeClicked = false;
    function badgeClickHandler(e) {
      if (badgeClicked) return;
      badgeClicked = true;
      badge.style.pointerEvents = 'none';
      e.preventDefault();
      e.stopPropagation();
      badge.style.opacity = '0';
      badge.style.transform = 'scale(0.8)';
      setTimeout(() => {
        if (badge.parentNode) badge.parentNode.removeChild(badge);
        showToast('For more details, please click the EcoShop extension icon in your browser toolbar.');
      }, 420);
    }
    badge.addEventListener('click', badgeClickHandler);
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
    // First attempt to extract product info
    setTimeout(() => {
      const productInfo = extractProductInfo();
      if (productInfo.brand || productInfo.name) {
        sendToServiceWorker(productInfo);
      } else {
        console.log("EcoShop: Initial extraction failed, trying again in 2 seconds");
        // Try again after a longer delay for dynamic content
        setTimeout(() => {
          const productInfo = extractProductInfo();
          if (productInfo.brand || productInfo.name) {
            sendToServiceWorker(productInfo);
          } else {
            console.log("EcoShop: Could not extract product information");
          }
        }, 2000);
      }
    }, 1000);
  });
    // Also try extraction when DOM content changes (but only once)
  // This helps with single-page apps or sites that load content dynamically
  window.ecoshopObserver = new MutationObserver((mutations) => {
    // Only check if we haven't already displayed a badge AND haven't already requested data
    if (!document.getElementById('ecoshop-sustainability-badge') && !hasRequestedData) {
      const productInfo = extractProductInfo();
      if (productInfo.brand || productInfo.name) {
        sendToServiceWorker(productInfo);
      }
    }
  });

  // Start observing once the initial page is loaded
  setTimeout(() => {
    window.ecoshopObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: false,
      characterData: false
    });
  }, 3000);
})();
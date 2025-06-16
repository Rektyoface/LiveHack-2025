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
    
    if (url.includes('shopee.sg')) {
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
      if (response && response.success) {
        displaySustainabilityBadge(response.data);
      } else {
        console.error("Error getting sustainability data:", response);
      }
    });
  }
  
  // Display a sustainability badge on the page
  function displaySustainabilityBadge(sustainabilityData) {
    // Create floating badge
    const badge = document.createElement('div');
    badge.id = 'ecoshop-sustainability-badge';
    badge.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background-color: white;
      border: 2px solid #${getColorForScore(sustainabilityData.score)};
      border-radius: 8px;
      padding: 15px;
      z-index: 10000;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
      font-family: Arial, sans-serif;
    `;
    
    badge.innerHTML = `
      <h3 style="margin: 0 0 10px 0; color: #333;">Sustainability Score</h3>
      <div style="font-size: 32px; font-weight: bold; color: #${getColorForScore(sustainabilityData.score)};">
        ${sustainabilityData.score}/100
      </div>
      <p style="margin: 10px 0 0 0;">
        Click extension icon for details
      </p>
    `;
    
    document.body.appendChild(badge);
    
    // Make badge dismissable
    badge.addEventListener('click', () => {
      badge.style.display = 'none';
    });
  }
  
  // Get color based on sustainability score
  function getColorForScore(score) {
    if (score >= 70) return '4CAF50'; // Green
    if (score >= 40) return 'FFC107'; // Yellow/Amber
    return 'F44336'; // Red
  }
  
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
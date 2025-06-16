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
    
    // Add more website detection logic
    if (url.includes('shopee.sg') || url.includes('shopee.com')) {
      // Extract from Shopee
      productInfo.brand = document.querySelector('.qPNIqx')?.textContent?.trim();
      productInfo.name = document.querySelector('.YPqix5')?.textContent?.trim();
    } else if (url.includes('amazon')) {
      productInfo.brand = document.querySelector('#bylineInfo')?.textContent?.trim();
      productInfo.name = document.querySelector('#productTitle')?.textContent?.trim();
    } else if (url.includes('lazada')) {
      productInfo.brand = document.querySelector('.pdp-product-brand')?.textContent?.trim();
      productInfo.name = document.querySelector('.pdp-mod-product-name')?.textContent?.trim();
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
  
  // Get user preference for dark/light mode
  async function getUserTheme() {
    return new Promise(resolve => {
      chrome.storage.sync.get({ 'darkMode': true }, // Default to dark mode
        (result) => resolve(result.darkMode)
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
    
    // Get user theme preference
    const darkMode = await getUserTheme();
    
    // Create floating badge
    badge = document.createElement('div');
    badge.id = 'ecoshop-sustainability-badge';
    badge.style.cssText = `
      position: fixed;
      bottom: 40px; /* Moved up by 20px to avoid Shopee chat button */
      right: 20px;
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
        Click to see details
      </p>
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
      chrome.runtime.sendMessage({ action: "openPopup" });
    });
    
    // Add theme toggle button
    const themeToggle = document.createElement('div');
    themeToggle.style.cssText = `
      position: absolute;
      top: 10px;
      right: 10px;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background-color: ${darkMode ? '#fff' : '#222'};
      cursor: pointer;
      border: 1px solid #ccc;
    `;
    
    themeToggle.addEventListener('click', async (e) => {
      e.stopPropagation(); // Prevent triggering badge click
      const currentTheme = await getUserTheme();
      const newTheme = !currentTheme;
      chrome.storage.sync.set({ 'darkMode': newTheme });
      badge.style.backgroundColor = newTheme ? '#222' : 'white';
      badge.style.color = newTheme ? '#fff' : '#333';
      const headerText = badge.querySelector('h3');
      if (headerText) headerText.style.color = newTheme ? '#fff' : '#333';
      themeToggle.style.backgroundColor = newTheme ? '#fff' : '#222';
    });
    
    badge.appendChild(themeToggle);
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
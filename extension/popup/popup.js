// EcoShop Popup Script
document.addEventListener('DOMContentLoaded', function() {
  // Elements
  chrome.storage.sync.get(['settings'], (data) => {
    const seniorEnabled = data.settings?.seniorMode === true;
    document.documentElement.setAttribute('data-senior', seniorEnabled ? 'true' : 'false');
    console.log('✅ Applied senior mode:', seniorEnabled);
    console.log('🔎 Final attribute:', document.documentElement.getAttribute('data-senior'));
  });
  const loadingElement = document.getElementById('loading');
  const loadingMessageElement = document.getElementById('loading-message');
  const noProductElement = document.getElementById('no-product');
  const productInfoElement = document.getElementById('product-info');
  const brandNameElement = document.getElementById('brand-name');
  const scoreValueElement = document.getElementById('score-value');
  const sustainabilityMetricsContainer = document.getElementById('sustainability-metrics-container'); // New container
  const dataCertaintyElement = document.getElementById('data-certainty');
  const sustainabilityMessageElement = document.getElementById('sustainability-message');
  const alternativesListElement = document.getElementById('alternatives-list');
  const optionsButton = document.getElementById('options-button');
  const learnMoreButton = document.getElementById('learn-more');
  const websiteBadge = document.getElementById('website-badge');

  // Initialize dark mode from storage
  initTheme();
  
  // Initialize theme from saved preference
  async function initTheme() {
    try {
      const result = await chrome.storage.sync.get({ 'darkMode': true });
      setTheme(result.darkMode);
    } catch (error) {
      console.error("Error loading theme preference:", error);
      setTheme(true); // Default to dark mode
    }
  }

  function setTheme(isDarkMode) {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
  }  // Show loading state initially - always fetch fresh data
  showLoadingState();
  
  // Start progressive loading messages after a short delay
  setTimeout(() => {
    showProgressiveLoading();
  }, 1000);
  
  chrome.tabs.query({active: true, currentWindow: true}, async function(tabs) {
    if (tabs.length === 0) {
      showNoProductMessage();
      return;
    }
    const currentTab = tabs[0];
    const url = new URL(currentTab.url);
    websiteBadge.textContent = url.hostname;
    const isShopee = currentTab.url.includes('shopee.sg') || currentTab.url.includes('shopee.com');
    
    if (!isShopee) {
      showNoProductMessage("Visit Shopee to see sustainability ratings");
      return;
    }
    
    // ALWAYS fetch fresh data from database - no caching
    console.log("popup.js: Always fetching fresh data from database for URL:", currentTab.url);
    
    chrome.tabs.sendMessage(currentTab.id, { action: "getProductInfo" }, function(response) {
      if (chrome.runtime.lastError || !response) {
        chrome.runtime.sendMessage({ 
          action: "checkCurrentPage", 
          url: currentTab.url,
          title: currentTab.title
        }, (backendResponse) => {
          handleSustainabilityData(backendResponse);
        });
        return;
      }
      if (response.productInfo) {
        chrome.runtime.sendMessage({
          action: "checkSustainability",
          productInfo: response.productInfo
        }, (backendResponse) => {
          handleSustainabilityData(backendResponse);
        });
      } else {
        showNoProductMessage("Couldn't identify product information");
      }
    });
  });

  // Listen for refresh message to re-apply weights and update scoring
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'refreshEcoShopPopup') {
      // Always reload the popup to fetch latest settings and recalculate
      window.location.reload();
    }
  });  // Handle fresh sustainability data from database - ALWAYS fresh, never cached
  function handleSustainabilityData(response) {
    console.log("=== POPUP.JS: FRESH DATA FROM DATABASE ===");
    console.log("Full response object:", JSON.stringify(response, null, 2));
    
    // Clear the progressive loading interval
    if (window.ecoshopLoadingInterval) {
      clearInterval(window.ecoshopLoadingInterval);
      window.ecoshopLoadingInterval = null;
    }
    
    // Hide loading state
    loadingElement.classList.add('hidden');
    
    if (!response || !response.success) {
      console.error("popup.js: Database response unsuccessful or missing.", response);
      if (response && response.error) {
        if (response.error.includes("Database connection") || response.error.includes("Backend service unavailable")) {
          showNoProductMessage("Database connection required. Please check your internet connection and ensure the backend service is running.");
        } else {
          showNoProductMessage(response.message || response.error);
        }
      } else {
        showNoProductMessage("No fresh sustainability data available from database");
      }
      return;
    }

    const data = response.data;
    console.log("popup.js: Fresh data object from database:", data);
    console.log("popup.js: Fresh backend score value:", data.score);
    console.log("popup.js: Fresh backend score type:", typeof data.score);

    // Show product info section
    productInfoElement.classList.remove('hidden');
    
    // CRITICAL: Use the fresh backend score directly from database
    const backendScore = data.score;
    let displayScore;
      // Only show score if we have a valid number from fresh database data
    if (typeof backendScore === 'number' && !isNaN(backendScore)) {
      displayScore = Math.round(backendScore);
      console.log("popup.js: Using fresh database score:", displayScore);
    } else {
      console.warn("popup.js: Fresh database score not valid:", backendScore);
      // Don't show a default - show that we need fresh data from database
      showNoProductMessage("Fresh score not available from database. Please try again.");
      return;
    }

    // Update the main score display with fresh database score only
    const scoreColor = getScoreColor(displayScore);
    scoreValueElement.style.color = '#FFF';
    scoreValueElement.parentElement.style.backgroundColor = scoreColor;
    brandNameElement.textContent = data.brand_name || data.brand || "Unknown Brand";
    scoreValueElement.textContent = displayScore;

    console.log("popup.js: Updated main score display with fresh database score:", displayScore);

    // Update the browser action badge to match the popup score
    chrome.runtime.sendMessage({ action: "setBadgeScore", score: displayScore });

    // Render the breakdown details (but DON'T let this override the main score)
    sustainabilityMetricsContainer.innerHTML = '';
    const breakdown = data.sustainability_breakdown || data.breakdown;
    let detailsData = [];
    const fieldOrder = [
      { key: 'production_and_brand', label: 'Production And Brand' },
      { key: 'circularity_and_end_of_life', label: 'Circularity And End Of Life' },
      { key: 'material_composition', label: 'Material Composition' }
    ];
    
    if (breakdown) {
      fieldOrder.forEach(field => {
        const metricData = breakdown[field.key] || {};
        const value = metricData.value || metricData.rating;
        const score = typeof metricData.score === 'number' ? metricData.score : undefined;

        // Field ratings display the raw score out of 10, not weighted
        const displayFieldScore = (score !== undefined && score >= 0) ? Math.max(0, Math.min(10, score)) : undefined;
        const ratingText = (displayFieldScore !== undefined) ? `(Rating: ${displayFieldScore}/10)` : '(Rating: --/10)';

        let valueText;
        if (value && value !== "Unknown") {
          valueText = value;
        } else if (displayFieldScore !== undefined) {
          valueText = "Unknown";
        } else {
          valueText = "We could not find data";
        }
        
        detailsData.push({
          title: field.label,
          value: valueText,
          score: displayFieldScore,
          analysis: metricData.analysis || "We could not find data"
        });
        
        const metricElement = document.createElement('div');
        metricElement.className = 'metric';
        metricElement.innerHTML = `
          <h3>${field.label}</h3>
          <div class="metric-value">${valueText} ${ratingText}</div>
          <div class="meter">
            <div class="meter-bar" style="width: ${displayFieldScore ? displayFieldScore * 10 : 0}%; background-color: ${getScoreColor(displayFieldScore ? displayFieldScore * 10 : 0)};"></div>
          </div>
        `;
        sustainabilityMetricsContainer.appendChild(metricElement);
      });
    } else {
      // Always show the 3 default fields with placeholder values
      fieldOrder.forEach(field => {
        detailsData.push({
          title: field.label,
          value: "We could not find data",
          score: undefined,
          analysis: "We could not find data"
        });
        const metricElement = document.createElement('div');
        metricElement.className = 'metric';
        metricElement.innerHTML = `
          <h3>${field.label}</h3>
          <div class="metric-value">We could not find data (Rating: --/10)</div>
          <div class="meter">
            <div class="meter-bar" style="width: 0%; background-color: #ccc;"></div>
          </div>
        `;
        sustainabilityMetricsContainer.appendChild(metricElement);
      });
    }
    
    // Show Details button logic
    const showDetailsButton = document.getElementById('show-details');
    showDetailsButton.disabled = false;
    showDetailsButton.onclick = function() {
      chrome.storage.local.set({ sustainabilityDetails: { allFields: detailsData } }, function() {
        window.location.href = 'details.html';
      });
    }

    // Show Recommendations button logic
    const showRecommendationsButton = document.getElementById('show-recommendations');
    const recommendations = data.recommendations || [];
    
    console.log('Recommendations from backend:', recommendations);
    
    if (recommendations.length > 0) {
      showRecommendationsButton.disabled = false;
      showRecommendationsButton.textContent = `View Recommendations (${recommendations.length})`;
      showRecommendationsButton.onclick = function() {
        console.log('Storing recommendations:', recommendations);
        chrome.storage.local.set({ 
          sustainabilityRecommendations: recommendations,
          currentProductCategory: data.category || 'Unknown'
        }, function() {
          window.location.href = 'recommendations.html';
        });
      }
    } else {
      showRecommendationsButton.disabled = true;
      showRecommendationsButton.textContent = 'No Recommendations Available';
      showRecommendationsButton.style.opacity = '0.6';
    }

    if (data.certainty) {
      dataCertaintyElement.textContent = capitalizeFirstLetter(data.certainty);
    }
    
    if (data.message) {
      sustainabilityMessageElement.textContent = data.message;
    } else {
      sustainabilityMessageElement.textContent = getDefaultMessage(displayScore);
    }

    if (data.alternatives && data.alternatives.length > 0) {
      alternativesListElement.innerHTML = '';
      data.alternatives.forEach(alt => {
        const altElement = document.createElement('div');
        altElement.className = 'alternative-item';
        altElement.innerHTML = `
          <div class="alternative-name">${alt.brand}</div>
          <div class="alternative-score" style="background-color: ${getScoreColor(alt.score)}">${alt.score}</div>
        `;
        altElement.addEventListener('click', () => {
          window.open(`https://www.google.com/search?q=${encodeURIComponent(alt.brand)}+sustainable+products`, '_blank');
        });
        alternativesListElement.appendChild(altElement);
      });
    } else {
      document.querySelector('.alternatives-container').classList.add('hidden');
    }
  }

  function showNoProductMessage(message = "Please visit a product page to see sustainability information") {
    loadingElement.classList.add('hidden');
    productInfoElement.classList.add('hidden');
    noProductElement.classList.remove('hidden');
    noProductElement.querySelector('p').textContent = message;
  }

  function getScoreColor(score) {
    if (score === null || score === undefined || isNaN(score)) return '#ccc'; // Default for N/A
    if (score >= 70) return '#4caf50'; // Green
    if (score >= 40) return '#ff9800'; // Orange
    return '#f44336'; // Red
  }

  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  function getDefaultMessage(score) {
    if (score === undefined || score === null) return "We could not find any sustainability information for this product.";
    if (score >= 70) return "This product has good sustainability practices.";
    if (score >= 40) return "This product has average sustainability practices.";
    return "This product has poor sustainability practices.";
  }
  optionsButton.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  // Learn More button - remove the incorrect details navigation  // The "Show Details" button handles navigation to details page
  function showLoadingState() {
    loadingElement.classList.remove('hidden');
    noProductElement.classList.add('hidden');
    productInfoElement.classList.add('hidden');
    
    // Set loading indicators
    if (scoreValueElement) {
      scoreValueElement.textContent = '...';
      scoreValueElement.style.color = '#999';
    }
    if (brandNameElement) {
      brandNameElement.textContent = 'Loading...';
    }
    
    // Start progressive loading messages
    updateLoadingMessage("Fetching fresh data from database...");
    
    console.log("popup.js: Showing loading state - fetching fresh data from database");
  }
  
  function updateLoadingMessage(message) {
    if (loadingMessageElement) {
      loadingMessageElement.textContent = message;
    }
  }
    function showProgressiveLoading() {
    let step = 0;
    const messages = [
      "Fetching fresh data from database...",
      "Analyzing sustainability metrics...",
      "Calculating scores and recommendations...",
      "Preparing detailed breakdown..."
    ];
    
    const interval = setInterval(() => {
      if (step < messages.length) {
        updateLoadingMessage(messages[step]);
        step++;
        
        // If we're past the first step and still loading, it's likely a cache miss with LLM analysis
        if (step >= 2) {
          updateLoadingMessage("Analyzing product sustainability...");
          clearInterval(interval);
        }
      }
    }, 3000); // Change message every 3 seconds for cache hit, then switch to analyzing for cache miss
    
    // Store interval ID to clear it when data arrives
    window.ecoshopLoadingInterval = interval;
  }
});
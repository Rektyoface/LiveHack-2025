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
  }

  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
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
    chrome.tabs.sendMessage(currentTab.id, { action: "getProductInfo" }, function(response) {
      if (chrome.runtime.lastError || !response) {
        chrome.runtime.sendMessage({ 
          action: "checkCurrentPage", 
          url: currentTab.url,
          title: currentTab.title
        }, handleSustainabilityData);
        return;
      }
      if (response.productInfo) {
        chrome.runtime.sendMessage({
          action: "checkSustainability",
          productInfo: response.productInfo
        }, handleSustainabilityData);
      } else {
        showNoProductMessage("Couldn't identify product information");
      }
    });
  });

  function handleSustainabilityData(response) {
    console.log("popup.js: Received response in handleSustainabilityData:", response); // Existing log

    loadingElement.classList.add('hidden');
    if (!response || !response.success) {
      console.error("popup.js: Response unsuccessful or missing.", response); // Added for debugging
      if (response && response.error) {
        if (response.error.includes("Database connection")) {
          showNoProductMessage("Database connection required. Please check your internet connection and ensure the backend service is running.");
        } else {
          showNoProductMessage(response.message || response.error);
        }
      } else {
        showNoProductMessage("No sustainability data available");
      }
      return;
    }

    const data = response.data;
    console.log("popup.js: Data object:", data); // Added for debugging

    productInfoElement.classList.remove('hidden');
    // Only use score from backend, never use default_sustainability_score
    let mainScore = typeof data.score === 'number' ? data.score : undefined;
    let displayScore = mainScore; // Use backend score directly
    const scoreColor = getScoreColor(displayScore);
    scoreValueElement.style.color = '#FFF';
    scoreValueElement.parentElement.style.backgroundColor = scoreColor;
    brandNameElement.textContent = data.brand_name || data.brand || "Unknown Brand";
    scoreValueElement.textContent = displayScore !== undefined ? displayScore : "Unknown";

    sustainabilityMetricsContainer.innerHTML = '';

    // Use 'sustainability_breakdown' if present, else fallback to 'breakdown' (from backend)
    const breakdown = data.sustainability_breakdown || data.breakdown;
    let detailsData = [];

    if (breakdown) {
      console.log("popup.js: sustainability_breakdown object:", breakdown); // Debug
      const fieldOrder = [
        { key: 'production_and_brand', label: 'Production And Brand' },
        { key: 'circularity_and_end_of_life', label: 'Circularity And End Of Life' },
        { key: 'material_composition', label: 'Material Composition' }
      ];
      fieldOrder.forEach(field => {
        const metricData = breakdown[field.key] || {};
        let value = metricData.value || metricData.rating || "Unknown";
        let score = typeof metricData.score === 'number' ? metricData.score : undefined;
        // No rebasing: display score directly
        let displayFieldScore = score;
        // Clamp displayFieldScore to 0-10 for user readability
        if (typeof displayFieldScore === 'number') {
          displayFieldScore = Math.max(0, Math.min(10, displayFieldScore));
        }
        // Show 'We could not find data' only if value is 'Unknown' or missing AND score is missing/undefined/-1/0
        if ((value === "Unknown" || !value) && (score === undefined || score === -1 || score === 0)) {
          value = "We could not find data";
        }
        // Show 'Unknown' if score is -1
        let ratingText = (score === -1) ? '(Rating: Unknown --/10)' : (typeof displayFieldScore === 'number' ? `(Rating: ${displayFieldScore}/10)` : (score === 0 ? '(Rating: 0/10)' : '(Rating: --/10)'));
        detailsData.push({
          title: field.label,
          value,
          score: displayFieldScore,
          analysis
        });
        // Render summary in popup
        const metricElement = document.createElement('div');
        metricElement.className = 'metric';
        metricElement.innerHTML = `
          <h3>${field.label}</h3>
          <div class="metric-value">${value} ${ratingText}</div>
          <div class="meter">
            <div class="meter-bar" style="width: ${displayFieldScore && displayFieldScore > 0 ? displayFieldScore * 10 : 0}%; background-color: ${getScoreColor(displayFieldScore && displayFieldScore > 0 ? displayFieldScore * 10 : 0)};"></div>
          </div>
        `;
        sustainabilityMetricsContainer.appendChild(metricElement);
      });
    } else {
      // Always show the 3 default fields with placeholder values
      const defaultFields = [
        { key: 'production_and_brand', label: 'Production And Brand' },
        { key: 'circularity_and_end_of_life', label: 'Circularity And End Of Life' },
        { key: 'material_composition', label: 'Material Composition' }
      ];
      defaultFields.forEach(field => {
        detailsData.push({
          title: field.label,
          value: "we could not find data",
          score: 0.0,
          analysis: "we could not find data"
        });
        const metricElement = document.createElement('div');
        metricElement.className = 'metric';
        metricElement.innerHTML = `
          <h3>${field.label}</h3>
          <div class="metric-value">we could not find data (Rating: --/10)</div>
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

    if (data.certainty) { // Assuming certainty is still part of the response
      dataCertaintyElement.textContent = capitalizeFirstLetter(data.certainty);
    }
    if (data.message) { // Assuming message is still part of the response
      sustainabilityMessageElement.textContent = data.message;
    } else {
      sustainabilityMessageElement.textContent = getDefaultMessage(mainScore);
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
    if (score >= 70) return '#4CAF50'; // Green
    if (score >= 40) return '#FFC107'; // Yellow/Amber
    return '#F44336'; // Red
  }

  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }

  function getDefaultMessage(score) {
    if (score === null || score === undefined || isNaN(score)) return "Sustainability information is not available.";
    if (score >= 70) return "This product demonstrates strong sustainability practices.";
    if (score >= 40) return "This product has average sustainability practices.";
    return "This product has areas for improvement in sustainability.";
  }

  optionsButton.addEventListener('click', function() {
    chrome.runtime.openOptionsPage();
  });

  learnMoreButton.addEventListener('click', function() {
    // Replace with your actual learn more link
    window.open('https://example.com/learn-more-sustainability', '_blank');
  });
});
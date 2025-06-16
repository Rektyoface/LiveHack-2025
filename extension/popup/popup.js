// EcoShop Popup Script
document.addEventListener('DOMContentLoaded', function() {
  // Elements
  const loadingElement = document.getElementById('loading');
  const noProductElement = document.getElementById('no-product');
  const productInfoElement = document.getElementById('product-info');
  const brandNameElement = document.getElementById('brand-name');
  const scoreValueElement = document.getElementById('score-value');
  const carbonValueElement = document.getElementById('carbon-value');
  const carbonMetricElement = document.getElementById('carbon-metric');
  const carbonMeterElement = document.getElementById('carbon-meter');
  const waterMetricElement = document.getElementById('water-metric');
  const waterMeterElement = document.getElementById('water-meter');
  const wasteMetricElement = document.getElementById('waste-metric');
  const wasteMeterElement = document.getElementById('waste-meter');
  const laborMetricElement = document.getElementById('labor-metric');
  const laborMeterElement = document.getElementById('labor-meter');
  const dataCertaintyElement = document.getElementById('data-certainty');
  const sustainabilityMessageElement = document.getElementById('sustainability-message');
  const alternativesListElement = document.getElementById('alternatives-list');
  const optionsButton = document.getElementById('options-button');
  const learnMoreButton = document.getElementById('learn-more');

  // Get current tab information
  chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    if (tabs.length === 0) {
      showNoProductMessage();
      return;
    }

    // Get the current tab
    const currentTab = tabs[0];
    
    // Check if the URL is a supported e-commerce site
    const supportedSites = [
      'amazon.com',
      'shopee.com',
      'etsy.com'
    ];
    
    const isProductPage = supportedSites.some(site => currentTab.url.includes(site));
    
    if (!isProductPage) {
      showNoProductMessage("Visit a supported shopping site to see sustainability ratings");
      return;
    }
    
    // Request sustainability data for the current product
    chrome.tabs.sendMessage(currentTab.id, { action: "getProductInfo" }, function(response) {
      // If we couldn't communicate with content script, try a different approach
      if (chrome.runtime.lastError || !response) {
        // Direct request to service worker
        chrome.runtime.sendMessage({ 
          action: "checkCurrentPage", 
          url: currentTab.url,
          title: currentTab.title
        }, handleSustainabilityData);
        return;
      }
      
      // If we received product info from content script
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

  // Process and display sustainability data
  function handleSustainabilityData(response) {
    loadingElement.classList.add('hidden');
    
    if (!response || !response.success || !response.data) {
      showNoProductMessage("No sustainability data available");
      return;
    }
    
    const data = response.data;
    productInfoElement.classList.remove('hidden');
    
    // Apply score color
    const scoreColor = getScoreColor(data.score);
    scoreValueElement.style.color = '#FFF';
    scoreValueElement.parentElement.style.backgroundColor = scoreColor;
    
    // Populate data
    brandNameElement.textContent = data.brand || "Unknown Brand";
    scoreValueElement.textContent = data.score || "N/A";
    
    // Carbon footprint
    if (data.co2e) {
      carbonValueElement.textContent = data.co2e;
      const carbonPercent = Math.min(data.co2e / 10 * 100, 100);
      carbonMeterElement.style.width = `${100 - carbonPercent}%`;
      carbonMeterElement.style.backgroundColor = getInverseColor(carbonPercent);
    }
    
    // Water usage
    if (data.waterUsage) {
      waterMetricElement.textContent = capitalizeFirstLetter(data.waterUsage);
      waterMeterElement.style.width = getPercentForRating(data.waterUsage);
      waterMeterElement.style.backgroundColor = getColorForRating(data.waterUsage);
    }
    
    // Waste generated
    if (data.wasteGenerated) {
      wasteMetricElement.textContent = capitalizeFirstLetter(data.wasteGenerated);
      wasteMeterElement.style.width = getPercentForRating(data.wasteGenerated);
      wasteMeterElement.style.backgroundColor = getColorForRating(data.wasteGenerated);
    }
    
    // Labor practices
    if (data.laborPractices) {
      laborMetricElement.textContent = capitalizeFirstLetter(data.laborPractices);
      laborMeterElement.style.width = getPercentForRating(data.laborPractices, true);
      laborMeterElement.style.backgroundColor = getColorForRating(data.laborPractices, true);
    }
    
    // Data certainty
    if (data.certainty) {
      dataCertaintyElement.textContent = capitalizeFirstLetter(data.certainty);
    }
    
    // Sustainability message
    if (data.message) {
      sustainabilityMessageElement.textContent = data.message;
    } else {
      sustainabilityMessageElement.textContent = getDefaultMessage(data.score);
    }
    
    // Alternatives
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
          // Could open a link to this alternative product
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
    if (score >= 70) return '#4CAF50'; // Green
    if (score >= 40) return '#FFC107'; // Yellow/Amber
    return '#F44336'; // Red
  }
  
  function getInverseColor(percent) {
    if (percent <= 30) return '#4CAF50'; // Green
    if (percent <= 70) return '#FFC107'; // Yellow/Amber
    return '#F44336'; // Red
  }
  
  function getPercentForRating(rating, inverse = false) {
    const map = {
      'low': inverse ? '30%' : '75%',
      'medium': '50%',
      'high': inverse ? '75%' : '30%',
      'very low': inverse ? '20%' : '90%',
      'very high': inverse ? '90%' : '20%',
      'unknown': '50%',
      'good': '75%',
      'fair': '50%',
      'poor': '30%'
    };
    return map[rating.toLowerCase()] || '50%';
  }
  
  function getColorForRating(rating, inverse = false) {
    const lowValue = inverse ? 'poor' : 'low';
    const highValue = inverse ? 'good' : 'high';
    
    if (rating.toLowerCase().includes(lowValue) || 
        (inverse && rating.toLowerCase() === 'poor')) {
      return '#F44336'; // Red
    }
    if (rating.toLowerCase().includes(highValue) || 
        (inverse && rating.toLowerCase() === 'good')) {
      return '#4CAF50'; // Green
    }
    if (rating.toLowerCase() === 'medium' || 
        rating.toLowerCase() === 'fair' ||
        rating.toLowerCase() === 'unknown') {
      return '#FFC107'; // Yellow
    }
    return '#FFC107'; // Default to yellow
  }
  
  function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
  }
  
  function getDefaultMessage(score) {
    if (score >= 80) {
      return "This brand demonstrates exceptional commitment to sustainability practices.";
    } else if (score >= 60) {
      return "This brand shows good sustainability practices but has room for improvement.";
    } else if (score >= 40) {
      return "This brand has average sustainability practices with significant opportunities for improvement.";
    } else {
      return "This brand has concerning sustainability practices and should be considered carefully.";
    }
  }

  // Button event listeners
  optionsButton.addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });
  
  learnMoreButton.addEventListener('click', () => {
    window.open('https://example.com/about-sustainability-metrics', '_blank');
  });
});
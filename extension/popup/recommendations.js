// Recommendations page script
document.addEventListener('DOMContentLoaded', function() {
  // Apply theme and senior mode
  chrome.storage.sync.get(['settings'], (data) => {
    const seniorEnabled = data.settings?.seniorMode === true;
    document.documentElement.setAttribute('data-senior', seniorEnabled ? 'true' : 'false');
    
    const isDarkMode = data.settings?.darkMode !== false; // Default to dark mode
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
  });

  const recommendationsContent = document.getElementById('recommendations-content');
  const noRecommendations = document.getElementById('no-recommendations');
  const backButton = document.getElementById('back-button');  // Load recommendations from storage
  chrome.storage.local.get(['sustainabilityRecommendations', 'currentProductCategory'], function(result) {
    console.log('Loaded recommendations from storage:', result.sustainabilityRecommendations);
    console.log('Current product category:', result.currentProductCategory);
    
    // Update header with category info
    if (result.currentProductCategory && result.currentProductCategory !== 'Unknown') {
      const titleElement = document.getElementById('recommendations-title');
      titleElement.textContent = `Recommendations for ${result.currentProductCategory}`;
    }
    
    if (result.sustainabilityRecommendations && result.sustainabilityRecommendations.length > 0) {
      displayRecommendations(result.sustainabilityRecommendations);
    } else {
      showNoRecommendations();
    }
  });
  function displayRecommendations(recommendations) {
    recommendationsContent.innerHTML = '';
    
    // Add category information if available
    if (recommendations.length > 0) {
      const categoryElement = document.createElement('div');
      categoryElement.className = 'category-info';
      categoryElement.innerHTML = `<p style="margin-bottom: 16px; color: var(--color-text-secondary); font-style: italic;">Showing top sustainable products in similar categories</p>`;
      recommendationsContent.appendChild(categoryElement);
    }
    
    recommendations.forEach((recommendation, index) => {
      const recommendationElement = document.createElement('div');
      recommendationElement.className = 'recommendation-item';
      
      const score = recommendation.default_sustainability_score || recommendation.sustainability_score || 0;
      const scoreColor = getScoreColor(score);
      
      recommendationElement.innerHTML = `
        <div class="recommendation-header">
          <h3 class="recommendation-name">${recommendation.product_name || 'Unknown Product'}</h3>
          <div class="score-badge" style="background-color: ${scoreColor};">
            <span>${Math.round(score)}</span>
            <span>/100</span>
          </div>
        </div>
        <div class="recommendation-details">
          <div class="recommendation-brand">
            <strong>Brand:</strong> ${recommendation.brand || 'Unknown'}
          </div>
          <div class="recommendation-url">
            <a href="${recommendation.source_url}" target="_blank" class="recommendation-link">
              View Product →
            </a>
          </div>
        </div>
      `;
      
      recommendationsContent.appendChild(recommendationElement);
    });
  }

  function showNoRecommendations() {
    recommendationsContent.classList.add('hidden');
    noRecommendations.classList.remove('hidden');
  }

  function getScoreColor(score) {
    if (score === null || score === undefined || isNaN(score)) return '#ccc';
    if (score >= 70) return '#4CAF50'; // Green
    if (score >= 40) return '#FFC107'; // Yellow/Amber
    return '#F44336'; // Red
  }

  // Back button handler
  backButton.addEventListener('click', function() {
    window.location.href = 'popup.html';
  });
});

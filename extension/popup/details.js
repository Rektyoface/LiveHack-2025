document.addEventListener('DOMContentLoaded', function () {
  const detailsTitleElement = document.getElementById('details-title');
  const detailsContentElement = document.getElementById('details-content');
  const backButton = document.getElementById('back-button');

  chrome.storage.local.get(['sustainabilityDetails'], function (result) {
    if (result.sustainabilityDetails) {
      const { title, analysis } = result.sustainabilityDetails;
      detailsTitleElement.textContent = title || 'Sustainability Details';
      
      // Format the analysis text
      let formattedAnalysis = '';
      if (typeof analysis === 'string') {
        // Simple paragraph for plain string
        formattedAnalysis = `<p>${analysis.replace(/\n/g, '<br>')}</p>`;
      } else if (typeof analysis === 'object') {
        // If it's an object, iterate and display key-value pairs
        for (const key in analysis) {
          if (Object.hasOwnProperty.call(analysis, key)) {
            const value = analysis[key];
            const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); // Format key
            formattedAnalysis += `<h3>${formattedKey}</h3><p>${String(value).replace(/\n/g, '<br>')}</p>`;
          }
        }
      } else {
        formattedAnalysis = '<p>No details available.</p>';
      }
      detailsContentElement.innerHTML = formattedAnalysis;

      // Clear the stored details after displaying them
      chrome.storage.local.remove(['sustainabilityDetails']);
    } else {
      detailsTitleElement.textContent = 'Details Not Found';
      detailsContentElement.innerHTML = '<p>Could not load sustainability details. Please try again.</p>';
    }
  });

  backButton.addEventListener('click', function () {
    window.location.href = 'popup.html';
  });

  // Initialize theme
  chrome.storage.sync.get(['darkMode', 'settings'], (data) => {
    const isDarkMode = data.darkMode !== undefined ? data.darkMode : true;
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    
    const seniorEnabled = data.settings?.seniorMode === true;
    document.documentElement.setAttribute('data-senior', seniorEnabled ? 'true' : 'false');
  });
});

document.addEventListener('DOMContentLoaded', function () {
  const detailsTitleElement = document.getElementById('details-title');
  const detailsContentElement = document.getElementById('details-content');
  const backButton = document.getElementById('back-button');

  chrome.storage.local.get(['sustainabilityDetails'], function (result) {
    if (result.sustainabilityDetails && result.sustainabilityDetails.allFields) {
      const allFields = result.sustainabilityDetails.allFields;
      let html = '';
      allFields.forEach(field => {
        html += `<div class="details-section">
          <h2>${field.title}</h2>
          <div><strong>Rating:</strong> ${field.value} (${field.score ? field.score * 10 : '--'}/10)</div>
          <div><strong>Details:</strong> <p>${field.analysis.replace(/\n/g, '<br>')}</p></div>
        </div><hr>`;
      });
      detailsContentElement.innerHTML = html;
      chrome.storage.local.remove(['sustainabilityDetails']);
    } else {
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

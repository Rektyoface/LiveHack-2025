// EcoShop Options Script
document.addEventListener('DOMContentLoaded', function() {
  // Elements
  const carbonWeightInput = document.getElementById('carbon-weight');
  const waterWeightInput = document.getElementById('water-weight');
  const wasteWeightInput = document.getElementById('waste-weight');
  const laborWeightInput = document.getElementById('labor-weight');
  
  const carbonWeightValue = document.getElementById('carbon-weight-value');
  const waterWeightValue = document.getElementById('water-weight-value');
  const wasteWeightValue = document.getElementById('waste-weight-value');
  const laborWeightValue = document.getElementById('labor-weight-value');
  
  const showBadgeCheckbox = document.getElementById('show-badge');
  const showAlternativesCheckbox = document.getElementById('show-alternatives');
  const badgePositionSelect = document.getElementById('badge-position');
  const darkModeCheckbox = document.getElementById('dark-mode');
    const apiEndpointInput = document.getElementById('api-endpoint');
  const dataContributionCheckbox = document.getElementById('data-contribution');
  
  const restoreDefaultsButton = document.getElementById('restore-defaults');
  const saveSettingsButton = document.getElementById('save-settings');
  const statusMessage = document.getElementById('status-message');
  // Default settings
  const defaultSettings = {
    carbonWeight: 3,
    waterWeight: 3,
    wasteWeight: 3,
    laborWeight: 3,
    showBadge: true,
    showAlternatives: true,
    badgePosition: 'bottom-right',
    darkMode: true,
    apiEndpoint: 'http://localhost:5000/api/score',
    dataContribution: false
  };
  
  // Initialize theme from storage
  initTheme();
  
  // Load settings when the page loads
  loadSettings();
  
  // Initialize theme from saved preference
  async function initTheme() {
    try {
      const result = await chrome.storage.sync.get({ 'darkMode': true });
      setTheme(result.darkMode);
    } catch (error) {
      console.error("Error loading theme preference:", error);
      // Default to dark mode
      setTheme(true);
    }
  }
  
  // Set theme on page
  function setTheme(isDarkMode) {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
  }
  
  // Update display when sliders change
  carbonWeightInput.addEventListener('input', () => {
    carbonWeightValue.textContent = carbonWeightInput.value;
  });
  
  waterWeightInput.addEventListener('input', () => {
    waterWeightValue.textContent = waterWeightInput.value;
  });
  
  wasteWeightInput.addEventListener('input', () => {
    wasteWeightValue.textContent = wasteWeightInput.value;
  });
  
  laborWeightInput.addEventListener('input', () => {
    laborWeightValue.textContent = laborWeightInput.value;
  });
  
  // Save settings when the save button is clicked
  saveSettingsButton.addEventListener('click', saveSettings);
  
  // Restore defaults when the restore button is clicked
  restoreDefaultsButton.addEventListener('click', restoreDefaults);
  
  // Toggle dark mode preview
  darkModeCheckbox.addEventListener('change', () => {
    const isDarkMode = darkModeCheckbox.checked;
    setTheme(isDarkMode);
    chrome.storage.sync.set({ 'darkMode': isDarkMode });
  });
  
  // Save all current settings to storage
  function saveSettings() {
    const settings = {
      carbonWeight: parseInt(carbonWeightInput.value),
      waterWeight: parseInt(waterWeightInput.value),
      wasteWeight: parseInt(wasteWeightInput.value),
      laborWeight: parseInt(laborWeightInput.value),
      showBadge: showBadgeCheckbox.checked,
      showAlternatives: showAlternativesCheckbox.checked,
      badgePosition: badgePositionSelect.value,      darkMode: darkModeCheckbox.checked,
      apiEndpoint: apiEndpointInput.value.trim(),
      dataContribution: dataContributionCheckbox.checked
    };
    
    // Save both 'settings' object and the separate 'darkMode' setting for easier access
    chrome.storage.sync.set({ 
      settings: settings,
      darkMode: settings.darkMode
    }, () => {
      showStatus('Settings saved successfully!', 'success');
      
      // Notify the service worker that settings have changed
      chrome.runtime.sendMessage({ 
        action: "settingsUpdated", 
        settings: settings 
      });
    });
  }
  
  // Load saved settings from storage
  function loadSettings() {
    chrome.storage.sync.get(['settings', 'darkMode'], (data) => {
      const settings = data.settings || defaultSettings;
      
      // If darkMode is set separately (from popup or content script), use that value
      const darkMode = data.darkMode !== undefined ? data.darkMode : settings.darkMode;
      
      // Apply loaded settings to UI
      carbonWeightInput.value = settings.carbonWeight;
      carbonWeightValue.textContent = settings.carbonWeight;
      
      waterWeightInput.value = settings.waterWeight;
      waterWeightValue.textContent = settings.waterWeight;
      
      wasteWeightInput.value = settings.wasteWeight;
      wasteWeightValue.textContent = settings.wasteWeight;
      
      laborWeightInput.value = settings.laborWeight;
      laborWeightValue.textContent = settings.laborWeight;
      
      showBadgeCheckbox.checked = settings.showBadge;
      showAlternativesCheckbox.checked = settings.showAlternatives;
      badgePositionSelect.value = settings.badgePosition;
      darkModeCheckbox.checked = darkMode;
        apiEndpointInput.value = settings.apiEndpoint || '';
      dataContributionCheckbox.checked = settings.dataContribution;
      
      // Apply dark mode if enabled
      setTheme(darkMode);
    });
  }
  
  // Restore default settings
  function restoreDefaults() {
    // Apply default settings to UI
    carbonWeightInput.value = defaultSettings.carbonWeight;
    carbonWeightValue.textContent = defaultSettings.carbonWeight;
    
    waterWeightInput.value = defaultSettings.waterWeight;
    waterWeightValue.textContent = defaultSettings.waterWeight;
    
    wasteWeightInput.value = defaultSettings.wasteWeight;
    wasteWeightValue.textContent = defaultSettings.wasteWeight;
    
    laborWeightInput.value = defaultSettings.laborWeight;
    laborWeightValue.textContent = defaultSettings.laborWeight;
    
    showBadgeCheckbox.checked = defaultSettings.showBadge;
    showAlternativesCheckbox.checked = defaultSettings.showAlternatives;
    badgePositionSelect.value = defaultSettings.badgePosition;
    darkModeCheckbox.checked = defaultSettings.darkMode;
      apiEndpointInput.value = defaultSettings.apiEndpoint;
    dataContributionCheckbox.checked = defaultSettings.dataContribution;
    
    setTheme(defaultSettings.darkMode);
    
    showStatus('Default settings restored. Click Save to apply.', 'success');
  }
  
  // Display status message
  function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = 'status-message ' + type;
    
    // Clear the message after a few seconds
    setTimeout(() => {
      statusMessage.className = 'status-message';
    }, 3000);
  }
});
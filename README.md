# EcoShop - Sustainability Shopping Companion

EcoShop is a browser extension that provides real-time sustainability information about brands and products as you shop online. It helps consumers make more environmentally conscious purchasing decisions by presenting easy-to-understand sustainability scores and offering greener alternatives.

## Key Features

- **Real-time sustainability scores** for products and brands as you browse
- **Visual indicators** showing environmental impact using an intuitive traffic light system
- **Detailed sustainability metrics** including carbon footprint, water usage, waste generation, and labor practices
- **Alternative product recommendations** for more sustainable options
- **Customizable settings** to prioritize specific environmental factors that matter most to you

## Installation Instructions

### Load Unpacked Extension (Development Mode)

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/ecoshop.git
   cd ecoshop
   ```

2. Open your Chromium-based browser (Chrome, Edge, Brave, etc.)

3. Navigate to the extensions page:
   - Chrome/Brave: `chrome://extensions/`
   - Edge: `edge://extensions/`

4. Enable "Developer mode" (toggle in the top right corner)

5. Click "Load unpacked" and select the `extension/` folder from this repository

6. The EcoShop extension should now appear in your browser toolbar

## Sample Product URLs for Testing

Test the extension with these product URLs:

- Amazon: `https://www.amazon.com/dp/B07QN3683G` (Patagonia product)
- Etsy: `https://www.etsy.com/listing/123456789/product` (Any product will work)
- Any supported e-commerce site with product pages from brands in our dataset (see data/esg_scores.json)

## Running the Backend API (Optional)

The extension works offline using local data. If you want to use the backend API for more dynamic data:

1. Install requirements:
   ```
   cd backend
   pip install -r requirements.txt
   ```

2. Run the Flask app:
   ```
   python app.py
   ```

3. The API will be accessible at `http://localhost:5000/`

4. To use the API with the extension, go to the extension options and set the API endpoint to `http://localhost:5000/api/score`

## File Structure

```
├── README.md
├── backend/                  # Optional backend API
│   ├── app.py                # Flask API for sustainability data  
│   └── requirements.txt      # Python dependencies
├── data/
│   └── esg_scores.json       # Sustainability data for brands
├── extension/
│   ├── content.js            # Content script injected into web pages
│   ├── manifest.json         # Extension manifest file
│   ├── service_worker.js     # Background service worker
│   ├── icons/                # Extension icons
│   ├── options/              # User settings page
│   └── popup/                # Extension popup UI
└── scripts/
    └── fetch_esg_data.py     # Script to update sustainability data
```

## Refreshing Data

To update the sustainability data:

```
python scripts/fetch_esg_data.py --backup
```

This will fetch the latest data from configured sources and update the local dataset.

## License

[MIT License](https://opensource.org/licenses/MIT)

## Team

Created during the LiveHack 2025 hackathon for environmental sustainability.
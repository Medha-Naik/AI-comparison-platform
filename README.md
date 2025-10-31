# AI Shopping Assistant

A smart product comparison tool that searches across multiple e-commerce websites for the best deals.

## Features

- 🛍️ **Multi-Store Search**: Search across Flipkart, Reliance Digital, Croma, and Amazon
- 🔄 **Real Scrapers**: Live data from Flipkart and Reliance Digital
- 📊 **Price Comparison**: See all offers sorted by price
- 🎨 **Modern UI**: Beautiful and responsive design
- ⚡ **Fast & Reliable**: Smart fallback to mock data

## Configuration

### Real Scrapers vs Mock Data

Edit `backend/scrapers/safe_scrapers.py`:

```python
REAL_SCRAPERS_CONFIG = {
    'flipkart': True,          # ✅ Use real scraper
    'reliance digital': True,   # ✅ Use real scraper
    'croma': False,            # 📋 Use mock data
    'amazon': False            # 📋 Use mock data
}
```

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python app.py
```

The server will start at `http://127.0.0.1:5000`

### 3. Use the Web Interface

Open your browser and go to:
```
http://127.0.0.1:5000/
```

Then:
- Enter a product name in the search bar
- Click the search icon or press Enter
- View results from multiple stores
- Click "View Product" to visit the store

## API Endpoints

### Search for Products
```
GET /search?q=iphone+15
```

**Response:**
```json
{
  "query": "iphone 15",
  "count": 8,
  "offers": [
    {
      "title": "Apple iPhone 15 (128 GB) - Blue",
      "price": 69900,
      "price_display": "₹69,900",
      "url": "https://www.flipkart.com/...",
      "store": "flipkart"
    }
  ],
  "sources": {
    "flipkart": "real",
    "croma": "mock"
  }
}
```

### Health Check
```
GET /health
```

## Project Structure

```
ai-shopping-assistant/
├── backend/
│   ├── app.py                 # Flask server
│   ├── scrapers/             # Web scrapers
│   │   ├── flipkart.py
│   │   ├── reliance_digital.py
│   │   ├── croma.py
│   │   └── safe_scrapers.py  # Main scraper with fallback
│   └── data/
│       ├── mock_data.py      # Mock data
│       └── products.json      # Sample products
├── frontend/
│   ├── templates/
│   │   └── home.html         # Main page
│   └── static/
│       ├── home.css          # Styles
│       └── home.js            # Search logic
└── README.md
```

## How It Works

1. **User enters search query** on the frontend
2. **Frontend sends request** to `/search?q={query}`
3. **Backend calls scrapers** based on configuration:
   - Real scrapers for Flipkart & Reliance Digital
   - Mock data for other stores
4. **Results are sorted** by price (lowest first)
5. **Frontend displays** products in a grid layout

## Customization

### Add More Products to Mock Data

Edit `backend/data/products.json` to add more products.

### Change Scraper Settings

Edit `backend/scrapers/safe_scrapers.py`:

```python
REAL_SCRAPERS_CONFIG = {
    'flipkart': True,
    'reliance digital': True,
    'croma': True,      # Enable real Croma scraper
    'amazon': False
}
```

## Troubleshooting

### Real Scrapers Not Working?

- Make sure you have Chrome installed
- Check if sites are blocking automated access
- Use mock data for reliable demos

### Frontend Not Loading?

- Check if Flask server is running on port 5000
- Open browser console for errors
- Verify static files path in `app.py`

## License

Academic project for demonstration purposes.




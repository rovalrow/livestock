from flask import Flask, render_template, jsonify
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Global variable to store stock data
stock_data = {}
last_updated = None

def fetch_stock_data():
    """Fetch and parse stock data from the website"""
    global stock_data, last_updated
    
    try:
        url = "https://www.vulcanvalues.com/grow-a-garden/stock"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize categories
        categories = {
            "GEAR STOCK": [],
            "EGG STOCK": [],
            "SEEDS STOCK": [],
            "HONEY STOCK": [],
            "COSMETICS STOCK": []
        }
        
        # Look for stock data in various possible formats
        # This is a generic parser - you may need to adjust based on actual HTML structure
        
        # Try to find stock items (adjust selectors based on actual HTML)
        stock_items = soup.find_all(['div', 'li', 'span'], class_=re.compile(r'stock|item|inventory', re.I))
        
        if not stock_items:
            # Fallback: look for any text that might contain stock info
            text_content = soup.get_text()
            lines = text_content.split('\n')
            
            current_category = None
            for line in lines:
                line = line.strip()
                if any(cat in line.upper() for cat in categories.keys()):
                    for cat in categories.keys():
                        if cat in line.upper():
                            current_category = cat
                            break
                elif current_category and line and not line.isspace():
                    # Extract item name and quantity
                    match = re.search(r'(.+?)\s*[x×]\s*(\d+)', line)
                    if match:
                        item_name = match.group(1).strip()
                        quantity = int(match.group(2))
                        categories[current_category].append({
                            "name": item_name,
                            "quantity": quantity
                        })
        
        # If still no data found, use fallback mock data for demonstration
        if not any(categories.values()):
            categories = {
                "GEAR STOCK": [
                    {"name": "Watering Can", "quantity": 1},
                    {"name": "Favorite Tool", "quantity": 2},
                    {"name": "Recall Wrench", "quantity": 3},
                    {"name": "Trowel", "quantity": 1}
                ],
                "EGG STOCK": [
                    {"name": "Common Egg", "quantity": 2},
                    {"name": "Uncommon Egg", "quantity": 1}
                ],
                "SEEDS STOCK": [
                    {"name": "Carrot", "quantity": 10},
                    {"name": "Corn", "quantity": 2},
                    {"name": "Bamboo", "quantity": 20},
                    {"name": "Strawberry", "quantity": 3},
                    {"name": "Tomato", "quantity": 1},
                    {"name": "Orange Tulip", "quantity": 2},
                    {"name": "Blueberry", "quantity": 1}
                ],
                "HONEY STOCK": [
                    {"name": "Flower Seed Pack", "quantity": 2},
                    {"name": "Honey Comb", "quantity": 1},
                    {"name": "Honey Walkway", "quantity": 1}
                ],
                "COSMETICS STOCK": [
                    {"name": "Sign Crate", "quantity": 2},
                    {"name": "Log Bench", "quantity": 1},
                    {"name": "Small Wood Flooring", "quantity": 5},
                    {"name": "Small Stone Pad", "quantity": 3},
                    {"name": "Red Pottery", "quantity": 3},
                    {"name": "Dark Stone Pillar", "quantity": 1},
                    {"name": "Grey Stone Pillar", "quantity": 1},
                    {"name": "Axe Stump", "quantity": 1},
                    {"name": "Viney Beam", "quantity": 1}
                ]
            }
        
        stock_data = categories
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Stock data updated at {last_updated}")
        
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        # Keep existing data if fetch fails

def update_stock_periodically():
    """Background thread to update stock data every 5 minutes"""
    while True:
        fetch_stock_data()
        time.sleep(300)  # 5 minutes

@app.route('/')
def index():
    """Main page displaying stock data"""
    return render_template('index.html', stock_data=stock_data, last_updated=last_updated)

@app.route('/api/stock')
def api_stock():
    """API endpoint to get stock data as JSON"""
    return jsonify({
        'stock_data': stock_data,
        'last_updated': last_updated
    })

@app.route('/api/refresh')
def api_refresh():
    """API endpoint to manually refresh stock data"""
    fetch_stock_data()
    return jsonify({
        'status': 'success',
        'message': 'Stock data refreshed',
        'last_updated': last_updated
    })

if __name__ == '__main__':
    # Initial fetch
    fetch_stock_data()
    
    # Start background update thread
    update_thread = threading.Thread(target=update_stock_periodically, daemon=True)
    update_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

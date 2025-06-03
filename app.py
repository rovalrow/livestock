from flask import Flask, render_template, jsonify, Response
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
weather_data = {}
last_updated = None

# Category icons mapping
CATEGORY_ICONS = {
    "SEEDS": "🌱",
    "GEARS": "⚙️",
    "EGGS": "🥚",
    "EVENT_SHOP": "🎪",
    "COSMETICS": "💄"
}

def fetch_swertres_results():
    url = "https://www.lottopcso.com/swertres-result-today/"
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table with 3D results
        table = soup.find('table')
        if not table:
            return []

        results = []
        rows = table.find_all('tr')[1:]  # skip header
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                time = cols[0].text.strip()
                result = cols[1].text.strip()
                results.append(f"{time} {result}")
        return results
    except Exception as e:
        print(f"Failed to fetch Swertres results: {e}")
        return []

def fetch_stock_data():
    """Fetch and parse stock data from the website"""
    global stock_data, weather_data, last_updated
    
    try:
        url = "https://growagardenvalues.com/stock/stocks.php"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Initialize categories
        categories = {
            "SEEDS": [],
            "GEARS": [],
            "EGGS": [],
            "EVENT_SHOP": [],
            "COSMETICS": []
        }
        
        weather_info = {
            "current": None,
            "recent": []
        }
        
        # Parse Seeds section
        seeds_section = soup.find('section', {'id': 'seeds-section'})
        if seeds_section:
            stock_items = seeds_section.find_all('div', class_='stock-item')
            for item in stock_items:
                name_elem = item.find('div', class_='item-name')
                quantity_elem = item.find('div', class_='item-quantity')
                
                if name_elem and quantity_elem:
                    name = name_elem.get_text().strip()
                    quantity_text = quantity_elem.get_text().strip()
                    
                    # Extract quantity number
                    quantity_match = re.search(r'x(\d+)', quantity_text)
                    if quantity_match:
                        quantity = int(quantity_match.group(1))
                        categories["SEEDS"].append({
                            "name": name,
                            "quantity": quantity
                        })
        
        # Parse Gears section
        gears_section = soup.find('section', {'id': 'gears-section'})
        if gears_section:
            stock_items = gears_section.find_all('div', class_='stock-item')
            for item in stock_items:
                name_elem = item.find('div', class_='item-name')
                quantity_elem = item.find('div', class_='item-quantity')
                
                if name_elem and quantity_elem:
                    name = name_elem.get_text().strip()
                    quantity_text = quantity_elem.get_text().strip()
                    
                    # Extract quantity number
                    quantity_match = re.search(r'x(\d+)', quantity_text)
                    if quantity_match:
                        quantity = int(quantity_match.group(1))
                        categories["GEARS"].append({
                            "name": name,
                            "quantity": quantity
                        })
        
        # Parse Eggs section
        eggs_section = soup.find('section', {'id': 'eggs-section'})
        if eggs_section:
            stock_items = eggs_section.find_all('div', class_='stock-item')
            for item in stock_items:
                name_elem = item.find('div', class_='item-name')
                quantity_elem = item.find('div', class_='item-quantity')
                
                if name_elem and quantity_elem:
                    name = name_elem.get_text().strip()
                    quantity_text = quantity_elem.get_text().strip()
                    
                    # Extract quantity number
                    quantity_match = re.search(r'x(\d+)', quantity_text)
                    if quantity_match:
                        quantity = int(quantity_match.group(1))
                        categories["EGGS"].append({
                            "name": name,
                            "quantity": quantity
                        })
        
        # Parse Event Shop Stock section
        event_section = soup.find('section', {'id': 'event-shop-stock-section'})
        if event_section:
            stock_items = event_section.find_all('div', class_='stock-item')
            for item in stock_items:
                name_elem = item.find('div', class_='item-name')
                quantity_elem = item.find('div', class_='item-quantity')
                
                if name_elem and quantity_elem:
                    name = name_elem.get_text().strip()
                    quantity_text = quantity_elem.get_text().strip()
                    
                    # Extract quantity number
                    quantity_match = re.search(r'x(\d+)', quantity_text)
                    if quantity_match:
                        quantity = int(quantity_match.group(1))
                        categories["EVENT_SHOP"].append({
                            "name": name,
                            "quantity": quantity
                        })
        
        # Parse Cosmetics section
        cosmetics_section = soup.find('section', {'id': 'cosmetics-section'})
        if cosmetics_section:
            stock_items = cosmetics_section.find_all('div', class_='stock-item')
            for item in stock_items:
                name_elem = item.find('div', class_='item-name')
                quantity_elem = item.find('div', class_='item-quantity')
                
                if name_elem and quantity_elem:
                    name = name_elem.get_text().strip()
                    quantity_text = quantity_elem.get_text().strip()
                    
                    # Extract quantity number
                    quantity_match = re.search(r'x(\d+)', quantity_text)
                    if quantity_match:
                        quantity = int(quantity_match.group(1))
                        categories["COSMETICS"].append({
                            "name": name,
                            "quantity": quantity
                        })
        
        # Parse Weather section
        weather_section = soup.find('section', {'id': 'weather-section'})
        if weather_section:
            stock_items = weather_section.find_all('div', class_='stock-item')
            for item in stock_items:
                name_elem = item.find('div', class_='item-name')
                quantity_elem = item.find('div', class_='item-quantity')
                
                if name_elem and quantity_elem:
                    weather_name = name_elem.get_text().strip()
                    time_info = quantity_elem.get_text().strip()
                    
                    # Check if this is the current weather (Most Recent)
                    if "Most Recent" in time_info:
                        weather_info["current"] = weather_name
                    else:
                        weather_info["recent"].append({
                            "condition": weather_name,
                            "time": time_info
                        })
        
        stock_data = categories
        weather_data = weather_info
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        total_items = sum(len(items) for items in categories.values())
        print(f"Stock data updated at {last_updated}")
        print(f"Found {total_items} items across all categories")
        print(f"Seeds: {len(categories['SEEDS'])}, Gears: {len(categories['GEARS'])}, Eggs: {len(categories['EGGS'])}")
        print(f"Event Shop: {len(categories['EVENT_SHOP'])}, Cosmetics: {len(categories['COSMETICS'])}")
        print(f"Current weather: {weather_info['current']}")
        
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
    return render_template('index.html', 
                         stock_data=stock_data, 
                         weather_data=weather_data,
                         last_updated=last_updated,
                         category_icons=CATEGORY_ICONS)

@app.route('/api/stock')
def api_stock():
    """API endpoint to get stock data as JSON"""
    return jsonify({
        'stock_data': stock_data,
        'weather_data': weather_data,
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

@app.route('/api/3d')
def api_3d():
    results = fetch_swertres_results()
    return jsonify({
        "date": datetime.now().strftime("%B %d, %Y"),
        "results": results
    })

@app.route('/api/category/<category>')
def api_category(category):
    """API endpoint to get specific category data"""
    category_upper = category.upper()
    if category_upper in stock_data:
        return jsonify({
            'category': category_upper,
            'items': stock_data[category_upper],
            'last_updated': last_updated
        })
    else:
        return jsonify({
            'error': 'Category not found',
            'available_categories': list(stock_data.keys())
        }), 404

@app.route('/api/weather')
def api_weather():
    """API endpoint to get weather data"""
    return jsonify({
        'weather_data': weather_data,
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

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
weather_data = {}
last_updated = None

def parse_stock_section(soup, section_name):
    """Parse a specific stock section from the HTML"""
    items = []
    
    # Find the section header
    section_header = soup.find(text=re.compile(section_name, re.I))
    if not section_header:
        return items
    
    # Find the parent element and get subsequent elements
    current = section_header.parent if section_header.parent else section_header
    
    # Navigate to find items after the header
    while current:
        current = current.find_next_sibling() if hasattr(current, 'find_next_sibling') else None
        if not current:
            break
            
        # Stop if we hit another section
        if current.get_text() and any(sect in current.get_text().upper() for sect in 
                                     ['SEEDS', 'GEARS', 'EGGS', 'WEATHER', 'EVENT SHOP', 'COSMETICS']):
            if section_name.upper() not in current.get_text().upper():
                break
        
        # Look for item patterns
        text = current.get_text().strip()
        if text and 'x' in text:
            # Extract item name and quantity
            match = re.search(r'(.+?)\s*x(\d+)', text)
            if match:
                item_name = match.group(1).strip()
                quantity = int(match.group(2))
                items.append({
                    "name": item_name,
                    "quantity": quantity
                })
    
    return items

def fetch_stock_data():
    """Fetch and parse stock data from the new website"""
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
        
        # Get all text content and split into lines for easier parsing
        text_content = soup.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        # Initialize categories
        categories = {
            "SEEDS": [],
            "GEARS": [],
            "EGGS": [],
            "EVENT_SHOP": [],
            "COSMETICS": [],
            "COSMETIC_CRATES": [],
            "COSMETIC_ITEMS": []
        }
        
        weather_info = {
            "current": None,
            "recent": []
        }
        
        current_category = None
        current_subcategory = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for main categories
            if line.upper() == "SEEDS":
                current_category = "SEEDS"
                current_subcategory = None
            elif line.upper() == "GEARS":
                current_category = "GEARS"
                current_subcategory = None
            elif line.upper() == "EGGS":
                current_category = "EGGS"
                current_subcategory = None
            elif line.upper() == "EVENT SHOP STOCK":
                current_category = "EVENT_SHOP"
                current_subcategory = None
            elif line.upper() == "COSMETICS":
                current_category = "COSMETICS"
                current_subcategory = None
            elif line.upper() == "COSMETIC CRATES":
                current_category = "COSMETICS"
                current_subcategory = "COSMETIC_CRATES"
            elif line.upper() == "COSMETIC ITEMS":
                current_category = "COSMETICS"
                current_subcategory = "COSMETIC_ITEMS"
            elif line.upper() == "WEATHER":
                current_category = "WEATHER"
                current_subcategory = None
            
            # Parse weather information
            elif current_category == "WEATHER":
                if "Frost" in line or "Rain" in line or "Thunderstorm" in line:
                    if "Most Recent" in lines[i+1:i+2]:
                        weather_info["current"] = line
                    else:
                        # Look for time information in next lines
                        time_info = ""
                        if i + 1 < len(lines) and ("ago" in lines[i+1] or "mins" in lines[i+1] or "hours" in lines[i+1]):
                            time_info = lines[i+1]
                        weather_info["recent"].append({
                            "condition": line,
                            "time": time_info
                        })
            
            # Parse items with quantities
            elif current_category and current_category != "WEATHER":
                # Look for pattern: ItemName x[number]
                match = re.search(r'^(.+?)\s*x(\d+)$', line)
                if match:
                    item_name = match.group(1).strip()
                    quantity = int(match.group(2))
                    
                    item = {
                        "name": item_name,
                        "quantity": quantity
                    }
                    
                    if current_subcategory == "COSMETIC_CRATES":
                        categories["COSMETIC_CRATES"].append(item)
                    elif current_subcategory == "COSMETIC_ITEMS":
                        categories["COSMETIC_ITEMS"].append(item)
                    elif current_category in categories:
                        categories[current_category].append(item)
            
            i += 1
        
        # Combine cosmetic subcategories
        if categories["COSMETIC_CRATES"] or categories["COSMETIC_ITEMS"]:
            categories["COSMETICS"] = categories["COSMETIC_CRATES"] + categories["COSMETIC_ITEMS"]
        
        # Clean up empty subcategories
        del categories["COSMETIC_CRATES"]
        del categories["COSMETIC_ITEMS"]
        
        stock_data = categories
        weather_data = weather_info
        last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Stock data updated at {last_updated}")
        print(f"Found items: {sum(len(items) for items in categories.values())}")
        
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
                         last_updated=last_updated)

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

if __name__ == '__main__':
    # Initial fetch
    fetch_stock_data()
    
    # Start background update thread
    update_thread = threading.Thread(target=update_stock_periodically, daemon=True)
    update_thread.start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)

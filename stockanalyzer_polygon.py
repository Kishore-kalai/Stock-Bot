from flask import Flask, render_template, request, jsonify
import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import time
from functools import lru_cache

app = Flask(__name__)

# Replace this with your Polygon.io API Key
API_KEY = "xxxxxxxxx"

@lru_cache(maxsize=10)
def get_stock_data(ticker, period):
    """
    Fetch stock data using Polygon.io API and generate plot.
    Uses caching to reduce API calls and retries on rate limits.
    """
    # Define the date range based on the selected period
    period_mapping = {
        "1d": 1,
        "5d": 5,
        "1mo": 30,
        "3mo": 90,
        "6mo": 180,
        "1y": 365
    }

    days = period_mapping.get(period, 1)
    
    # Get today's date and the start date for the data
    end_date = time.strftime("%Y-%m-%d")
    start_date = (time.time() - (days * 86400))  # Convert days to seconds
    start_date = time.strftime("%Y-%m-%d", time.localtime(start_date))

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}?adjusted=true&sort=asc&apiKey={API_KEY}"
    
    retries = 3  # Number of retries on rate limit error
    delay = 5  # Delay (in seconds) between retries

    for attempt in range(retries):
        try:
            response = requests.get(url)
            if response.status_code == 429:
                print(f"Rate limited. Retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
                time.sleep(delay)
                continue
            elif response.status_code != 200:
                return None, None
            
            data = response.json()
            if "results" not in data or not data["results"]:
                return None, None
            
            # Extract closing prices and timestamps
            timestamps = [entry["t"] for entry in data["results"]]
            prices = [entry["c"] for entry in data["results"]]

            # Convert timestamps to readable dates
            dates = [time.strftime('%Y-%m-%d', time.localtime(ts / 1000)) for ts in timestamps]

            # Plot stock data
            plt.figure(figsize=(10, 6))
            plt.plot(dates, prices, 'b-')
            plt.title(f'{ticker} Stock Price')
            plt.xlabel('Date')
            plt.ylabel('Price (USD)')
            plt.grid(True)
            plt.xticks(rotation=45)

            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            plt.close('all')

            plot_data = base64.b64encode(buffer.getvalue()).decode()

            stock_info = {
                'current_price': prices[-1],
                'high': max(prices),
                'low': min(prices),
                'period': period
            }

            return stock_info, plot_data

        except Exception as e:
            print(f"Error fetching stock data: {str(e)}")
            return None, None

    return None, None  # Return None after max retries

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_stock', methods=['POST'])
def get_stock():
    try:
        ticker = request.form.get('ticker', '').upper()
        period = request.form.get('period', '1d')

        if not ticker:
            return jsonify({'error': 'Please enter a valid stock ticker'})

        stock_info, plot_data = get_stock_data(ticker, period)

        if stock_info is None:
            return jsonify({'error': f'Unable to fetch data for {ticker}'})
            
        return jsonify({
            'stock_info': stock_info,
            'plot_data': plot_data
        })
        
    except Exception as e:
        print(f"Error in get_stock route: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your request'})

if __name__ == '__main__':
    app.run(debug=True, threaded=True)


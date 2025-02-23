from flask import Flask, render_template, request, jsonify
import yfinance as yf
import matplotlib
matplotlib.use('Agg')   
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta
import pandas as pd

app = Flask(__name__)

def get_stock_data(ticker, period):
    """
    Fetch stock data using yfinance and generate plot
    Returns stock info and base64 encoded plot
    """
    try:
        
        stock = yf.Ticker(ticker)
        
         
        period_mapping = {
            "1d": ("1d", "5m"),     
            "5d": ("5d", "15m"),     
            "1mo": ("1mo", "1d"),    
            "3mo": ("3mo", "1d"),    
            "6mo": ("6mo", "1d"),    
            "1y": ("1y", "1d")       
        }
        
      
        selected_period, interval = period_mapping.get(period, ("1d", "5m"))
        
       
        hist = stock.history(period=selected_period, interval=interval)
        
        if hist.empty:
            return None, None
            
        
        plt.figure(figsize=(10, 6))
        plt.plot(hist.index, hist['Close'], 'b-')
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
            'current_price': hist['Close'].iloc[-1],   
            'high': hist['High'].max(),
            'low': hist['Low'].min(),
            'period': period
        }
        
        return stock_info, plot_data
        
    except Exception as e:
        print(f"Error fetching stock data: {str(e)}")
        return None, None
    finally:
        plt.close('all')   

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
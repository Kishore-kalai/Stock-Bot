import json
import openai
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import yfinance as yf
from openai import OpenAI


openai.api_key = open('API_KEY', 'r').read()


def get_stock_price(ticker):
    return str(yf.Ticker(ticker).history(period='1y').iloc[-1].Close)


def calculate_SMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.rolling(window=window).mean().iloc[-1])


def calculate_EMA(ticker, window):
    data = yf.Ticker(ticker).history(period='1y').Close
    return str(data.ewm(span=window, adjust=False).mean().iloc[-1])


def calculate_RSI(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    delta = data.diff()
    up = data.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=14 - 1, adjust=False).mean()
    ema_down = up.ewm(com=14 - 1, adjust=False).mean()
    rs = ema_up / ema_down
    return str(100 - (100 / (1 + rs)).iloc[-1])


def calculate_MACD(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    short_EMA = data.ewm(span=12, adjust=False).mean()
    long_EMA = data.ewm(span=26, adjust=False).mean()

    MACD = short_EMA - long_EMA
    signal = MACD.ewm(span=9, adjust=False).mean()
    MACD_histogram = MACD - signal

    return f'{MACD[-1]}, {signal[-1]}, {MACD_histogram[-1]}'


def plot_stock_price(ticker):
    data = yf.Ticker(ticker).history(period='1y').Close
    plt.figure(figsize=(10, 5))
    plt.plot(data.index, data)
    plt.title(f'{ticker} Stock price over Last year')
    plt.xlabel('Date')
    plt.ylabel('Stock Price ($)')
    plt.grid(True)
    plt.savefig('stock.png')
    plt.close()


functions = [
    {
        'name': 'get_stock_price',
        'description': 'Gets the latest stock price given the ticker symbol of a company',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (for example, AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'calculate_SMA',
        'description': 'Calculate the simple moving average of a given stock ticker and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (for example, AAPL for Apple).'
                },
                'window': {
                    'type': 'string',
                    'description': 'The timeframe to consider when calculating the SMA'
                },
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_EMA',
        'description': 'Calculate the exponential moving average of a given stock ticker and a window',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (for example, AAPL for Apple).'
                },
                'window': {
                    'type': 'string',
                    'description': 'The timeframe to consider when calculating the EMA'
                },
            },
            'required': ['ticker', 'window'],
        },
    },
    {
        'name': 'calculate_RSI',
        'description': 'Calculates the RSI of the given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (for example, AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'calculate_MACD',
        'description': 'Calculates the MACD of the given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (for example, AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
    {
        'name': 'plot_stock_price',
        'description': 'Plots the stock price for the last year of the given stock ticker',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticker': {
                    'type': 'string',
                    'description': 'The stock ticker symbol of a company (for example, AAPL for Apple).'
                },
            },
            'required': ['ticker'],
        },
    },
]

available_functions = {
    'get_stock_price': get_stock_price,
    'calculate_SMA': calculate_SMA,
    'calculate_EMA': calculate_EMA,
    'calculate_RSI': calculate_RSI,
    'calculate_MACD': calculate_MACD,
    'plot_stock_price': plot_stock_price,
}

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

st.title('Dublin Hangout Stock Chatbot Assistant')

user_input = st.text_input('Your Input:')

if user_input:
    try:
        st.session_state['messages'].append({'role': 'user', 'content': f'{user_input}'})
        client = OpenAI()
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=st.session_state['messages'],
            functions=functions,
            function_call='auto'
        )
        response_message = response.choices[0].message    

        if hasattr(response_message, 'function_call') and response_message.function_call:    
            function_name = response_message.function_call.name    
            function_args = json.loads(response_message.function_call.arguments)    
            if function_name in ['get_stock_price', 'plot_stock_price', 'calculate_RSI', 'calculate_MACD']:
                args_dict = {'ticker': function_args.get('ticker')}
            elif function_name in ['calculate_SMA', 'calculate_EMA']:
                args_dict = {'ticker': function_args.get('ticker'), 'window': function_args.get('window')}

            function_to_call = available_functions[function_name]
            function_response = function_to_call(**args_dict)

            if function_name == 'plot_stock_price':
                st.image('stock.png')
            else:
                st.session_state['messages'].append(response_message)
                st.session_state['messages'].append(
                    {
                        'role': 'function',
                        'name': function_name,
                        'content': function_response
                    }
                )

                second_response = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=st.session_state['messages'],
                )
                st.text(second_response.choices[0].message.content)    
                st.session_state['messages'].append({'role': 'assistant', 'content': second_response.choices[0].message.content})    
        else:
            st.text(response_message.content)
            st.session_state['messages'].append({'role': 'assistant', 'content': response_message.content})

    except Exception as e:
        raise e


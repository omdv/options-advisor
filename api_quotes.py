"""
Routines to get market quotes
"""
import os
import requests
import pandas as pd


def get_quotes(ticker, n_days=252):
    """
    Get quotes for a given ticker
    Legacy:
        quotes = yf.Ticker(ticker).history(period=period)
        quotes.index = pd.to_datetime(quotes.index.strftime('%Y-%m-%d'))
        return quotes
    """
    api_key = os.environ.get('TWELVEDATA_API_KEY')
    url = "https://api.twelvedata.com/time_series?"
    url = url + f"symbol={ticker}&interval=1day&outputsize={n_days}&apikey={api_key}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from twelvedata: {e}")
        return None

    try:
        data = pd.DataFrame(response.json()['values'])
    except ValueError:
        print(f"Failed to parse data from twelvedata: {response.json()}")
        return None

    data['datetime'] = pd.to_datetime(data['datetime'])
    data.set_index('datetime', inplace=True)
    data = data.apply(pd.to_numeric)
    return data


def _get_last_quote(ticker):
    """
    Get the latest quote for a given ticker
    """
    api_key = os.environ.get('TWELVEDATA_API_KEY')
    url = f"https://api.twelvedata.com/quote?symbol={ticker}&apikey={api_key}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data from twelvedata: {e}")
        return None

    data = response.json()
    quote = {}
    try:
        quote['close'] = float(data['close'])
        quote['open'] = float(data['open'])
        quote['previous_close'] = float(data['previous_close'])
        quote['datetime'] = pd.to_datetime(data['datetime'])
    except ValueError:
        print(f"Failed to parse quote for {ticker}: {data['close']}")
        return None

    return quote


def get_vix_open():
    """
    Get the Open VIX price using twelvedata API
    Legacy:
        vix = yf.Ticker('^VIX')
        hist = vix.history(period="7d")
        return hist['Open'].iloc[-1], hist.index[-1]

    """
    quote = _get_last_quote('VIX')
    vix_open = quote['open']

    return vix_open, quote['datetime']


def get_otc_open():
    """
    Get the Open to Prev.Close change for SPX
    Legacy:
        spx = yf.Ticker('^SPX')
        hist = spx.history(period="7d")
        otc = (hist['Open']-hist['Close'].shift(1)) / hist['Close'].shift(1) * 100
        return otc.iloc[-1], otc.index[-1]
    """
    quote = _get_last_quote('SPX')
    otc = (quote['open'] - quote['previous_close']) / quote['previous_close'] * 100

    return otc, quote['datetime']

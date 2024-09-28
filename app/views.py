from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
import pandas as pd 
import pandas_ta as ta
import mplfinance as mpf
from datetime import datetime
from io import BytesIO
import base64
import requests

# Create your views here.
def fetch_stock_data(symbol):
    api_key = 'C1HODZSUTNBVXCID'
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    if 'Time Series (5min)' not in data:
        return None
    time_series = data['Time Series (5min)']
    stock_data = []
    for time, values in time_series.items():
        stock_data.append({
            'timestamp': datetime.strptime(time, '%Y-%m-%d %H:%M:%S'),
            'open': float(values['1. open']),
            'high': float(values['2. high']),
            'low': float(values['3. low']),
            'close': float(values['4. close']),
            'volume': int(values['5. volume'])
        })
    return stock_data

def plot_candlestick(data):
    if not data:
        return None
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)

    # Calculate Moving Averages
    df['SMA20'] = ta.sma(df['close'], length=20)
    df['SMA50'] = ta.sma(df['close'], length=50)

    # Calculate RSI
    df['RSI'] = ta.rsi(df['close'], length=14)

    # Calculate MACD
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_Signal'] = macd['MACDs_12_26_9']
    df['MACD_Hist'] = macd['MACDh_12_26_9']

    # Plotting
    mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
    s = mpf.make_mpf_style(marketcolors=mc)

    fig, axes = mpf.plot(
        df,
        type='candle',
        style=s,
        title='Stock Price with Technical Indicators',
        ylabel='Price',
        volume=True,
        mav=(20, 50),
        addplot=[
            mpf.make_addplot(df['SMA20'], color='blue'),
            mpf.make_addplot(df['SMA50'], color='red'),
            mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI'),
            mpf.make_addplot(df['MACD'], panel=3, color='blue', ylabel='MACD'),
            mpf.make_addplot(df['MACD_Signal'], panel=3, color='red'),
            mpf.make_addplot(df['MACD_Hist'], type='bar', panel=3, color='gray')
        ],
        returnfig=True,
        figsize=(14, 10)  # Increase graph size
    )

    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    image_png = buf.getvalue()
    buf.close()
    image_b64 = base64.b64encode(image_png).decode('utf-8')
    return image_b64
def stock_chart(request):
    symbol = request.GET.get('symbol', 'AAPL')  # Default to AAPL if no symbol provided
    stock_data = fetch_stock_data(symbol)
    chart = plot_candlestick(stock_data) if stock_data else None
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'chart': chart, 'error': 'Invalid stock symbol or data not available.' if not chart else ''})
    return render(request, 'stock_chart.html', {'chart': chart, 'symbol': symbol})
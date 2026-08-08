"""
Extract step of the ETL pipeline.

Responsible only for pulling raw stock data from Yahoo Finance (yfinance).
No cleaning or calculations happen here — that is done in transform.py.
"""

import yfinance as yf

def extract_live_stock(symbol):
    # Pulls today's intraday data in 5-minute candles.
    stock_data = yf.download(symbol, period="1d", interval="5m")

    if stock_data.empty:
        return stock_data

    stock_data = stock_data.reset_index()

    # yfinance uses its own column names; rename them to the names
    # used everywhere else in this project (OpenPrice, ClosePrice, etc.)
    stock_data.rename(columns={
        "Datetime": "Date",
        "Open": "OpenPrice",
        "High": "High",
        "Low": "Low",
        "Close": "ClosePrice"
    }, inplace=True)

    return stock_data


def extract_history_stock(symbol):
    # Pulls 5 years of daily (end-of-day) data.
    stock_data = yf.download(symbol, period="5y", interval="1d")

    if stock_data.empty:
        return stock_data

    stock_data = stock_data.reset_index()

    stock_data.rename(columns={
        "Open": "OpenPrice",
        "High": "High",
        "Low": "Low",
        "Close": "ClosePrice"
    }, inplace=True)

    return stock_data

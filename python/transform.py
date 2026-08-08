"""
Transform step of the ETL pipeline.

Cleans the raw stock data and adds the calculated columns
(20-day moving average and trend) used by the dashboard.
"""

import numpy as np
import pandas as pd

def transform_data(stock_data, keep_time=False):

    if stock_data is None or stock_data.empty:
        return stock_data

    # yfinance sometimes returns MultiIndex columns (e.g. when a ticker
    # list is passed). Flatten them so column names stay simple strings.

    if isinstance(stock_data.columns, pd.MultiIndex):
        stock_data.columns = stock_data.columns.get_level_values(0)

    stock_data["Date"] = pd.to_datetime(stock_data["Date"])

    # Historical (daily) data only needs the date, not the time.
    # Live (intraday) data keeps the time so candles plot correctly.
    if not keep_time:
        stock_data["Date"] = stock_data["Date"].dt.date

    numeric_columns = [
        "OpenPrice",
        "High",
        "Low",
        "ClosePrice",
        "Volume"
    ]

    for column in numeric_columns:
        stock_data[column] = pd.to_numeric(stock_data[column], errors="coerce")

    # Drop rows where any required value is missing so bad data never
    # reaches the database or the dashboard.
    stock_data.dropna(
        subset=[
            "Date",
            "OpenPrice",
            "High",
            "Low",
            "ClosePrice",
            "Volume"
        ],
        inplace=True
    )

    # 20-period moving average of the closing price.
    stock_data["MA_20"] = (
        stock_data["ClosePrice"]
        .rolling(window=20, min_periods=1)
        .mean()
        .round(2)
    )
    print(stock_data[["ClosePrice", "MA_20"]].tail())

    # Trend is simply whether the current price is above or below its
    # own moving average.
    stock_data["Trend"] = np.where(
        stock_data["ClosePrice"] > stock_data["MA_20"],
        "UP",
        "DOWN"
    )

    return stock_data

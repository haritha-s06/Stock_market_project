# Stock_market_project
[![Python](https://img.shields.io/badge/Python-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![SQL%20Server](https://img.shields.io/badge/Database-SQL%20Server-CC2927.svg)](https://www.microsoft.com/sql-server)
[![Pandas](https://img.shields.io/badge/Pandas-Data%20Processing-blue.svg)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Visualization-purple.svg)](https://plotly.com/)
[![yfinance](https://img.shields.io/badge/yfinance-Python%20Library-orange.svg)](https://github.com/ranaroussi/yfinance)

# Real-Time Stock Analytics Dashboard

## About This Project

I built a dashboard that pulls live and historical stock data for NSE-listed companies, cleans it up, stores it in SQL Server, and shows it on an interactive Streamlit dashboard — candlestick charts, a 20-day moving average trend, and a plain-English summary of how the stock is performing, generated purely from the data itself (no external AI or ML model involved).

The project follows a proper ETL structure — pull the data, clean and calculate on it, then load it into the database — with a dashboard sitting on top that reads from both the live source and the stored historical data.

---

## What It Does

- Fetches live intraday prices (5-minute candles) and 5 years of daily historical prices from Yahoo Finance
- Calculates a 20-day moving average and marks each point as an UP or DOWN trend
- Stores the cleaned historical data in a SQL Server database
- Shows a live-updating candlestick chart that refreshes automatically every 60 seconds while the market is open
- Falls back to the last available session's data automatically when the market is closed, so the dashboard doesn't just break on weekends/holidays
- Generates a 5-point "Market Summary" in plain English — price vs moving average, today's range, latest candle movement, 1-year growth, and last-30-days performance — calculated entirely from the data already on screen

---

## How It Works (Pipeline Flow)

```text
      Yahoo Finance (yfinance)
                │
                ▼
           extract.py
   pulls live + historical prices
                │
                ▼
          transform.py
  cleans data, adds MA_20 + Trend
                │
                ▼
            load.py
   saves historical data to SQL Server
                │
                ▼
             app.py
   Streamlit dashboard reads live +
        stored historical data
```

Live data is fetched, cleaned, and shown on the dashboard directly — it's never written to the database. Only historical data gets stored, since that's what needs to persist between runs.

---

## Tools & Libraries Used

| What | Used For |
|------|----------|
| Python | Core language for the whole pipeline and dashboard |
| yfinance | Pulling live and historical stock price data from Yahoo Finance |
| pandas / NumPy | Cleaning data and calculating the moving average / trend |
| SQL Server + SQLAlchemy | Storing historical stock data (connects via Windows Authentication) |
| Plotly | Rendering the live candlestick chart |
| Streamlit | The dashboard itself — layout, live refresh, buttons, tables |
| pytz | Handling IST market-hours logic (market open/close, live data cutoff) |

---

## Folder Layout

```text
stock_project/
│
├── main.py              → wires extract → transform → load together
├── app.py                → Streamlit dashboard
│
├── python/
│   ├── extract.py        → pulls live + historical data from yfinance
│   ├── transform.py      → cleans data, adds MA_20 and Trend columns
│   └── load.py            → saves historical data into SQL Server
│
├── sql/
│   └── stockdb_setup.sql → creates the StockDB database and stock_data table
│
└── README.md
```

## Running the Dashboard

```bash
streamlit run app.py
```

This opens the dashboard in browser, usually at:

```text
http://localhost:8501
```

Pick a stock from the sidebar and click **Run Analysis** to load historical data and start the live view.

---

## Trend Logic

The dashboard marks a stock UP or DOWN by comparing its current close price to its own 20-day moving average:

```python
if ClosePrice > MA_20:
    Trend = "UP"
else:
    Trend = "DOWN"
```

---

## Problems I Ran Into

**Yahoo Finance timestamps weren't in Indian time.**
Live data came back in UTC by default, so the candlestick chart didn't line up with actual NSE market hours. I fixed this by converting timestamps to IST (`Asia/Kolkata`) and filtering the live data to only the 9:15 AM–3:30 PM trading window.

**The dashboard broke when the market was closed.**
On weekends and holidays, there's no live intraday data to show. I added a fallback that builds a "live-like" view from the most recent stored historical session instead, so the dashboard still shows something useful instead of an empty chart.

**Inserting a pandas DataFrame directly into SQL Server didn't work well with plain pyodbc.**
I switched to SQLAlchemy's `to_sql()` method, which handles the DataFrame-to-SQL insert reliably without writing manual insert statements.

---

## What I Learned

- Building a proper ETL pipeline with separate extract/transform/load steps instead of one big script
- Working with time zones and market-hours logic correctly
- Connecting a Python app to SQL Server and inserting data reliably
- Building a live-refreshing dashboard with Streamlit
- Turning raw numeric data into a plain-English summary without using any external AI/ML service

---

## About Me

**Haritha S**

Python · Streamlit · SQL Server · yfinance

---

## License

Built for learning and portfolio purposes.

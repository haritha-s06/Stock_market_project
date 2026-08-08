import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import pytz

from main import run_pipeline

from python.extract import extract_live_stock
from python.transform import transform_data

# =====================================================
# PAGE SETUP
# =====================================================

st.set_page_config(layout="wide")

# =====================================================
# fetch + clean live data
# =====================================================
def fetch_live(symbol):
    raw = extract_live_stock(symbol)
    if raw is None or raw.empty:
        return None

    df = transform_data(raw, keep_time=True)

    df["Date"] = pd.to_datetime(df["Date"])
    if df["Date"].dt.tz is not None:
        df["Date"] = df["Date"].dt.tz_convert("Asia/Kolkata")
    df["Date"] = df["Date"].dt.tz_localize(None)

    ist   = pytz.timezone("Asia/Kolkata")
    now   = datetime.now(ist)
    today = now.date()
    start  = pd.to_datetime(f"{today} 09:15:00")
    end    = pd.to_datetime(f"{today} 15:30:00")
    cutoff = min(now.replace(tzinfo=None), end)

    df = df[(df["Date"] >= start) & (df["Date"] <= cutoff)]
    df = df.tail(100)

    return df if not df.empty else None

# =====================================================
# FALLBACK — build a "live-like" row from historical data
# Used on weekends/holidays when intraday data is unavailable.
# Returns a DataFrame with the same columns fetch_live() produces,
# built from the most recent row(s) of history_df.
# =====================================================

def fallback_from_history(history_df):
    if history_df is None or history_df.empty:
        return None

    hist = history_df.copy()
    hist["Date"] = pd.to_datetime(hist["Date"])
    hist = hist.sort_values("Date")

    # Recompute MA_20 in case it isn't present / needs refresh
    if "MA_20" not in hist.columns or hist["MA_20"].isna().all():
        hist["MA_20"] = hist["ClosePrice"].rolling(20).mean().round(2)

    # Use last 100 rows so downstream candlestick/tail logic still works
    return hist.tail(100)

# =====================================================
# Market Summary (no external API)
# Builds 5 bullet points purely from the data already
# available in the dashboard. Called only on button click.
# =====================================================
def summary(price, high, low, ma20, df_live, history_df):
    """
    Returns a list of 5 plain-English bullet point strings.
    Uses only the values already computed in the dashboard.
    No external API or ML model involved.
    """

    bullets = []

    # ── Bullet 1: Current Price vs MA20 ───────────────────────────────────
    diff_ma   = round(price - ma20, 2)
    pct_ma    = round((diff_ma / ma20) * 100, 2) if ma20 else 0
    direction = "above" if diff_ma >= 0 else "below"
    strength  = "indicating stronger recent performance" if diff_ma >= 0 \
                else "indicating softer recent performance"

    bullets.append(
        f"The current stock price is ₹{price} compared to the 20-period moving "
        f"average of ₹{ma20}. The price is ₹{abs(diff_ma)} ({abs(pct_ma)}%) "
        f"{direction} its recent average, {strength}."
    )

    # ── Bullet 2: Price vs Today's High and Low ───────────────────────────
    dist_high = round(high - price, 2)
    dist_low  = round(price - low,  2)
    day_range = round(high - low, 2)
    pct_range = round((dist_low / day_range) * 100, 2) if day_range else 0

    bullets.append(
        f"The stock is trading ₹{dist_high} below today's high of ₹{high} and "
        f"₹{dist_low} above today's low of ₹{low}, placing it at roughly "
        f"{pct_range}% of today's trading range and showing "
        f"{'relative strength' if pct_range >= 50 else 'relative weakness'} "
        f"within the session."
    )

    # ── Bullet 3: Latest Candlestick (Open vs Close) ──────────────────────
    if df_live is not None and not df_live.empty:
        latest     = df_live.iloc[-1]
        open_price = round(float(latest["OpenPrice"]), 2)
        close_prc  = round(float(latest["ClosePrice"]), 2)
        candle_chg = round(close_prc - open_price, 2)
        candle_pct = round((candle_chg / open_price) * 100, 2) if open_price else 0
        movement   = "gain" if candle_chg >= 0 else "loss"
        sentiment  = "positive price movement" if candle_chg >= 0 \
                     else "downward price movement"

        bullets.append(
            f"The latest candle opened at ₹{open_price} and closed at ₹{close_prc}, "
            f"resulting in a {movement} of ₹{abs(candle_chg)} ({abs(candle_pct)}%), "
            f"indicating {sentiment} during the most recent interval."
        )
    else:
        bullets.append(
            "Live candlestick data is not available for the current session; "
            "please check back during market hours."
        )

    # ── Bullet 4: One-Year Historical Growth ──────────────────────────────
    if history_df is not None and not history_df.empty:
        hist          = history_df.copy()
        hist["Date"]  = pd.to_datetime(hist["Date"])
        hist          = hist.sort_values("Date")
        year_old      = round(float(hist.iloc[0]["ClosePrice"]),  2)
        year_new      = round(float(hist.iloc[-1]["ClosePrice"]), 2)
        yr_change     = round(year_new - year_old, 2)
        yr_pct        = round((yr_change / year_old) * 100, 2) if year_old else 0
        yr_direction  = "increased" if yr_change >= 0 else "decreased"

        bullets.append(
            f"Based on historical performance, the stock {yr_direction} from "
            f"₹{year_old} to ₹{year_new} over the tracked period, representing "
            f"approximately {abs(yr_pct)}% {'growth' if yr_change >= 0 else 'decline'} "
            f"in closing price."
        )
    else:
        bullets.append(
            "Long-term historical data is not yet available; "
            "click Run Analysis to load it."
        )

    # ── Bullet 5: Last 30 Days Performance ────────────────────────────────
    if history_df is not None and not history_df.empty:
        last30     = history_df.tail(30)
        avg_close  = round(float(last30["ClosePrice"].mean()), 2)
        start_30   = round(float(last30.iloc[0]["ClosePrice"]),  2)
        end_30     = round(float(last30.iloc[-1]["ClosePrice"]), 2)
        chg_30     = round(end_30 - start_30, 2)
        pct_30     = round((chg_30 / start_30) * 100, 2) if start_30 else 0
        dir_30     = "gained" if chg_30 >= 0 else "lost"

        bullets.append(
            f"Over the last 30 trading days, the stock maintained an average "
            f"closing price of ₹{avg_close} and {dir_30} ₹{abs(chg_30)} "
            f"({abs(pct_30)}%) from ₹{start_30} to ₹{end_30}, indicating "
            f"{'stable to positive' if chg_30 >= 0 else 'mild downward'} "
            f"market participation over the recent period."
        )
    else:
        bullets.append(
            "Historical data for the last 30 days is not yet loaded; "
            "click Run Analysis to populate this section."
        )

    return bullets

# =====================================================
# TITLE + "Summary" BUTTON
# =====================================================
st.title("Real-Time Stock Analytics Dashboard")

# Clicking the button sets a flag in session_state; the summary renders
# immediately below the button (before KPIs/candlestick) only when True.
if st.button("Summary"):
    st.session_state["summary"] = True

# ── AI Market Summary — rendered right below the button ───────────────────
if st.session_state.get("summary", False):

    st.markdown("---")
    st.subheader("Market Summary")

    if "analysis_stock" in st.session_state:
        summary_stock    = st.session_state["analysis_stock"]
        summary_history  = st.session_state.get("history_df")
        summary_live     = fetch_live(summary_stock)
        if summary_live is None:
            summary_live = fallback_from_history(summary_history)

        if summary_live is not None and not summary_live.empty:
            latest_row    = summary_live.iloc[-1]
            latest_price  = round(float(latest_row["ClosePrice"]), 2)
            latest_high   = round(float(latest_row["High"]),       2)
            latest_low    = round(float(latest_row["Low"]),        2)
            latest_ma20   = round(float(summary_live["MA_20"].iloc[-1]), 2)

            summary_bullets = summary(
                price      = latest_price,
                high       = latest_high,
                low        = latest_low,
                ma20       = latest_ma20,
                df_live    = summary_live,
                history_df = summary_history,
            )

            for bullet in summary_bullets:
                st.markdown(f"• {bullet}")

        else:
            st.warning(
                "No data available yet. Click **Run Analysis** to load historical data."
            )
    else:
        st.warning("Click **Run Analysis** first to load data for the summary.")

    # Allow user to hide the summary again
    if st.button("Hide Summary"):
        st.session_state["show_ai_summary"] = False
        st.rerun()

    st.markdown("---")

# =====================================================
# STOCK SELECTION  (sidebar — never refreshed)
# =====================================================

stock = st.sidebar.selectbox(
    "Select Stock",
    [
        # Large Cap
        'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS',
        'ICICIBANK.NS', 'LT.NS', 'SBIN.NS', 'KOTAKBANK.NS',
        'ITC.NS', 'BHARTIARTL.NS', 'ASIANPAINT.NS',
        'MARUTI.NS', 'WIPRO.NS', 'HCLTECH.NS', 'AXISBANK.NS',
        'BAJFINANCE.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'NESTLEIND.NS',
        'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'JSWSTEEL.NS',
        'TATAMOTORS.NS', 'TATASTEEL.NS', 'ADANIENT.NS', 'ADANIPORTS.NS',
        'SUNPHARMA.NS', 'DRREDDY.NS', 'CIPLA.NS', 'DIVISLAB.NS',
        'BAJAJFINSV.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS',
        'INDUSINDBK.NS', 'FEDERALBNK.NS', 'GRASIM.NS', 'HINDALCO.NS',
        'COALINDIA.NS', 'BPCL.NS', 'IOC.NS', 'BRITANNIA.NS',
        'PIDILITIND.NS', 'HAVELLS.NS', 'VOLTAS.NS', 'MUTHOOTFIN.NS',
        'LUPIN.NS', 'BIOCON.NS'
    ]
)

# ==========================
# MARKET STATUS
# ==========================

def get_market_status():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    market_open  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_closed = now.weekday() >= 5 or not (market_open <= now <= market_close)
    interval = None if is_closed else 60
    return is_closed, interval

is_closed, refresh_interval = get_market_status()

if is_closed:
    st.markdown("<h3 style='color:red;'>Market CLOSED</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 style='color:green;'>Market OPEN</h3>", unsafe_allow_html=True)


# =====================================================
# FRAGMENT — auto-refreshes every 60 s
# =====================================================

@st.fragment(run_every=refresh_interval)
def live_section(symbol):

    df = fetch_live(symbol)
    using_fallback = False

    if df is None:
        # Market closed / no intraday data — fall back to last available
        # historical session so KPIs and chart still render on weekends.
        history_df = st.session_state.get("history_df")
        df = fallback_from_history(history_df)
        using_fallback = True

    if df is None:
        st.warning("No data available yet. Click **Run Analysis** to load historical data.")
        return

    if using_fallback:
        st.info(
            "Market is closed — showing the most recent available trading session."
        )

    # ── Latest row values ──────────────────────────────────────────────────
    latest   = df.iloc[-1]
    price    = float(latest["ClosePrice"])
    high     = float(latest["High"])
    low      = float(latest["Low"])
    trend    = "UP" if latest["ClosePrice"] > latest["OpenPrice"] else "DOWN"

    # ── KPI cards ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Price",  round(price, 2))
    c2.metric("High",   round(high,  2))
    c3.metric("Low",    round(low,   2))
    c4.metric("Trend",  trend)

    # ── Live candlestick chart ─────────────────────────────────────────────
    st.subheader("Live Candlestick Chart")

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["OpenPrice"],
            high=df["High"],
            low=df["Low"],
            close=df["ClosePrice"],
            name="Candlestick"
        )
    )
    fig.update_layout(
        height=700,
        xaxis_rangeslider_visible=False,
        yaxis=dict(side="right")
    )
    st.plotly_chart(fig,width = 'stretch')

    # ── Refresh timestamp ──────────────────────────────────────────────────
    if using_fallback:
        st.caption(
            f"Showing last available session data as of "
            f"{pd.to_datetime(latest['Date']).strftime('%Y-%m-%d')}."
        )
    else:
        st.caption(
            f"Auto-refreshed at: "
            f"{datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S')} IST"
        )

# =====================================================
# STATIC SECTION — rendered once, never auto-refreshed
# =====================================================
def render_static(history_df):

    st.subheader("Yearly Trend")
    if history_df is not None and not history_df.empty:
        history_df["Year"] = pd.to_datetime(history_df["Date"]).dt.year
        yearly = history_df.groupby("Year")["ClosePrice"].last().round(2)
        st.line_chart(yearly)
    else:
        st.warning("Yearly data unavailable.")

    st.subheader("Last 30 Days Historical Data")
    if history_df is not None and not history_df.empty:
        display = history_df.copy()
        display["Volume"] = display["Volume"].apply(
            lambda x: f"{int(x):,}" if pd.notnull(x) else x
        )
        display["High"] = display["High"].apply(
            lambda x: f"{float(x):.2f}" if pd.notnull(x) else x
        )
        display["Low"] = display["Low"].apply(
            lambda x: f"{float(x):.2f}" if pd.notnull(x) else x
        )
        display["ClosePrice"] = display["ClosePrice"].apply(
            lambda x: f"{float(x):.2f}" if pd.notnull(x) else x
        )
        last_30 = display.tail(30)[["Date", "High", "Low", "ClosePrice", "Volume"]]
        st.dataframe(last_30, use_container_width=True)
    else:
        st.warning("No historical data available.")

# =====================================================
# MAIN FLOW
# =====================================================
if st.sidebar.button("Run Analysis"):
    try:
        with st.spinner("Running pipeline..."):
            _, history_df = run_pipeline(stock)

        st.session_state["history_df"]      = history_df
        st.session_state["analysis_stock"]  = stock
        st.success("Analysis complete.")

    except Exception as e:
        st.error("Pipeline failed.")
        st.caption(f"Debug: {e}")

if "analysis_stock" in st.session_state:

    if st.session_state["analysis_stock"] != stock:
        st.info(
            f"Live data showing **{stock}** | "
            f"Historical data is for **{st.session_state['analysis_stock']}**. "
            "Click **Run Analysis** to sync both."
        )

    live_section(stock)                                  # ← auto-refreshes every 60 s

    render_static(st.session_state["history_df"])

else:
    st.info("Select a stock and click **Run Analysis** to start.")
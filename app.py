```python
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from io import StringIO

# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(
    page_title="Nifty 100 HA Bollinger Alert",
    page_icon="📊",
    layout="wide",
)

IST = ZoneInfo("Asia/Kolkata")

# =========================================================
# SETTINGS
# =========================================================

BB_LENGTH = 40
BB_MULTIPLIER = 4.0
WATCH_DAYS = 2

WATCH_FILE = "watchlist.json"

NSE_URL = (
    "https://www.nseindia.com/api/"
    "equity-stockIndices?index=NIFTY%20100"
)

# NSE Indices official Nifty 100 constituent CSV
NIFTY100_CSV_URL = (
    "https://www.niftyindices.com/"
    "IndexConstituent/ind_nifty100list.csv"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.main-title {
    font-size: 28px;
    font-weight: 800;
    margin-bottom: 2px;
}

.sub-title {
    color: #777;
    font-size: 14px;
    margin-bottom: 14px;
}

.metric-card {
    border-radius: 10px;
    padding: 12px;
    border: 1px solid rgba(128,128,128,.20);
    background: rgba(128,128,128,.05);
    text-align: center;
}

.small-note {
    color: #777;
    font-size: 12px;
}

</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE
# =========================================================

if "scanner_on" not in st.session_state:
    st.session_state.scanner_on = True

if "last_scan_date" not in st.session_state:
    st.session_state.last_scan_date = None

if "last_scan_time" not in st.session_state:
    st.session_state.last_scan_time = None


# =========================================================
# WATCHLIST
# =========================================================

def load_watchlist():

    if not os.path.exists(WATCH_FILE):
        return []

    try:

        with open(
            WATCH_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if isinstance(data, list):
            return data

    except Exception:
        pass

    return []


def save_watchlist(data):

    try:

        with open(
            WATCH_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        return True

    except Exception:
        return False


# =========================================================
# NIFTY 100
# =========================================================

@st.cache_data(
    ttl=21600,
    show_spinner=False
)
def get_nifty100_symbols():

    # -----------------------------------------------------
    # METHOD 1: NSE API
    # -----------------------------------------------------

    try:

        session = requests.Session()

        session.get(
            "https://www.nseindia.com",
            headers=HEADERS,
            timeout=15
        )

        response = session.get(
            NSE_URL,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        records = data.get(
            "data",
            []
        )

        symbols = []

        for row in records:

            symbol = str(
                row.get(
                    "symbol",
                    ""
                )
            ).strip().upper()

            if symbol:
                symbols.append(symbol)

        symbols = list(
            dict.fromkeys(symbols)
        )

        if len(symbols) >= 95:

            return symbols[:100]

    except Exception:
        pass


    # -----------------------------------------------------
    # METHOD 2: NSE INDICES OFFICIAL CSV
    # -----------------------------------------------------

    try:

        response = requests.get(
            NIFTY100_CSV_URL,
            headers=HEADERS,
            timeout=30
        )

        response.raise_for_status()

        df = pd.read_csv(
            StringIO(
                response.text
            )
        )

        # Try normal Symbol column
        symbol_col = None

        for col in df.columns:

            clean = str(
                col
            ).strip().upper()

            if clean in (
                "SYMBOL",
                "SYMBOLS"
            ):

                symbol_col = col
                break

        if symbol_col is not None:

            symbols = (
                df[symbol_col]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
                .tolist()
            )

            symbols = list(
                dict.fromkeys(symbols)
            )

            if len(symbols) >= 95:

                return symbols[:100]

    except Exception:
        pass


    # -----------------------------------------------------
    # METHOD 3: FALLBACK
    #
    # This is deliberately NOT limited to 55.
    # It contains a broad large-cap universe so the app
    # continues to work if NSE blocks both sources.
    # -----------------------------------------------------

    fallback = [
        "ADANIENT",
        "ADANIPORTS",
        "APOLLOHOSP",
        "ASIANPAINT",
        "AXISBANK",
        "BAJAJ-AUTO",
        "BAJFINANCE",
        "BAJAJFINSV",
        "BEL",
        "BHARTIARTL",
        "BPCL",
        "BRITANNIA",
        "CIPLA",
        "COALINDIA",
        "DRREDDY",
        "EICHERMOT",
        "ETERNAL",
        "GRASIM",
        "HCLTECH",
        "HDFCBANK",
        "HDFCLIFE",
        "HEROMOTOCO",
        "HINDALCO",
        "HINDUNILVR",
        "ICICIBANK",
        "INDIGO",
        "INDUSINDBK",
        "INFY",
        "ITC",
        "JIOFIN",
        "JSWSTEEL",
        "KOTAKBANK",
        "LT",
        "M&M",
        "MARUTI",
        "MAXHEALTH",
        "NESTLEIND",
        "NTPC",
        "ONGC",
        "POWERGRID",
        "RELIANCE",
        "SBILIFE",
        "SBIN",
        "SHRIRAMFIN",
        "SUNPHARMA",
        "TATACONSUM",
        "TATAMOTORS",
        "TATASTEEL",
        "TCS",
        "TECHM",
        "TITAN",
        "TRENT",
        "ULTRACEMCO",
        "WIPRO",
        "ABB",
        "ADANIPOWER",
        "AMBUJACEM",
        "AUROPHARMA",
        "BANKBARODA",
        "BANDHANBNK",
        "BERGEPAINT",
        "BIOCON",
        "BOSCHLTD",
        "CANBK",
        "CHOLAFIN",
        "COLPAL",
        "CUMMINSIND",
        "DABUR",
        "DIVISLAB",
        "DLF",
        "GAIL",
        "GODREJCP",
        "GODREJPROP",
        "HAL",
        "ICICIGI",
        "ICICIPRULI",
        "INDUSTOWER",
        "IRCTC",
        "IRFC",
        "JINDALSTEL",
        "LICI",
        "LICHSGFIN",
        "LODHA",
        "LUPIN",
        "MANKIND",
        "MARICO",
        "MOTHERSON",
        "MPHASIS",
        "MUTHOOTFIN",
        "NAUKRI",
        "NHPC",
        "NMDC",
        "OFSS",
        "PFC",
        "PIDILITIND",
        "PNB",
        "POLYCAB",
        "RECLTD",
        "SAIL",
        "SIEMENS",
        "SRF",
        "TORNTPHARM",
        "TVSMOTOR",
        "UNOMINDA",
        "UPL",
        "VEDL",
        "YESBANK",
        "ZYDUSLIFE",
    ]

    return list(
        dict.fromkeys(
            fallback
        )
    )


# =========================================================
# YAHOO SYMBOL
# =========================================================

def yf_symbol(symbol):

    return f"{symbol}.NS"


# =========================================================
# DAILY DATA
# =========================================================

@st.cache_data(
    ttl=1800,
    show_spinner=False
)
def download_daily(symbol):

    try:

        ticker = yf.Ticker(
            yf_symbol(symbol)
        )

        df = ticker.history(
            period="15mo",
            interval="1d",
            auto_adjust=False,
            actions=False
        )

        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        if isinstance(
            df.columns,
            pd.MultiIndex
        ):

            df.columns = [
                c[0]
                for c in df.columns
            ]

        required = [
            "Open",
            "High",
            "Low",
            "Close"
        ]

        for col in required:

            if col not in df.columns:
                return pd.DataFrame()

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        df = df.dropna(
            subset=required
        )

        return df

    except Exception:

        return pd.DataFrame()


# =========================================================
# HEIKIN ASHI
# =========================================================

def heikin_ashi(df):

    if df.empty:
        return pd.DataFrame()

    out = pd.DataFrame(
        index=df.index
    )

    o = df["Open"].astype(float)
    h = df["High"].astype(float)
    l = df["Low"].astype(float)
    c = df["Close"].astype(float)

    ha_close = (
        o + h + l + c
    ) / 4.0

    ha_open = np.zeros(
        len(df),
        dtype=float
    )

    ha_open[0] = (
        o.iloc[0]
        + c.iloc[0]
    ) / 2.0

    for i in range(
        1,
        len(df)
    ):

        ha_open[i] = (
            ha_open[i - 1]
            + ha_close.iloc[i - 1]
        ) / 2.0

    ha_high = pd.concat(
        [
            pd.Series(
                ha_open,
                index=df.index
            ),
```

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import json
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(
    page_title="Nifty 100 HA Bollinger Alert",
    page_icon="📊",
    layout="wide",
)

# =========================================================
# SETTINGS
# =========================================================

BB_LENGTH = 40
BB_MULTIPLIER = 4.0
WATCH_DAYS = 2

WATCH_FILE = "watchlist.json"

NSE_URL = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20100"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
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

.signal-box {
    padding: 12px;
    border-radius: 10px;
    border: 1px solid rgba(128,128,128,.25);
    background: rgba(128,128,128,.06);
    margin-bottom: 10px;
}

.green-box {
    border-left: 5px solid #16a34a;
}

.yellow-box {
    border-left: 5px solid #eab308;
}

.red-box {
    border-left: 5px solid #dc2626;
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
# WATCHLIST FILE
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
# NIFTY 100 LIST
# =========================================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_nifty100_symbols():

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

        if len(symbols) >= 80:
            return symbols

    except Exception:
        pass

    # Fallback list
    return [
        "ADANIENT",
        "ADANIPORTS",
        "ADANIPOWER",
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
    ]


# =========================================================
# YFINANCE SYMBOL
# =========================================================

def yf_symbol(symbol):

    return f"{symbol}.NS"


# =========================================================
# DOWNLOAD DAILY DATA
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

        if df.empty:
            return pd.DataFrame()

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
            ha_close,
            h
        ],
        axis=1
    ).max(axis=1)

    ha_low = pd.concat(
        [
            pd.Series(
                ha_open,
                index=df.index
            ),
            ha_close,
            l
        ],
        axis=1
    ).min(axis=1)

    out["HA_Open"] = ha_open
    out["HA_High"] = ha_high
    out["HA_Low"] = ha_low
    out["HA_Close"] = ha_close

    return out


# =========================================================
# BOLLINGER
# =========================================================

def add_bollinger(ha):

    if ha.empty:
        return ha

    out = ha.copy()

    out["Middle"] = (
        out["HA_Close"]
        .rolling(
            BB_LENGTH
        )
        .mean()
    )

    out["Std"] = (
        out["HA_Close"]
        .rolling(
            BB_LENGTH
        )
        .std(
            ddof=0
        )
    )

    out["Upper"] = (
        out["Middle"]
        + (
            BB_MULTIPLIER
            * out["Std"]
        )
    )

    out["Lower"] = (
        out["Middle"]
        - (
            BB_MULTIPLIER
            * out["Std"]
        )
    )

    return out


# =========================================================
# CROSS CONDITION
# =========================================================

def find_cross_signal(df):

    if df.empty:
        return None

    ha = heikin_ashi(df)

    if ha.empty:
        return None

    bb = add_bollinger(
        ha
    )

    if len(bb) < BB_LENGTH + 2:
        return None

    prev = bb.iloc[-2]
    curr = bb.iloc[-1]

    if pd.isna(
        prev["Middle"]
    ):
        return None

    if pd.isna(
        curr["Middle"]
    ):
        return None

    previous_below = (
        float(prev["HA_Close"])
        < float(prev["Middle"])
    )

    current_above = (
        float(curr["HA_Close"])
        > float(curr["Middle"])
    )

    if not (
        previous_below
        and current_above
    ):
        return None

    signal_date = (
        pd.Timestamp(
            bb.index[-1]
        ).date()
    )

    trigger_high = float(
        df["High"].iloc[-1]
    )

    ha_high = float(
        curr["HA_High"]
    )

    ha_close = float(
        curr["HA_Close"]
    )

    middle = float(
        curr["Middle"]
    )

    return {
        "signal_date": str(
            signal_date
        ),
        "trigger_high": trigger_high,
        "ha_high": ha_high,
        "ha_close": ha_close,
        "middle": middle,
    }


# =========================================================
# CHECK ENTRY
# =========================================================

def check_entry(
    symbol,
    trigger_high,
    start_date
):

    df = download_daily(
        symbol
    )

    if df.empty:
        return None

    data = df.copy()

    data.index = pd.to_datetime(
        data.index
    )

    try:

        data = data[
            data.index.date
            > start_date
        ]

    except Exception:
        return None

    if data.empty:
        return None

    data = data.head(
        WATCH_DAYS
    )

    for idx, row in data.iterrows():

        high = float(
            row["High"]
        )

        if high > float(
            trigger_high
        ):

            entry_date = (
                pd.Timestamp(
                    idx
                ).date()
            )

            return {
                "entry_date": str(
                    entry_date
                ),
                "entry_time": "09:15-15:30",
                "entry_price": float(
                    trigger_high
                ),
            }

    return None


# =========================================================
# SCAN ONE SYMBOL
# =========================================================

def scan_symbol(symbol):

    df = download_daily(
        symbol
    )

    if df.empty:
        return None

    signal = find_cross_signal(
        df
    )

    if signal is None:
        return None

    return {
        "Symbol": symbol,
        "Signal Date": signal[
            "signal_date"
        ],
        "Trigger High": signal[
            "trigger_high"
        ],
        "HA Close": signal[
            "ha_close"
        ],
        "Middle": signal[
            "middle"
        ],
        "Status": "WATCHING",
        "Entry Date": "",
        "Entry Time": "",
        "Entry Price": "",
        "Days Left": WATCH_DAYS,
    }


# =========================================================
# DATE HELPERS
# =========================================================

def trading_days_after(
    signal_date,
    days=2
):

    try:

        start = pd.Timestamp(
            signal_date
        )

        end = start + pd.Timedelta(
            days=7
        )

        weekdays = pd.date_range(
            start=start + pd.Timedelta(days=1),
            end=end,
            freq="B"
        )

        return [
            str(x.date())
            for x in weekdays[:days]
        ]

    except Exception:
        return []


def days_left(
    signal_date
):

    dates = trading_days_after(
        signal_date,
        WATCH_DAYS
    )

    today = datetime.now(
        IST
    ).date()

    remaining = 0

    for d in dates:

        try:

            if pd.Timestamp(
                d
            ).date() >= today:

                remaining += 1

        except Exception:
            pass

    return remaining


# =========================================================
# UPDATE EXISTING WATCHLIST
# =========================================================

def update_watchlist(
    watchlist
):

    changed = False

    active = []

    for item in watchlist:

        symbol = item.get(
            "Symbol",
            ""
        )

        signal_date_text = item.get(
            "Signal Date",
            ""
        )

        trigger = item.get(
            "Trigger High"
        )

        status = item.get(
            "Status",
            "WATCHING"
        )

        if not symbol:
            continue

        if status == "TRIGGERED":
            active.append(item)
            continue

        if status == "EXPIRED":
            active.append(item)
            continue

        try:

            signal_date = pd.Timestamp(
                signal_date_text
            ).date()

        except Exception:

            active.append(item)
            continue

        watch_dates = trading_days_after(
            signal_date,
            WATCH_DAYS
        )

        today = datetime.now(
            IST
        ).date()

        # Future / current watch period
        if today not in [
            pd.Timestamp(x).date()
            for x in watch_dates
        ]:

            if today > pd.Timestamp(
                watch_dates[-1]
            ).date():

                item["Status"] = "EXPIRED"
                item["Days Left"] = 0
                changed = True

            active.append(item)
            continue

        entry = check_entry(
            symbol,
            float(trigger),
            signal_date
        )

        if entry:

            item["Status"] = "TRIGGERED"

            item["Entry Date"] = (
                entry["entry_date"]
            )

            item["Entry Time"] = (
                entry["entry_time"]
            )

            item["Entry Price"] = (
                entry["entry_price"]
            )

            item["Days Left"] = 0

            changed = True

        else:

            left = days_left(
                signal_date
            )

            if item.get(
                "Days Left"
            ) != left:

                item["Days Left"] = left
                changed = True

        active.append(item)

    return active, changed


# =========================================================
# ADD NEW SIGNALS
# =========================================================

def add_new_signals(
    watchlist,
    symbols
):

    existing_keys = set()

    for item in watchlist:

        existing_keys.add(
            (
                item.get(
                    "Symbol"
                ),
                item.get(
                    "Signal Date"
                )
            )
        )

    today = datetime.now(
        IST
    ).date()

    added = 0

    progress = st.progress(
        0
    )

    total = len(
        symbols
    )

    for i, symbol in enumerate(
        symbols
    ):

        signal = scan_symbol(
            symbol
        )

        if signal:

            key = (
                signal["Symbol"],
                signal["Signal Date"]
            )

            if key not in existing_keys:

                watchlist.append(
                    signal
                )

                existing_keys.add(
                    key
                )

                added += 1

        progress.progress(
            (i + 1) / max(
                total,
                1
            )
        )

    progress.empty()

    return watchlist, added


# =========================================================
# MARKET STATUS
# =========================================================

def is_market_time():

    now = datetime.now(
        IST
    )

    if now.weekday() >= 5:
        return False

    current = now.time()

    start = datetime.strptime(
        "09:00",
        "%H:%M"
    ).time()

    end = datetime.strptime(
        "15:30",
        "%H:%M"
    ).time()

    return (
        start <= current <= end
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    '📊 Nifty 100 Heikin Ashi Bollinger Alert'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'NSE data • Heikin Ashi • 1 Day • Bollinger 40 / 4 • '
    '2-Day High Break Watch'
    '</div>',
    unsafe_allow_html=True
)

# =========================================================
# CONTROL
# =========================================================

c1, c2, c3, c4 = st.columns(
    4
)

with c1:

    if st.session_state.scanner_on:

        if st.button(
            "🟢 Scanner ON",
            use_container_width=True
        ):

            st.session_state.scanner_on = False
            st.rerun()

    else:

        if st.button(
            "🔴 Scanner OFF",
            use_container_width=True
        ):

            st.session_state.scanner_on = True
            st.rerun()

with c2:

    st.metric(
        "Universe",
        "Nifty 100"
    )

with c3:

    st.metric(
        "Bollinger",
        "40 / 4"
    )

with c4:

    st.metric(
        "Watch",
        "2 Days"
    )

st.caption(
    "Scanner ON hone par signal scan/update hoga. "
    "OFF hone par automatic scan nahi chalega."
)

# =========================================================
# INFO
# =========================================================

st.info(
    "Signal rule: पिछली Heikin Ashi candle ka Close "
    "Middle Band se neeche ho aur current Heikin Ashi candle "
    "Middle Band ke upar close ho. Signal candle ka NORMAL "
    "candle High BUY Trigger hai."
)

# =========================================================
# LOAD WATCHLIST
# =========================================================

watchlist = load_watchlist()

# =========================================================
# UPDATE EXISTING WATCHLIST
# =========================================================

if st.session_state.scanner_on:

    watchlist, changed = update_watchlist(
        watchlist
    )

    if changed:
        save_watchlist(
            watchlist
        )

# =========================================================
# DAILY SCAN
# =========================================================

now = datetime.now(
    IST
)

today = now.date()

market_open_window = is_market_time()

scan_allowed = (
    st.session_state.scanner_on
    and (
        st.session_state.last_scan_date
        != today
    )
)

if scan_allowed:

    st.subheader(
        "🔎 Daily Nifty 100 Scan"
    )

    symbols = get_nifty100_symbols()

    st.write(
        f"Nifty 100 symbols loaded: "
        f"{len(symbols)}"
    )

    # Scan once per app session/day
    watchlist, added = add_new_signals(
        watchlist,
        symbols
    )

    save_watchlist(
        watchlist
    )

    st.session_state.last_scan_date = today
    st.session_state.last_scan_time = now.strftime(
        "%H:%M:%S"
    )

    if added:

        st.success(
            f"{added} new signal(s) WATCHLIST me add hue."
        )

    else:

        st.info(
            "Aaj koi naya Heikin Ashi Bollinger cross nahi mila."
        )

# =========================================================
# MANUAL SCAN
# =========================================================

if st.button(
    "🔄 Manual Scan Now",
    use_container_width=True
):

    symbols = get_nifty100_symbols()

    with st.spinner(
        "Nifty 100 scan ho raha hai..."
    ):

        watchlist, added = add_new_signals(
            watchlist,
            symbols
        )

        watchlist, changed = update_watchlist(
            watchlist
        )

        save_watchlist(
            watchlist
        )

    st.session_state.last_scan_date = today
    st.session_state.last_scan_time = now.strftime(
        "%H:%M:%S"
    )

    if added:

        st.success(
            f"{added} new signal(s) mile."
        )

    else:

        st.info(
            "Koi naya signal nahi mila."
        )

    st.rerun()

# =========================================================
# STATUS
# =========================================================

st.markdown(
    "---"
)

status_col1, status_col2, status_col3 = st.columns(
    3
)

with status_col1:

    if st.session_state.scanner_on:

        st.success(
            "Scanner: ON"
        )

    else:

        st.error(
            "Scanner: OFF"
        )

with status_col2:

    st.write(
        f"Last scan: "
        f"{st.session_state.last_scan_time or '--'}"
    )

with status_col3:

    st.write(
        f"Market window: "
        f"{'09:00–15:30' if market_open_window else 'Closed'}"
    )

# =========================================================
# WATCHLIST TABLE
# =========================================================

st.subheader(
    "👀 Watchlist"
)

if not watchlist:

    st.info(
        "Abhi koi share WATCHLIST me nahi hai. "
        "Signal milne par yahan automatically aayega."
    )

else:

    rows = []

    for item in watchlist:

        rows.append(
            {
                "Share": item.get(
                    "Symbol",
                    ""
                ),
                "Signal Date": item.get(
                    "Signal Date",
                    ""
                ),
                "Trigger High": item.get(
                    "Trigger High",
                    ""
                ),
                "HA Close": item.get(
                    "HA Close",
                    ""
                ),
                "Middle": item.get(
                    "Middle",
                    ""
                ),
                "Status": item.get(
                    "Status",
                    ""
                ),
                "Days Left": item.get(
                    "Days Left",
                    ""
                ),
                "Entry Date": item.get(
                    "Entry Date",
                    ""
                ),
                "Entry Time": item.get(
                    "Entry Time",
                    ""
                ),
                "Entry Price": item.get(
                    "Entry Price",
                    ""
                ),
            }
        )

    table = pd.DataFrame(
        rows
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True
    )

# =========================================================
# SIGNAL DETAILS
# =========================================================

watch_count = sum(
    1
    for x in watchlist
    if x.get("Status") == "WATCHING"
)

triggered_count = sum(
    1
    for x in watchlist
    if x.get("Status") == "TRIGGERED"
)

expired_count = sum(
    1
    for x in watchlist
    if x.get("Status") == "EXPIRED"
)

a, b, c = st.columns(
    3
)

with a:

    st.metric(
        "Currently Watching",
        watch_count
    )

with b:

    st.metric(
        "BUY Trigger Hit",
        triggered_count
    )

with c:

    st.metric(
        "Expired",
        expired_count
    )

# =========================================================
# RULES
# =========================================================

with st.expander(
    "📘 Scanner Rules"
):

    st.write(
        f"""
1. Universe: **Nifty 100**
2. Timeframe: **1 Day**
3. Candle: **Heikin Ashi**
4. Bollinger Length: **{BB_LENGTH}**
5. Multiplier: **{BB_MULTIPLIER}**
6. Previous HA Close < Previous Middle Band
7. Current HA Close > Current Middle Band
8. Cross candle ka **NORMAL candle High** BUY Trigger hai.
9. Trigger ko signal ke baad **2 trading days** tak watch kiya jayega.
10. Agar High cross hota hai to **Entry Date, Time aur Entry Price** save hoga.
11. 2 trading days me trigger nahi hua to status **EXPIRED**.
12. Dhan API/order ka koi use nahi hai.
        """
    )

# =========================================================
# REFRESH
# =========================================================

if st.session_state.scanner_on:

    st.caption(
        "Scanner ON hai. App ko refresh/reload karne par "
        "saved watchlist dobara load hogi."
    )

```python
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="Nifty 100 HA Bollinger Alert",
    page_icon="📈",
    layout="wide",
)

IST = ZoneInfo("Asia/Kolkata")

WATCH_FILE = "watchlist.json"

BB_LENGTH = 40
BB_MULTIPLIER = 4

WATCH_DAYS = 2


# =========================================================
# NIFTY 100
# =========================================================

NIFTY100 = [
    "RELIANCE.NS",
    "HDFCBANK.NS",
    "BHARTIARTL.NS",
    "TCS.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "INFY.NS",
    "LICI.NS",
    "HINDUNILVR.NS",
    "ITC.NS",
    "LT.NS",
    "BAJFINANCE.NS",
    "HCLTECH.NS",
    "MARUTI.NS",
    "KOTAKBANK.NS",
    "M&M.NS",
    "SUNPHARMA.NS",
    "AXISBANK.NS",
    "ULTRACEMCO.NS",
    "NTPC.NS",
    "TITAN.NS",
    "ADANIENT.NS",
    "ONGC.NS",
    "ADANIPORTS.NS",
    "WIPRO.NS",
    "POWERGRID.NS",
    "COALINDIA.NS",
    "NESTLEIND.NS",
    "BAJAJFINSV.NS",
    "JSWSTEEL.NS",
    "TATASTEEL.NS",
    "HINDALCO.NS",
    "ADANIPOWER.NS",
    "GRASIM.NS",
    "TECHM.NS",
    "INDUSINDBK.NS",
    "HDFCLIFE.NS",
    "SBILIFE.NS",
    "DRREDDY.NS",
    "CIPLA.NS",
    "TATAMOTORS.NS",
    "EICHERMOT.NS",
    "HEROMOTOCO.NS",
    "BAJAJ-AUTO.NS",
    "TVSMOTOR.NS",
    "ASIANPAINT.NS",
    "DMART.NS",
    "TATACONSUM.NS",
    "BRITANNIA.NS",
    "MARICO.NS",
    "DABUR.NS",
    "BEL.NS",
    "HAL.NS",
    "BHEL.NS",
    "TRENT.NS",
    "ZOMATO.NS",
    "JIOFIN.NS",
    "SHRIRAMFIN.NS",
    "CHOLAFIN.NS",
    "PFC.NS",
    "RECLTD.NS",
    "IOC.NS",
    "BPCL.NS",
    "GAIL.NS",
    "HINDPETRO.NS",
    "VEDL.NS",
    "NMDC.NS",
    "JINDALSTEL.NS",
    "SAIL.NS",
    "DLF.NS",
    "LODHA.NS",
    "GODREJPROP.NS",
    "LTIM.NS",
    "COFORGE.NS",
    "PERSISTENT.NS",
    "MPHASIS.NS",
    "OFSS.NS",
    "APOLLOHOSP.NS",
    "MAXHEALTH.NS",
    "AUROPHARMA.NS",
    "DIVISLAB.NS",
    "LUPIN.NS",
    "ZYDUSLIFE.NS",
    "TORNTPHARM.NS",
    "INDIGO.NS",
    "IRCTC.NS",
    "IRFC.NS",
    "RVNL.NS",
    "CONCOR.NS",
    "INDUSTOWER.NS",
    "BHARTIARTL.NS",
    "SIEMENS.NS",
    "ABB.NS",
    "CUMMINSIND.NS",
    "AMBUJACEM.NS",
    "SHREECEM.NS",
    "PIDILITIND.NS",
    "SRF.NS",
    "INDHOTEL.NS",
    "MOTHERSON.NS",
    "BOSCHLTD.NS",
]


# Remove duplicates
NIFTY100 = list(dict.fromkeys(NIFTY100))


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
<style>

.main-title {
    font-size: 28px;
    font-weight: 800;
}

.sub-title {
    color: #777;
    margin-bottom: 15px;
}

.status-on {
    background: #16a34a;
    color: white;
    padding: 7px 14px;
    border-radius: 20px;
    font-weight: 800;
    display: inline-block;
}

.status-off {
    background: #dc2626;
    color: white;
    padding: 7px 14px;
    border-radius: 20px;
    font-weight: 800;
    display: inline-block;
}

.signal-box {
    padding: 12px;
    border-radius: 10px;
    border: 1px solid rgba(128,128,128,.25);
    margin-bottom: 8px;
}

</style>
""",
    unsafe_allow_html=True,
)


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
                indent=2,
                ensure_ascii=False
            )

    except Exception as e:

        st.warning(
            "Watchlist save nahi ho payi: "
            + str(e)
        )


# =========================================================
# SESSION STATE
# =========================================================

if "watchlist" not in st.session_state:
    st.session_state.watchlist = load_watchlist()

if "running" not in st.session_state:
    st.session_state.running = True


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">'
    '📈 Nifty 100 Heikin Ashi Bollinger Alert'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">'
    'NSE Data • 1 Day • Heikin Ashi • Bollinger 40 / 4'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# ON / OFF
# =========================================================

c1, c2, c3 = st.columns(
    [1.2, 1.2, 4]
)

with c1:

    if st.button(
        "🟢 ON",
        use_container_width=True
    ):

        st.session_state.running = True
        st.rerun()

with c2:

    if st.button(
        "🔴 OFF",
        use_container_width=True
    ):

        st.session_state.running = False
        st.rerun()

with c3:

    if st.session_state.running:

        st.markdown(
            '<span class="status-on">'
            'RUNNING'
            '</span>',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<span class="status-off">'
            'STOPPED'
            '</span>',
            unsafe_allow_html=True
        )


# =========================================================
# SETTINGS
# =========================================================

a, b, c, d = st.columns(4)

a.metric(
    "Universe",
    "Nifty 100"
)

b.metric(
    "Timeframe",
    "1 Day"
)

c.metric(
    "BB Length",
    BB_LENGTH
)

d.metric(
    "Multiplier",
    BB_MULTIPLIER
)


# =========================================================
# HEIKIN ASHI
# =========================================================

def make_heikin_ashi(df):

    df = df.copy()

    if df.empty:
        return df

    ha = pd.DataFrame(
        index=df.index
    )

    ha["HA_Close"] = (
        df["Open"]
        + df["High"]
        + df["Low"]
        + df["Close"]
    ) / 4

    ha_open = []

    for i in range(len(df)):

        if i == 0:

            value = (
                df["Open"].iloc[i]
                + df["Close"].iloc[i]
            ) / 2

        else:

            value = (
                ha_open[i - 1]
                + ha["HA_Close"].iloc[i - 1]
            ) / 2

        ha_open.append(value)

    ha["HA_Open"] = ha_open

    ha["HA_High"] = pd.concat(
        [
            df["High"],
            ha["HA_Open"],
            ha["HA_Close"]
        ],
        axis=1
    ).max(axis=1)

    ha["HA_Low"] = pd.concat(
        [
            df["Low"],
            ha["HA_Open"],
            ha["HA_Close"]
        ],
        axis=1
    ).min(axis=1)

    return ha


# =========================================================
# DOWNLOAD DATA
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False
)
def download_data(symbol):

    try:

        df = yf.download(
            symbol,
            period="1y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return pd.DataFrame()

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
# INDICATORS
# =========================================================

def calculate_indicator(df):

    ha = make_heikin_ashi(
        df
    )

    if len(ha) < BB_LENGTH + 2:

        return pd.DataFrame()

    ha["Middle"] = (
        ha["HA_Close"]
        .rolling(
            BB_LENGTH
        )
        .mean()
    )

    ha["STD"] = (
        ha["HA_Close"]
        .rolling(
            BB_LENGTH
        )
        .std()
    )

    ha["Upper"] = (
        ha["Middle"]
        + BB_MULTIPLIER
        * ha["STD"]
    )

    ha["Lower"] = (
        ha["Middle"]
        - BB_MULTIPLIER
        * ha["STD"]
    )

    return ha.dropna(
        subset=[
            "Middle"
        ]
    )


# =========================================================
# SIGNAL CHECK
# =========================================================

def find_today_signal(
    symbol,
    df
):

    ind = calculate_indicator(
        df
    )

    if len(ind) < 2:

        return None

    prev = ind.iloc[-2]
    curr = ind.iloc[-1]

    prev_close = float(
        prev["HA_Close"]
    )

    curr_close = float(
        curr["HA_Close"]
    )

    prev_middle = float(
        prev["Middle"]
    )

    curr_middle = float(
        curr["Middle"]
    )

    condition = (
        prev_close <= prev_middle
        and curr_close > curr_middle
    )

    if not condition:

        return None

    date_value = ind.index[-1]

    if hasattr(
        date_value,
        "date"
    ):

        signal_date = str(
            date_value.date()
        )

    else:

        signal_date = str(
            date_value
        )

    high = float(
        curr["HA_High"]
    )

    return {
        "symbol": symbol,
        "signal_date": signal_date,
        "trigger_high": high,
        "middle": curr_middle,
        "ha_close": curr_close,
        "status": "WATCH",
        "entry_date": "",
        "entry_time": "",
        "entry_price": "",
        "watch_until": "",
    }


# =========================================================
# TRADING DAYS
# =========================================================

def add_two_trading_days(
    date_string
):

    try:

        d = pd.Timestamp(
            date_string
        )

        days = 0

        while days < WATCH_DAYS:

            d = d + pd.Timedelta(
                days=1
            )

            if d.weekday() < 5:
                days += 1

        return str(
            d.date()
        )

    except Exception:

        return date_string


# =========================================================
# UPDATE WATCHLIST
# =========================================================

def add_new_signals():

    watchlist = st.session_state.watchlist

    today = datetime.now(
        IST
    ).date()

    added = []

    for symbol in NIFTY100:

        # Existing active signal?
        existing = [
            x
            for x in watchlist
            if x.get("symbol") == symbol
            and x.get("status") == "WATCH"
        ]

        if existing:
            continue

        df = download_data(
            symbol
        )

        if df.empty:
            continue

        signal = find_today_signal(
            symbol,
            df
        )

        if signal is None:
            continue

        # Only today's latest daily candle
        if signal["signal_date"] != str(today):

            continue

        signal["watch_until"] = (
            add_two_trading_days(
                signal["signal_date"]
            )
        )

        watchlist.append(
            signal
        )

        added.append(
            symbol
        )

    st.session_state.watchlist = watchlist

    save_watchlist(
        watchlist
    )

    return added


# =========================================================
# CHECK ACTIVE WATCHES
# =========================================================

def check_watchlist():

    watchlist = st.session_state.watchlist

    today = datetime.now(
        IST
    ).date()

    current_time = datetime.now(
        IST
    )

    changed = False

    for item in watchlist:

        if item.get("status") != "WATCH":
            continue

        symbol = item.get(
            "symbol"
        )

        watch_until = item.get(
            "watch_until"
        )

        try:

            expiry = pd.Timestamp(
                watch_until
            ).date()

        except Exception:

            continue

        # Expired
        if today > expiry:

            item["status"] = "EXPIRED"

            changed = True

            continue

        df = download_data(
            symbol
        )

        if df.empty:
            continue

        # Latest actual NSE candle
        latest = df.iloc[-1]

        current_high = float(
            latest["High"]
        )

        trigger = float(
            item["trigger_high"]
        )

        if current_high > trigger:

            item["status"] = "TRIGGERED"

            item["entry_date"] = (
                str(today)
            )

            item["entry_time"] = (
                current_time.strftime(
                    "%H:%M:%S"
                )
            )

            item["entry_price"] = (
                round(
                    trigger,
                    2
                )
            )

            changed = True

    if changed:

        st.session_state.watchlist = watchlist

        save_watchlist(
            watchlist
        )


# =========================================================
# RUN SCAN
# =========================================================

if st.session_state.running:

    st.info(
        "System ON hai. NSE daily data ke basis par scan ho raha hai."
    )

    today = datetime.now(
        IST
    )

    # Daily signal check
    if today.weekday() < 5:

        with st.spinner(
            "Nifty 100 scan ho raha hai..."
        ):

            new_symbols = add_new_signals()

            check_watchlist()

        if new_symbols:

            st.success(
                "New WATCH signal: "
                + ", ".join(
                    new_symbols
                )
            )

    else:

        st.info(
            "Weekend hai. NSE daily scan nahi chalega."
        )

else:

    st.warning(
        "System OFF hai. Scan band hai."
    )


# =========================================================
# WATCHLIST
# =========================================================

st.divider()

st.subheader(
    "👀 WATCH LIST"
)

active = [
    x
    for x in st.session_state.watchlist
    if x.get("status") == "WATCH"
]

triggered = [
    x
    for x in st.session_state.watchlist
    if x.get("status") == "TRIGGERED"
]

expired = [
    x
    for x in st.session_state.watchlist
    if x.get("status") == "EXPIRED"
]


if not active:

    st.info(
        "Abhi koi share WATCH condition me nahi hai."
    )

else:

    rows = []

    for x in active:

        rows.append(
            {
                "Share": x.get(
                    "symbol"
                ),
                "Signal Date": x.get(
                    "signal_date"
                ),
                "Trigger High": x.get(
                    "trigger_high"
                ),
                "Middle Band": x.get(
                    "middle"
                ),
                "HA Close": x.get(
                    "ha_close"
                ),
                "Watch Till": x.get(
                    "watch_until"
                ),
                "Status": "WATCH",
            }
        )

    watch_df = pd.DataFrame(
        rows
    )

    st.dataframe(
        watch_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# TRIGGERED
# =========================================================

st.divider()

st.subheader(
    "🔔 HIGH CROSS / BUY ALERT"
)

if not triggered:

    st.info(
        "Abhi kisi WATCH share ka Trigger High cross nahi hua."
    )

else:

    rows = []

    for x in triggered:

        rows.append(
            {
                "Share": x.get(
                    "symbol"
                ),
                "Signal Date": x.get(
                    "signal_date"
                ),
                "Trigger High": x.get(
                    "trigger_high"
                ),
                "Entry Date": x.get(
                    "entry_date"
                ),
                "Entry Time": x.get(
                    "entry_time"
                ),
                "Entry Price": x.get(
                    "entry_price"
                ),
                "Status": "BUY ALERT",
            }
        )

    trigger_df = pd.DataFrame(
        rows
    )

    st.dataframe(
        trigger_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# OLD / EXPIRED
# =========================================================

if expired:

    with st.expander(
        "Expired Signals"
    ):

        rows = []

        for x in expired:

            rows.append(
                {
                    "Share": x.get(
                        "symbol"
                    ),
                    "Signal Date": x.get(
                        "signal_date"
                    ),
                    "Trigger High": x.get(
                        "trigger_high"
                    ),
                    "Watch Till": x.get(
                        "watch_until"
                    ),
                    "Status": "EXPIRED",
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# RULE DISPLAY
# =========================================================

st.divider()

st.subheader(
    "Strategy Rules"
)

st.markdown(
    """
**Universe:** Nifty 100

**Timeframe:** 1 Day

**Candle:** Heikin Ashi

**Bollinger Length:** 40

**Multiplier:** 4

**WATCH condition:**

1. Previous Heikin Ashi candle Close <= Middle Band
2. Current Heikin Ashi candle Close > Middle Band
3. Cross wali candle ka High = BUY Trigger
4. Share ko agle 2 trading days tak WATCH kiya jayega
5. High cross hone par BUY ALERT generate hoga

**Important:** Yeh app sirf alert/watchlist banata hai. Dhan order place nahi karta.
"""
)


# =========================================================
# FOOTER
# =========================================================

st.caption(
    "NSE market data via Yahoo Finance. "
    "Data availability provider par depend karti hai."
)
```

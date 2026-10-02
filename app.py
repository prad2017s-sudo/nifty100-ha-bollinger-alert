
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime, timedelta, time as dt_time
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import escape


# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(
    page_title="Nifty 100 HA Bollinger Alert",
    page_icon="📈",
    layout="wide",
)


# =========================================================
# CONSTANTS
# =========================================================

IST = ZoneInfo("Asia/Kolkata")

MARKET_START = dt_time(9, 0)
MARKET_END = dt_time(15, 30)

REFRESH_SECONDS = 10

BB_LENGTH = 40
BB_MULTIPLIER = 4.0

INDEX_NAME = "NIFTY 100"

NSE_HOME = "https://www.nseindia.com"

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
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

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.app-title {
    font-size: 27px;
    font-weight: 800;
    line-height: 1.25;
}

.app-subtitle {
    color: #777;
    font-size: 14px;
    margin-top: 4px;
    margin-bottom: 14px;
}

.status-box {
    padding: 12px 14px;
    border-radius: 10px;
    border: 1px solid rgba(128,128,128,.25);
    background: rgba(128,128,128,.07);
    margin-bottom: 12px;
}

.watch-card {
    padding: 13px;
    border-radius: 10px;
    border: 1px solid rgba(128,128,128,.25);
    background: rgba(128,128,128,.06);
    margin-bottom: 10px;
}

.watch-symbol {
    font-size: 17px;
    font-weight: 800;
}

.watch-trigger {
    font-size: 14px;
    margin-top: 5px;
}

.alert-card {
    padding: 14px;
    border-radius: 10px;
    border: 2px solid #16a34a;
    background: rgba(22,163,74,.10);
    margin-bottom: 10px;
}

.alert-title {
    font-size: 18px;
    font-weight: 900;
}

.alert-price {
    font-size: 14px;
    margin-top: 5px;
}

.signal-card {
    padding: 12px;
    border-radius: 10px;
    border: 1px solid rgba(128,128,128,.25);
    background: rgba(128,128,128,.06);
    margin-bottom: 8px;
}

.signal-buy {
    color: #16a34a;
    font-weight: 900;
}

.signal-watch {
    color: #ca8a04;
    font-weight: 900;
}

.small-muted {
    color: #777;
    font-size: 12px;
}

@media(max-width:700px) {

    .block-container {
        padding-top: 1.5rem;
    }

    .app-title {
        font-size: 20px;
    }

    .app-subtitle {
        font-size: 11px;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# NSE SESSION
# =========================================================

@st.cache_resource
def get_nse_session():

    session = requests.Session()

    session.headers.update(
        NSE_HEADERS
    )

    try:
        session.get(
            NSE_HOME,
            timeout=15
        )
    except Exception:
        pass

    return session


NSE = get_nse_session()


# =========================================================
# SAFE NSE GET
# =========================================================

def nse_get(
    url,
    params=None,
    timeout=15
):

    try:

        response = NSE.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                **NSE_HEADERS,
                "Referer": NSE_HOME + "/",
            }
        )

        if response.status_code == 200:

            return response.json()

        # Refresh NSE cookies once
        try:
            NSE.get(
                NSE_HOME,
                timeout=10,
                headers=NSE_HEADERS
            )
        except Exception:
            pass

        response = NSE.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                **NSE_HEADERS,
                "Referer": NSE_HOME + "/",
            }
        )

        if response.status_code == 200:
            return response.json()

    except Exception:
        pass

    return None


# =========================================================
# NIFTY 100 CONSTITUENTS
# =========================================================

@st.cache_data(
    ttl=6 * 60 * 60,
    show_spinner=False
)
def get_nifty100_symbols():

    url = (
        NSE_HOME
        + "/api/equity-stockIndices"
    )

    data = nse_get(
        url,
        params={
            "index": "NIFTY 100"
        },
        timeout=20
    )

    if not data:
        return []

    rows = data.get(
        "data",
        []
    )

    symbols = []

    for row in rows:

        symbol = str(
            row.get(
                "symbol",
                ""
            )
        ).strip().upper()

        if not symbol:
            continue

        # Avoid index row if returned
        if symbol in {
            "NIFTY 100",
            "NIFTY100"
        }:
            continue

        symbols.append(
            symbol
        )

    return list(
        dict.fromkeys(symbols)
    )


# =========================================================
# FALLBACK NIFTY 100 LIST
#
# Used only if NSE constituent endpoint temporarily fails.
# =========================================================

FALLBACK_NIFTY100 = [
    "ADANIENT",
    "ADANIPORTS",
    "ADANIPOWER",
    "ADANIGREEN",
    "ADANIENSOL",
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
    "DIVISLAB",
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
    "HINDZINC",
    "ICICIBANK",
    "ICICIGI",
    "ICICIPRULI",
    "INDIGO",
    "INDUSINDBK",
    "INFY",
    "ITC",
    "JIOFIN",
    "JSWSTEEL",
    "KOTAKBANK",
    "LT",
    "LICI",
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
    "VEDL",
    "APOLLOTYRE",
    "ABB",
    "ABBOTINDIA",
    "AMBUJACEM",
    "BANKBARODA",
    "BERGEPAINT",
    "BOSCHLTD",
    "CANBK",
    "CHOLAFIN",
    "COLPAL",
    "CONCOR",
    "CUMMINSIND",
    "DABUR",
    "DLF",
    "DMART",
    "EXIDEIND",
    "FEDERALBNK",
    "GAIL",
    "GODREJCP",
    "GODREJPROP",
    "HAL",
    "HAVELLS",
    "ICICIBANK",
    "IOC",
    "IRCTC",
    "IRFC",
    "JINDALSTEL",
    "LICHSGFIN",
    "MOTHERSON",
    "MUTHOOTFIN",
    "NMDC",
    "OFSS",
    "PFC",
    "PIDILITIND",
    "PNB",
]


# =========================================================
# HISTORICAL DATA
# =========================================================

def get_historical_data(
    symbol,
    days=420
):

    end_date = datetime.now(
        IST
    ).date()

    start_date = (
        end_date
        - timedelta(days=days)
    )

    url = (
        NSE_HOME
        + "/api/historical/cm/equity"
    )

    params = {
        "symbol": symbol,
        "series": "[EQ]",
        "from": start_date.strftime(
            "%d-%m-%Y"
        ),
        "to": end_date.strftime(
            "%d-%m-%Y"
        ),
    }

    data = nse_get(
        url,
        params=params,
        timeout=20
    )

    if not data:
        return pd.DataFrame()

    records = data.get(
        "data",
        []
    )

    if not records:
        return pd.DataFrame()

    rows = []

    for item in records:

        try:

            date_value = item.get(
                "CH_TIMESTAMP"
            )

            if not date_value:
                date_value = item.get(
                    "TIMESTAMP"
                )

            close = item.get(
                "CH_CLOSING_PRICE"
            )

            high = item.get(
                "CH_TRADE_HIGH_PRICE"
            )

            low = item.get(
                "CH_TRADE_LOW_PRICE"
            )

            open_price = item.get(
                "CH_OPENING_PRICE"
            )

            if (
                date_value is None
                or close is None
                or high is None
                or low is None
                or open_price is None
            ):
                continue

            rows.append(
                {
                    "Date": pd.to_datetime(
                        date_value,
                        dayfirst=True,
                        errors="coerce"
                    ),
                    "Open": float(
                        open_price
                    ),
                    "High": float(
                        high
                    ),
                    "Low": float(
                        low
                    ),
                    "Close": float(
                        close
                    ),
                }
            )

        except Exception:
            continue

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(
        rows
    )

    df = df.dropna(
        subset=[
            "Date",
            "Open",
            "High",
            "Low",
            "Close"
        ]
    )

    df = (
        df
        .drop_duplicates(
            "Date"
        )
        .sort_values(
            "Date"
        )
        .reset_index(
            drop=True
        )
    )

    return df


# =========================================================
# HEIKIN ASHI
# =========================================================

def make_heikin_ashi(
    df
):

    if df.empty:
        return pd.DataFrame()

    out = df.copy()

    ha_close = (
        out["Open"]
        + out["High"]
        + out["Low"]
        + out["Close"]
    ) / 4.0

    ha_open = np.zeros(
        len(out)
    )

    ha_open[0] = (
        out["Open"].iloc[0]
        + out["Close"].iloc[0]
    ) / 2.0

    for i in range(
        1,
        len(out)
    ):

        ha_open[i] = (
            ha_open[i - 1]
            + ha_close.iloc[i - 1]
        ) / 2.0

    ha_high = pd.concat(
        [
            pd.Series(
                ha_open,
                index=out.index
            ),
            ha_close,
            out["High"],
        ],
        axis=1
    ).max(
        axis=1
    )

    ha_low = pd.concat(
        [
            pd.Series(
                ha_open,
                index=out.index
            ),
            ha_close,
            out["Low"],
        ],
        axis=1
    ).min(
        axis=1
    )

    out["HA_Open"] = ha_open
    out["HA_High"] = ha_high
    out["HA_Low"] = ha_low
    out["HA_Close"] = ha_close

    return out


# =========================================================
# BOLLINGER
# =========================================================

def add_bollinger(
    df
):

    out = df.copy()

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
        + BB_MULTIPLIER
        * out["Std"]
    )

    out["Lower"] = (
        out["Middle"]
        - BB_MULTIPLIER
        * out["Std"]
    )

    return out


# =========================================================
# FIND WATCH CONDITION
# =========================================================

def find_watch_signal(
    df
):

    if df.empty:
        return None

    df = make_heikin_ashi(
        df
    )

    df = add_bollinger(
        df
    )

    if len(df) < BB_LENGTH + 2:
        return None

    # Only completed historical daily candles.
    # Current market day's incomplete candle is excluded.
    today = datetime.now(
        IST
    ).date()

    df["DateOnly"] = (
        pd.to_datetime(
            df["Date"]
        ).dt.date
    )

    completed = df[
        df["DateOnly"]
        < today
    ].copy()

    if len(completed) < BB_LENGTH + 2:
        return None

    completed = completed.dropna(
        subset=[
            "Middle",
            "HA_Close",
            "HA_High"
        ]
    )

    if len(completed) < 2:
        return None

    previous = completed.iloc[
        -2
    ]

    cross = completed.iloc[
        -1
    ]

    # =====================================================
    # USER CONDITION
    #
    # Previous candle Close BELOW Middle
    # Current candle Close ABOVE Middle
    # =====================================================

    condition = (
        float(
            previous["HA_Close"]
        )
        < float(
            previous["Middle"]
        )
        and
        float(
            cross["HA_Close"]
        )
        > float(
            cross["Middle"]
        )
    )

    if not condition:
        return None

    return {
        "date": cross["Date"],
        "trigger": float(
            cross["HA_High"]
        ),
        "ha_open": float(
            cross["HA_Open"]
        ),
        "ha_high": float(
            cross["HA_High"]
        ),
        "ha_low": float(
            cross["HA_Low"]
        ),
        "ha_close": float(
            cross["HA_Close"]
        ),
        "middle": float(
            cross["Middle"]
        ),
        "previous_close": float(
            previous["HA_Close"]
        ),
        "previous_middle": float(
            previous["Middle"]
        ),
    }


# =========================================================
# CACHE HISTORICAL SIGNAL
# =========================================================

@st.cache_data(
    ttl=6 * 60 * 60,
    show_spinner=False
)
def calculate_all_watch_signals(
    symbols_tuple
):

    symbols = list(
        symbols_tuple
    )

    results = {}

    progress = None

    # Sequential is intentionally used to reduce
    # NSE request pressure.
    for symbol in symbols:

        try:

            history = get_historical_data(
                symbol
            )

            signal = find_watch_signal(
                history
            )

            if signal:

                results[symbol] = signal

        except Exception:
            continue

    return results


# =========================================================
# CURRENT NIFTY 100 QUOTES
# =========================================================

def get_current_nifty100_quotes():

    url = (
        NSE_HOME
        + "/api/equity-stockIndices"
    )

    data = nse_get(
        url,
        params={
            "index": "NIFTY 100"
        },
        timeout=20
    )

    result = {}

    if not data:
        return result

    rows = data.get(
        "data",
        []
    )

    for row in rows:

        symbol = str(
            row.get(
                "symbol",
                ""
            )
        ).strip().upper()

        if not symbol:
            continue

        try:

            ltp = row.get(
                "lastPrice"
            )

            if ltp is None:
                ltp = row.get(
                    "lastPrice"
                )

            if ltp is None:
                continue

            result[symbol] = {
                "price": float(
                    ltp
                ),
                "change": (
                    float(
                        row.get(
                            "pChange"
                        )
                    )
                    if row.get(
                        "pChange"
                    ) is not None
                    else None
                ),
                "previous_close": (
                    float(
                        row.get(
                            "previousClose"
                        )
                    )
                    if row.get(
                        "previousClose"
                    ) is not None
                    else None
                ),
                "day_high": (
                    float(
                        row.get(
                            "dayHigh"
                        )
                    )
                    if row.get(
                        "dayHigh"
                    ) is not None
                    else None
                ),
                "day_low": (
                    float(
                        row.get(
                            "dayLow"
                        )
                    )
                    if row.get(
                        "dayLow"
                    ) is not None
                    else None
                ),
            }

        except Exception:
            continue

    return result


# =========================================================
# SESSION HELPERS
# =========================================================

def is_market_monitoring_time(
    now
):

    t = now.time()

    return (
        t >= MARKET_START
        and t <= MARKET_END
    )


def market_status_text(
    now
):

    t = now.time()

    if t < MARKET_START:
        return "WAITING — 09:00 par monitoring start hoga"

    if t > MARKET_END:
        return "CLOSED — 15:30 ke baad monitoring band hai"

    return "LIVE MONITORING"


# =========================================================
# SESSION STATE
# =========================================================

if "alerts" not in st.session_state:
    st.session_state.alerts = {}

if "watch_refresh" not in st.session_state:
    st.session_state.watch_refresh = 0

if "manual_scan" not in st.session_state:
    st.session_state.manual_scan = False


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="app-title">'
    '📈 Nifty 100 Heikin Ashi Bollinger Alert'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="app-subtitle">'
    'NSE • 1 Day • Heikin Ashi • Bollinger 40 / 4 '
    '• BUY Trigger = Cross Candle High'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# CURRENT TIME
# =========================================================

now = datetime.now(
    IST
)

monitoring = is_market_monitoring_time(
    now
)


# =========================================================
# TOP CONTROLS
# =========================================================

c1, c2, c3, c4 = st.columns(
    4
)

with c1:

    st.metric(
        "Universe",
        INDEX_NAME
    )

with c2:

    st.metric(
        "Timeframe",
        "1 Day"
    )

with c3:

    st.metric(
        "BB",
        "40 / 4"
    )

with c4:

    st.metric(
        "Refresh",
        "10 sec"
    )


# =========================================================
# MARKET STATUS
# =========================================================

if monitoring:

    st.markdown(
        f"""
        <div class="status-box">
            🟢 <b>LIVE MONITORING</b><br>
            NSE price trigger checking ON<br>
            <span class="small-muted">
                {now.strftime("%d %b %Y %H:%M:%S IST")}
                &nbsp;|&nbsp;
                Monitoring: 09:00–15:30
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

elif now.time() < MARKET_START:

    st.markdown(
        f"""
        <div class="status-box">
            🟡 <b>WAITING</b><br>
            Monitoring 09:00 IST par start hoga.<br>
            <span class="small-muted">
                Current time:
                {now.strftime("%d %b %Y %H:%M:%S IST")}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        f"""
        <div class="status-box">
            🔴 <b>MARKET MONITORING CLOSED</b><br>
            15:30 IST ke baad automatic checking band hai.<br>
            <span class="small-muted">
                Last check:
                {now.strftime("%d %b %Y %H:%M:%S IST")}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# CONTROLS
# =========================================================

control1, control2 = st.columns(
    [1, 4]
)

with control1:

    if st.button(
        "🔄 Re-scan",
        use_container_width=True
    ):

        st.cache_data.clear()

        st.session_state.watch_refresh += 1

        st.rerun()


with control2:

    st.caption(
        "Re-scan se Nifty 100 ke daily candles dobara calculate honge. "
        "Normal monitoring mein sirf current NSE quote check hota hai."
    )


# =========================================================
# LOAD NIFTY 100
# =========================================================

symbols = get_nifty100_symbols()

if not symbols:

    symbols = FALLBACK_NIFTY100


symbols = list(
    dict.fromkeys(
        symbols
    )
)


# =========================================================
# WATCH SIGNAL CALCULATION
# =========================================================

with st.spinner(
    "Nifty 100 Heikin Ashi + Bollinger signals calculate ho rahe hain..."
):

    watch_signals = calculate_all_watch_signals(
        tuple(symbols)
    )


# =========================================================
# CURRENT QUOTES
# =========================================================

quotes = {}

if monitoring:

    quotes = get_current_nifty100_quotes()

else:

    # Outside monitoring window, one quote request
    # can still show latest NSE snapshot.
    quotes = get_current_nifty100_quotes()


# =========================================================
# BUILD WATCHLIST
# =========================================================

watch_rows = []

for symbol, signal in watch_signals.items():

    q = quotes.get(
        symbol,
        {}
    )

    price = q.get(
        "price"
    )

    trigger = float(
        signal["trigger"]
    )

    crossed = (
        price is not None
        and float(price) > trigger
    )

    watch_rows.append(
        {
            "Symbol": symbol,
            "Cross Date": signal["date"],
            "Trigger": trigger,
            "Current Price": price,
            "Distance %": (
                (
                    (
                        float(price)
                        - trigger
                    )
                    / trigger
                    * 100
                )
                if price is not None
                and trigger > 0
                else None
            ),
            "Status": (
                "BUY ALERT"
                if crossed
                else "WATCH"
            ),
            "Middle": signal["middle"],
            "HA Close": signal["ha_close"],
            "HA High": signal["ha_high"],
            "Previous HA Close": signal[
                "previous_close"
            ],
            "Previous Middle": signal[
                "previous_middle"
            ],
        }
    )


watch_df = pd.DataFrame(
    watch_rows
)


# =========================================================
# ALERT PROCESSING
# =========================================================

new_alerts = []

if monitoring:

    for row in watch_rows:

        symbol = row["Symbol"]

        if row["Status"] != "BUY ALERT":
            continue

        alert_key = (
            f"{symbol}_"
            f"{pd.Timestamp(row['Cross Date']).date()}_"
            f"{row['Trigger']:.4f}"
        )

        if (
            alert_key
            not in st.session_state.alerts
        ):

            st.session_state.alerts[
                alert_key
            ] = {
                "symbol": symbol,
                "trigger": row["Trigger"],
                "price": row["Current Price"],
                "time": now,
            }

            new_alerts.append(
                st.session_state.alerts[
                    alert_key
                ]
            )


# =========================================================
# NEW ALERTS
# =========================================================

if new_alerts:

    for alert in new_alerts:

        st.toast(
            (
                f"BUY ALERT: "
                f"{alert['symbol']} "
                f"above ₹{alert['trigger']:.2f}"
            ),
            icon="🚨"
        )

        st.markdown(
            f"""
            <div class="alert-card">
                <div class="alert-title">
                    🚨 BUY ALERT — {escape(alert["symbol"])}
                </div>
                <div class="alert-price">
                    Trigger:
                    <b>₹{alert["trigger"]:.2f}</b>
                    &nbsp; | &nbsp;
                    Current:
                    <b>₹{alert["price"]:.2f}</b>
                </div>
                <div class="small-muted">
                    Trigger crossed at
                    {alert["time"].strftime("%H:%M:%S IST")}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# WATCHLIST HEADER
# =========================================================

st.subheader(
    "👀 WATCHLIST"
)

st.caption(
    "Previous HA Close < Middle Band → "
    "Cross candle HA Close > Middle Band. "
    "Us cross candle ka HA High BUY trigger hai."
)


# =========================================================
# WATCHLIST
# =========================================================

if watch_df.empty:

    st.info(
        "Abhi Nifty 100 mein given condition wala "
        "koi completed daily Heikin Ashi cross nahi mila."
    )

else:

    # =====================================================
    # SORT BUY ALERT FIRST
    # =====================================================

    watch_df["_sort"] = (
        watch_df["Status"]
        .eq("BUY ALERT")
        .astype(int)
    )

    watch_df = (
        watch_df
        .sort_values(
            [
                "_sort",
                "Symbol"
            ],
            ascending=[
                False,
                True
            ]
        )
        .drop(
            columns="_sort"
        )
        .reset_index(
            drop=True
        )
    )

    # =====================================================
    # SUMMARY
    # =====================================================

    alert_count = int(
        (
            watch_df["Status"]
            == "BUY ALERT"
        ).sum()
    )

    watch_count = int(
        (
            watch_df["Status"]
            == "WATCH"
        ).sum()
    )

    a1, a2, a3 = st.columns(
        3
    )

    a1.metric(
        "Total Watch",
        len(watch_df)
    )

    a2.metric(
        "BUY Alerts",
        alert_count
    )

    a3.metric(
        "Still Watching",
        watch_count
    )


    # =====================================================
    # CARDS
    # =====================================================

    for _, row in watch_df.iterrows():

        symbol = str(
            row["Symbol"]
        )

        trigger = float(
            row["Trigger"]
        )

        price = row[
            "Current Price"
        ]

        distance = row[
            "Distance %"
        ]

        status = row[
            "Status"
        ]

        cross_date = pd.to_datetime(
            row["Cross Date"]
        )

        if status == "BUY ALERT":

            status_html = (
                '<span class="signal-buy">'
                '🚨 BUY ALERT'
                '</span>'
            )

        else:

            status_html = (
                '<span class="signal-watch">'
                '👀 WATCH'
                '</span>'
            )

        price_text = (
            "--"
            if pd.isna(price)
            else f"₹{float(price):,.2f}"
        )

        distance_text = (
            "--"
            if pd.isna(distance)
            else f"{float(distance):+.2f}%"
        )

        st.markdown(
            f"""
            <div class="watch-card">

                <div class="watch-symbol">
                    {escape(symbol)}
                    &nbsp;&nbsp;
                    {status_html}
                </div>

                <div class="watch-trigger">
                    BUY Trigger:
                    <b>₹{trigger:,.2f}</b>
                    &nbsp; | &nbsp;
                    Current:
                    <b>{price_text}</b>
                    &nbsp; | &nbsp;
                    Distance:
                    <b>{distance_text}</b>
                </div>

                <div class="small-muted">
                    Cross Candle:
                    {cross_date.strftime("%d %b %Y")}
                    &nbsp; | &nbsp;
                    HA Close:
                    ₹{float(row["HA Close"]):,.2f}
                    &nbsp; | &nbsp;
                    HA High:
                    ₹{float(row["HA High"]):,.2f}
                    &nbsp; | &nbsp;
                    Middle:
                    ₹{float(row["Middle"]):,.2f}
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# ALERT HISTORY
# =========================================================

if st.session_state.alerts:

    st.subheader(
        "🚨 Alert History"
    )

    history_rows = []

    for key, alert in reversed(
        list(
            st.session_state.alerts.items()
        )
    ):

        history_rows.append(
            {
                "Symbol": alert[
                    "symbol"
                ],
                "Trigger": (
                    f"₹{alert['trigger']:,.2f}"
                ),
                "Price at Alert": (
                    f"₹{alert['price']:,.2f}"
                ),
                "Time": alert[
                    "time"
                ].strftime(
                    "%d %b %Y %H:%M:%S"
                ),
            }
        )

    history_df = pd.DataFrame(
        history_rows
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# SIGNAL DETAILS
# =========================================================

with st.expander(
    "📐 Strategy Rules"
):

    st.markdown(
        f"""
**Universe:** Nifty 100

**Timeframe:** 1 Day

**Candle:** Heikin Ashi

**Bollinger Length:** {BB_LENGTH}

**Bollinger Multiplier:** {BB_MULTIPLIER}

**WATCH condition:**

1. Previous completed Heikin Ashi candle ka Close
   Middle Band se **neeche** ho.

2. Latest completed Heikin Ashi candle ka Close
   Middle Band se **upar** ho.

3. Ye latest candle **cross candle** hai.

4. Cross candle ka **Heikin Ashi High**
   BUY Trigger hai.

5. Current NSE price jab is High ko **upar cross**
   kare, tab BUY ALERT.

**Monitoring:** 09:00–15:30 IST

**Refresh:** 10 seconds

**Dhan:** Not used.
"""
    )


# =========================================================
# DATA SOURCE NOTE
# =========================================================

with st.expander(
    "ℹ️ Data / Alert Note"
):

    st.write(
        "Ye app NSE public market-data endpoints ko use karta hai. "
        "NSE ke public endpoints temporary throttling ya access "
        "restriction de sakte hain. Aise case mein data blank/old "
        "ho sakta hai aur app retry karega."
    )

    st.write(
        "Daily Heikin Ashi/Bollinger signal completed daily candles "
        "par calculate hota hai. Current day ki incomplete candle ko "
        "WATCH signal banane ke liye use nahi kiya gaya hai."
    )

    st.write(
        "BUY ALERT sirf informational alert hai. "
        "Koi order place nahi hota."
    )


# =========================================================
# AUTO REFRESH
# =========================================================

# Streamlit built-in fragment refresh.
# This keeps the app checking current NSE price every 10 sec
# only while the page is running.

if monitoring:

    try:

        from streamlit_autorefresh import st_autorefresh

        st_autorefresh(
            interval=REFRESH_SECONDS * 1000,
            key="nifty100_alert_refresh"
        )

    except Exception:

        # Fallback: no hard failure if package is unavailable.
        pass

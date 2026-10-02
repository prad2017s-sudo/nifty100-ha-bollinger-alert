import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
page_title="Nifty 100 HA Bollinger Alert",
page_icon="📈",
layout="wide",
)

IST = ZoneInfo("Asia/Kolkata")

WATCH_FILE = "watchlist.json"

BB_LENGTH = 40
BB_MULTIPLIER = 4
WATCH_TRADING_DAYS = 2

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

NIFTY100 = list(dict.fromkeys(NIFTY100))

st.markdown(
""" <style>
.title {
font-size: 28px;
font-weight: 800;
margin-bottom: 3px;
}

```
.subtitle {
    color: #777;
    margin-bottom: 18px;
}

.on {
    background: #16a34a;
    color: white;
    padding: 7px 15px;
    border-radius: 20px;
    font-weight: 800;
    display: inline-block;
}

.off {
    background: #dc2626;
    color: white;
    padding: 7px 15px;
    border-radius: 20px;
    font-weight: 800;
    display: inline-block;
}
</style>
""",
unsafe_allow_html=True,
```

)

def load_watchlist():

```
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
```

def save_watchlist(data):

```
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
except Exception:
    pass
```

if "running" not in st.session_state:
st.session_state.running = True

if "watchlist" not in st.session_state:
st.session_state.watchlist = load_watchlist()

st.markdown(
'<div class="title">📈 Nifty 100 Heikin Ashi Bollinger Alert</div>',
unsafe_allow_html=True
)

st.markdown(
'<div class="subtitle">NSE Data • 1 Day • Heikin Ashi • Bollinger 40 / 4 • No Dhan</div>',
unsafe_allow_html=True
)

c1, c2, c3 = st.columns([1, 1, 4])

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
'<span class="on">RUNNING</span>',
unsafe_allow_html=True
)
else:
st.markdown(
'<span class="off">STOPPED</span>',
unsafe_allow_html=True
)

m1, m2, m3, m4 = st.columns(4)

m1.metric("Universe", "Nifty 100")
m2.metric("Timeframe", "1 Day")
m3.metric("BB Length", BB_LENGTH)
m4.metric("Multiplier", BB_MULTIPLIER)

def make_heikin_ashi(df):

```
if df.empty:
    return pd.DataFrame()

df = df.copy()

ha = pd.DataFrame(index=df.index)

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
        ha["HA_Close"],
    ],
    axis=1
).max(axis=1)

ha["HA_Low"] = pd.concat(
    [
        df["Low"],
        ha["HA_Open"],
        ha["HA_Close"],
    ],
    axis=1
).min(axis=1)

return ha
```

@st.cache_data(
ttl=3600,
show_spinner=False
)
def get_daily_data(symbol):

```
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

    if any(
        c not in df.columns
        for c in required
    ):
        return pd.DataFrame()

    for c in required:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )

    df = df.dropna(
        subset=required
    )

    return df

except Exception:
    return pd.DataFrame()
```

def calculate_bollinger(df):

```
ha = make_heikin_ashi(df)

if len(ha) < BB_LENGTH + 2:
    return pd.DataFrame()

ha["Middle"] = (
    ha["HA_Close"]
    .rolling(BB_LENGTH)
    .mean()
)

ha["STD"] = (
    ha["HA_Close"]
    .rolling(BB_LENGTH)
    .std()
)

ha["Upper"] = (
    ha["Middle"]
    + BB_MULTIPLIER * ha["STD"]
)

ha["Lower"] = (
    ha["Middle"]
    - BB_MULTIPLIER * ha["STD"]
)

return ha.dropna(
    subset=["Middle"]
)
```

def get_signal(symbol, df):

```
ind = calculate_bollinger(df)

if len(ind) < 2:
    return None

previous = ind.iloc[-2]
current = ind.iloc[-1]

previous_close = float(
    previous["HA_Close"]
)

previous_middle = float(
    previous["Middle"]
)

current_close = float(
    current["HA_Close"]
)

current_middle = float(
    current["Middle"]
)

crossed = (
    previous_close <= previous_middle
    and current_close > current_middle
)

if not crossed:
    return None

signal_date = ind.index[-1]

if hasattr(
    signal_date,
    "date"
):
    signal_date = str(
        signal_date.date()
    )
else:
    signal_date = str(
        signal_date
    )

trigger_high = float(
    current["HA_High"]
)

return {
    "symbol": symbol,
    "signal_date": signal_date,
    "trigger_high": round(
        trigger_high,
        2
    ),
    "middle": round(
        current_middle,
        2
    ),
    "ha_close": round(
        current_close,
        2
    ),
    "status": "WATCH",
    "watch_day": 0,
    "watch_until": "",
    "entry_date": "",
    "entry_time": "",
    "entry_price": "",
}
```

def is_weekday(date_obj):

```
return date_obj.weekday() < 5
```

def calculate_watch_until(signal_date):

```
try:

    d = pd.Timestamp(
        signal_date
    )

    count = 0

    while count < WATCH_TRADING_DAYS:

        d = d + pd.Timedelta(
            days=1
        )

        if d.weekday() < 5:
            count += 1

    return str(
        d.date()
    )

except Exception:

    return str(
        signal_date
    )
```

def already_exists(
symbol,
signal_date
):

```
for item in st.session_state.watchlist:

    if (
        item.get("symbol") == symbol
        and item.get("signal_date") == signal_date
    ):
        return True

return False
```

def scan_for_new_signals():

```
today = datetime.now(
    IST
).date()

today_string = str(today)

new_signals = []

for symbol in NIFTY100:

    df = get_daily_data(
        symbol
    )

    if df.empty:
        continue

    signal = get_signal(
        symbol,
        df
    )

    if signal is None:
        continue

    if signal["signal_date"] != today_string:
        continue

    if already_exists(
        symbol,
        signal["signal_date"]
    ):
        continue

    signal["watch_until"] = calculate_watch_until(
        signal["signal_date"]
    )

    st.session_state.watchlist.append(
        signal
    )

    new_signals.append(
        symbol
    )

if new_signals:
    save_watchlist(
        st.session_state.watchlist
    )

return new_signals
```

def check_expiry():

```
today = datetime.now(
    IST
).date()

changed = False

for item in st.session_state.watchlist:

    if
```

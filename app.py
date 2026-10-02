import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import json
import os
import time
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

# =========================================================
# CONFIG
# =========================================================

IST = ZoneInfo("Asia/Kolkata")

APP_TITLE = "Nifty 100 Heikin Ashi Bollinger Alert"

BOLL_LENGTH = 40
BOLL_MULTIPLIER = 4.0

WATCH_DAYS = 2

MARKET_START = "09:15"
MARKET_END = "15:30"

STATE_FILE = "watch_state.json"

NIFTY100_URL = (
    "https://www.niftyindices.com/IndexConstituent/"
    "ind_nifty100list.csv"
)

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📈",
    layout="wide",
)

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

.title {
    font-size: 28px;
    font-weight: 800;
}

.subtitle {
    color: #777;
    font-size: 14px;
    margin-bottom: 15px;
}

.box {
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
}

.watch {
    border-left: 5px solid #f59e0b;
}

.triggered {
    border-left: 5px solid #16a34a;
}

.expired {
    border-left: 5px solid #dc2626;
}

.big-status {
    font-size: 22px;
    font-weight: 800;
}

.small {
    color: #777;
    font-size: 12px;
}

.buy {
    color: #16a34a;
    font-weight: 800;
}

</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# HEADER
# =========================================================

st.markdown(
    f'<div class="title">📈 {APP_TITLE}</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="subtitle">
Nifty 100 • Heikin Ashi • Daily Bollinger Middle Cross •
2 Trading Day Watch • Dhan Not Used
</div>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SETTINGS
# =========================================================

with st.sidebar:

    st.header("Settings")

    enabled = st.toggle(
        "🟢 Monitoring ON",
        value=True,
        key="monitoring_enabled",
    )

    st.divider()

    st.write("Strategy")

    st.write("Universe: Nifty 100")
    st.write("Timeframe: 1 Day")
    st.write("Candle: Heikin Ashi")
    st.write(f"Bollinger Length: {BOLL_LENGTH}")
    st.write(f"Multiplier: {BOLL_MULTIPLIER}")
    st.write(f"Watch Period: {WATCH_DAYS} trading days")

    st.divider()

    st.write(
        "Daily signal scan: completed daily candle"
    )

    st.write(
        "Intraday trigger: 09:15–15:30"
    )

# =========================================================
# TIME
# =========================================================

now = datetime.now(IST)
today = now.date()

market_open = (
    now.strftime("%H:%M") >= MARKET_START
    and now.strftime("%H:%M") <= MARKET_END
)

st.info(
    f"Current: {now.strftime('%d-%b-%Y %H:%M:%S IST')} "
    f"| Monitoring: {'ON' if enabled else 'OFF'}"
)

# =========================================================
# STATE
# =========================================================

def empty_state():

    return {
        "watchlist": [],
        "alerts": [],
        "last_scan_date": None,
    }


def load_state():

    if not os.path.exists(STATE_FILE):
        return empty_state()

    try:

        with open(
            STATE_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):
            return empty_state()

        data.setdefault(
            "watchlist",
            [],
        )

        data.setdefault(
            "alerts",
            [],
        )

        data.setdefault(
            "last_scan_date",
            None,
        )

        return data

    except Exception:

        return empty_state()


def save_state(state):

    try:

        with open(
            STATE_FILE,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                state,
                f,
                indent=2,
                ensure_ascii=False,
            )

    except Exception:
        pass


state = load_state()

# =========================================================
# NIFTY 100
# =========================================================

@st.cache_data(
    ttl=3600,
    show_spinner=False,
)
def get_nifty100():

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64)"
        ),
        "Accept": "text/csv,*/*",
    }

    try:

        r = requests.get(
            NIFTY100_URL,
            headers=headers,
            timeout=20,
        )

        r.raise_for_status()

        df = pd.read_csv(
            __import__("io").StringIO(
                r.text
            )
        )

        if "Symbol" not in df.columns:
            raise ValueError(
                "Nifty 100 CSV me Symbol column nahi mila."
            )

        symbols = (
            df["Symbol"]
            .astype(str)
            .str.strip()
            .str.upper()
            .tolist()
        )

        symbols = [
            x
            for x in symbols
            if x
            and x != "NAN"
        ]

        return sorted(
            list(dict.fromkeys(symbols))
        )

    except Exception as e:

        st.error(
            "Nifty 100 list load nahi hui: "
            + str(e)
        )

        return []


symbols = get_nifty100()

# =========================================================
# YAHOO SYMBOL
# =========================================================

def yahoo_symbol(symbol):

    return f"{symbol}.NS"


# =========================================================
# DOWNLOAD DAILY DATA
# =========================================================

@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def get_daily_data(symbol):

    try:

        df = yf.download(
            yahoo_symbol(symbol),
            period="1y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            return pd.DataFrame()

        if isinstance(
            df.columns,
            pd.MultiIndex,
        ):

            df.columns = [
                c[0]
                for c in df.columns
            ]

        df.columns = [
            str(c).title()
            for c in df.columns
        ]

        required = [
            "Open",
            "High",
            "Low",
            "Close",
        ]

        if not all(
            c in df.columns
            for c in required
        ):
            return pd.DataFrame()

        df = df[
            required
        ].copy()

        for c in required:

            df[c] = pd.to_numeric(
                df[c],
                errors="coerce",
            )

        df = df.dropna()

        if df.empty:
            return df

        df.index = pd.to_datetime(
            df.index
        )

        return df

    except Exception:

        return pd.DataFrame()

# =========================================================
# INTRADAY DATA
# =========================================================

@st.cache_data(
    ttl=30,
    show_spinner=False,
)
def get_intraday_price(symbol):

    try:

        df = yf.download(
            yahoo_symbol(symbol),
            period="1d",
            interval="1m",
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        if df is None or df.empty:
            return None, None

        if isinstance(
            df.columns,
            pd.MultiIndex,
        ):

            df.columns = [
                c[0]
                for c in df.columns
            ]

        if "Close" not in df.columns:
            return None, None

        close = pd.to_numeric(
            df["Close"],
            errors="coerce",
        ).dropna()

        if close.empty:
            return None, None

        latest_price = float(
            close.iloc[-1]
        )

        timestamp = close.index[-1]

        return (
            latest_price,
            timestamp,
        )

    except Exception:

        return None, None

# =========================================================
# HEIKIN ASHI
# =========================================================

def heikin_ashi(df):

    if df.empty:
        return pd.DataFrame()

    ha = pd.DataFrame(
        index=df.index
    )

    ha["HA_Close"] = (
        df["Open"]
        + df["High"]
        + df["Low"]
        + df["Close"]
    ) / 4.0

    ha_open = []

    for i in range(
        len(df)
    ):

        if i == 0:

            value = (
                df["Open"].iloc[i]
                + df["Close"].iloc[i]
            ) / 2.0

        else:

            value = (
                ha_open[i - 1]
                + ha["HA_Close"].iloc[i - 1]
            ) / 2.0

        ha_open.append(
            value
        )

    ha["HA_Open"] = ha_open

    ha["HA_High"] = pd.concat(
        [
            df["High"],
            ha["HA_Open"],
            ha["HA_Close"],
        ],
        axis=1,
    ).max(axis=1)

    ha["HA_Low"] = pd.concat(
        [
            df["Low"],
            ha["HA_Open"],
            ha["HA_Close"],
        ],
        axis=1,
    ).min(axis=1)

    return ha

# =========================================================
# BOLLINGER
# =========================================================

def calculate_signal(df):

    ha = heikin_ashi(df)

    if len(ha) < BOLL_LENGTH + 2:

        return None

    ha["Middle"] = (
        ha["HA_Close"]
        .rolling(
            BOLL_LENGTH
        )
        .mean()
    )

    ha["Std"] = (
        ha["HA_Close"]
        .rolling(
            BOLL_LENGTH
        )
        .std()
    )

    ha["Upper"] = (
        ha["Middle"]
        + (
            BOLL_MULTIPLIER
            * ha["Std"]
        )
    )

    ha["Lower"] = (
        ha["Middle"]
        - (
            BOLL_MULTIPLIER
            * ha["Std"]
        )
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Use only COMPLETED daily candles.
    #
    # Yahoo daily data generally contains current
    # session data during market hours. Therefore the
    # latest row is excluded when market is open.
    # -----------------------------------------------------

    if market_open:

        completed = ha.iloc[:-1].copy()

    else:

        completed = ha.copy()

    if len(completed) < BOLL_LENGTH + 2:
        return None

    previous = completed.iloc[-2]
    current = completed.iloc[-1]

    if pd.isna(
        previous["Middle"]
    ) or pd.isna(
        current["Middle"]
    ):

        return None

    previous_below = (
        float(previous["HA_Close"])
        < float(previous["Middle"])
    )

    current_above = (
        float(current["HA_Close"])
        > float(current["Middle"])
    )

    crossed = (
        previous_below
        and current_above
    )

    if not crossed:
        return None

    candle_date = (
        pd.Timestamp(
            completed.index[-1]
        ).date()
    )

    high = float(
        current["HA_High"]
    )

    close = float(
        current["HA_Close"]
    )

    middle = float(
        current["Middle"]
    )

    return {
        "cross_date": str(
            candle_date
        ),
        "trigger_high": high,
        "ha_close": close,
        "middle": middle,
    }

# =========================================================
# DAILY SCAN
# =========================================================

def run_daily_scan():

    scan_date = str(
        today
    )

    if (
        state.get(
            "last_scan_date"
        )
        == scan_date
    ):

        return 0

    new_count = 0

    for symbol in symbols:

        df = get_daily_data(
            symbol
        )

        if df.empty:
            continue

        signal = calculate_signal(
            df
        )

        if not signal:
            continue

        cross_date = signal[
            "cross_date"
        ]

        # Same signal already present?
        already = False

        for item in state[
            "watchlist"
        ]:

            if (
                item.get("symbol")
                == symbol
                and item.get("cross_date")
                == cross_date
            ):

                already = True
                break

        if already:
            continue

        item = {
            "symbol": symbol,
            "cross_date": cross_date,
            "trigger_high": signal[
                "trigger_high"
            ],
            "ha_close": signal[
                "ha_close"
            ],
            "middle": signal[
                "middle"
            ],
            "days_watched": 0,
            "status": "WATCHING",
            "entry_date": None,
            "entry_time": None,
            "entry_price": None,
        }

        state[
            "watchlist"
        ].append(item)

        new_count += 1

    state[
        "last_scan_date"
    ] = scan_date

    save_state(
        state
    )

    return new_count

# =========================================================
# WATCH DAY CALCULATION
# =========================================================

def trading_days_after(
    start_date,
    count,
):

    d = pd.Timestamp(
        start_date
    )

    days = 0

    while days < count:

        d = d + pd.Timedelta(
            days=1
        )

        if d.weekday() < 5:

            days += 1

    return d.date()

# =========================================================
# EXPIRE OLD WATCHES
# =========================================================

def update_expired():

    changed = False

    for item in state[
        "watchlist"
    ]:

        if item.get(
            "status"
        ) != "WATCHING":
            continue

        try:

            cross = date.fromisoformat(
                item["cross_date"]
            )

        except Exception:

            continue

        expiry = trading_days_after(
            cross,
            WATCH_DAYS,
        )

        if today > expiry:

            item[
                "status"
            ] = "EXPIRED"

            changed = True

    if changed:
        save_state(
            state
        )

# =========================================================
# LIVE TRIGGER CHECK
# =========================================================

def check_live_triggers():

    if not enabled:
        return

    if not market_open:
        return

    changed = False

    for item in state[
        "watchlist"
    ]:

        if item.get(
            "status"
        ) != "WATCHING":

            continue

        symbol = item[
            "symbol"
        ]

        try:

            cross = date.fromisoformat(
                item[
                    "cross_date"
                ]
            )

        except Exception:

            continue

        expiry = trading_days_after(
            cross,
            WATCH_DAYS,
        )

        if today > expiry:
            item[
                "status"
            ] = "EXPIRED"
            changed = True
            continue

        price, timestamp = (
            get_intraday_price(
                symbol
            )
        )

        if price is None:
            continue

        trigger = float(
            item[
                "trigger_high"
            ]
        )

        if price >= trigger:

            item[
                "status"
            ] = "BUY ALERT"

            item[
                "entry_date"
            ] = str(
                today
            )

            item[
                "entry_time"
            ] = now.strftime(
                "%H:%M:%S"
            )

            item[
                "entry_price"
            ] = float(
                price
            )

            state[
                "alerts"
            ].append(
                {
                    "symbol": symbol,
                    "cross_date": item[
                        "cross_date"
                    ],
                    "trigger_high": trigger,
                    "entry_date": str(
                        today
                    ),
                    "entry_time": now.strftime(
                        "%H:%M:%S"
                    ),
                    "entry_price": float(
                        price
                    ),
                }
            )

            changed = True

    if changed:
        save_state(
            state
        )

# =========================================================
# RUN ENGINE
# =========================================================

if enabled:

    # Daily scan only once per date.
    #
    # Best practice:
    # scan completed candle after market close.
    #
    # During market hours the previous completed
    # candle is used.

    if not market_open:

        run_daily_scan()

    update_expired()

    if market_open:

        check_live_triggers()

else:

    st.warning(
        "🔴 Monitoring OFF — scanning aur trigger checking band hai."
    )

# =========================================================
# REFRESH
# =========================================================

if enabled:

    time.sleep(0.1)

    st.markdown(
        """
        <div class="small">
        Monitoring ON • App refresh ke saath active watchlist
        check hoti rahegi.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Streamlit rerun
    time.sleep(5)
    st.rerun()

# =========================================================
# SUMMARY
# =========================================================

watching = [
    x
    for x in state[
        "watchlist"
    ]
    if x.get(
        "status"
    ) == "WATCHING"
]

alerts = [
    x
    for x in state[
        "watchlist"
    ]
    if x.get(
        "status"
    ) == "BUY ALERT"
]

expired = [
    x
    for x in state[
        "watchlist"
    ]
    if x.get(
        "status"
    ) == "EXPIRED"
]

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Nifty 100",
    len(symbols),
)

c2.metric(
    "NEW / WATCHING",
    len(watching),
)

c3.metric(
    "BUY ALERT",
    len(alerts),
)

c4.metric(
    "EXPIRED",
    len(expired),
)

# =========================================================
# NEW WATCH TABLE
# =========================================================

st.subheader(
    "🟡 2-Day WATCH"
)

if watching:

    rows = []

    for item in watching:

        cross = date.fromisoformat(
            item[
                "cross_date"
            ]
        )

        expiry = trading_days_after(
            cross,
            WATCH_DAYS,
        )

        rows.append(
            {
                "Share": item[
                    "symbol"
                ],
                "Cross Date": item[
                    "cross_date"
                ],
                "Buy Trigger": round(
                    float(
                        item[
                            "trigger_high"
                        ]
                    ),
                    2,
                ),
                "HA Close": round(
                    float(
                        item[
                            "ha_close"
                        ]
                    ),
                    2,
                ),
                "Middle": round(
                    float(
                        item[
                            "middle"
                        ]
                    ),
                    2,
                ),
                "Watch Till": str(
                    expiry
                ),
                "Status": "WATCHING",
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "Abhi koi active 2-day WATCH signal nahi hai."
    )

# =========================================================
# BUY ALERT TABLE
# =========================================================

st.subheader(
    "🟢 BUY ALERT / ENTRY"
)

if alerts:

    rows = []

    for item in alerts:

        rows.append(
            {
                "Share": item[
                    "symbol"
                ],
                "Cross Date": item[
                    "cross_date"
                ],
                "Trigger High": round(
                    float(
                        item[
                            "trigger_high"
                        ]
                    ),
                    2,
                ),
                "Entry Date": item[
                    "entry_date"
                ],
                "Entry Time": item[
                    "entry_time"
                ],
                "Entry Price": round(
                    float(
                        item[
                            "entry_price"
                        ]
                    ),
                    2,
                ),
                "Status": "BUY ALERT",
            }
        )

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "Abhi koi trigger hit nahi hua."
    )

# =========================================================
# EXPIRED
# =========================================================

with st.expander(
    "Expired Signals"
):

    if expired:

        rows = []

        for item in expired:

            rows.append(
                {
                    "Share": item[
                        "symbol"
                    ],
                    "Cross Date": item[
                        "cross_date"
                    ],
                    "Trigger High": round(
                        float(
                            item[
                                "trigger_high"
                            ]
                        ),
                        2,
                    ),
                    "Status": "EXPIRED",
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.write(
            "Koi expired signal nahi hai."
        )

# =========================================================
# ALERT HISTORY
# =========================================================

with st.expander(
    "BUY Alert History"
):

    if state[
        "alerts"
    ]:

        st.dataframe(
            pd.DataFrame(
                state[
                    "alerts"
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.write(
            "Alert history empty hai."
        )

# =========================================================
# FOOTER
# =========================================================

st.caption(
    "Educational/paper alert tool. "
    "No Dhan order is placed. "
    "Market-data availability may depend on the public data provider."
)

# =========================================================
# NIFTY 100 - FULL 100 STOCK UNIVERSE
# =========================================================

NIFTY100_CSV_URL = (
    "https://nsearchives.nseindia.com/"
    "content/indices/ind_nifty100list.csv"
)


# ---------------------------------------------------------
# HARD-CODED NIFTY 100 FALLBACK
# ---------------------------------------------------------
# App पहले official NSE CSV से list लेने की कोशिश करेगा.
# अगर NSE unavailable हो, तो यह 100-symbol fallback चलेगा.
# ---------------------------------------------------------

NIFTY100_FALLBACK = [

    "ABB",
    "ADANIENSOL",
    "ADANIENT",
    "ADANIGREEN",
    "ADANIPORTS",
    "ADANIPOWER",
    "APOLLOHOSP",
    "ASIANPAINT",
    "AXISBANK",
    "BAJAJ-AUTO",

    "BAJFINANCE",
    "BAJAJFINSV",
    "BAJAJHLDNG",
    "BANKBARODA",
    "BEL",
    "BHARTIARTL",
    "BIOCON",
    "BOSCHLTD",
    "BPCL",
    "BRITANNIA",

    "CANBK",
    "CGPOWER",
    "CHOLAFIN",
    "CIPLA",
    "COALINDIA",
    "CUMMINSIND",
    "DIVISLAB",
    "DLF",
    "DMART",
    "DRREDDY",

    "EICHERMOT",
    "ETERNAL",
    "GAIL",
    "GLAND",
    "GODREJCP",
    "GRASIM",
    "HAL",
    "HCLTECH",
    "HDFCAMC",
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
    "IOC",
    "ITC",
    "JINDALSTEL",
    "JSWSTEEL",
    "JIOFIN",
    "KOTAKBANK",
    "LT",
    "LUPIN",
    "M&M",

    "MARICO",
    "MARUTI",
    "MAXHEALTH",
    "MOTHERSON",
    "MUTHOOTFIN",
    "NESTLEIND",
    "NMDC",
    "NTPC",
    "ONGC",
    "PAYTM",

    "PFC",
    "PIDILITIND",
    "PNB",
    "POWERGRID",
    "RELIANCE",
    "SBICARD",
    "SBILIFE",
    "SBIN",
    "SHRIRAMFIN",
    "SIEMENS",

    "SOLARINDS",
    "SRF",
    "SUNPHARMA",
    "TATACONSUM",
    "TATAMOTORS",
    "TATAPOWER",
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",

    "TORNTPHARM",
    "TRENT",
    "TVSMOTOR",
    "ULTRACEMCO",
    "UNIONBANK",
    "VBL",
    "VEDL",
    "WIPRO",
    "ZYDUSLIFE",
]


# =========================================================
# VALIDATE FALLBACK
# =========================================================

NIFTY100_FALLBACK = list(
    dict.fromkeys(
        NIFTY100_FALLBACK
    )
)

if len(NIFTY100_FALLBACK) != 100:

    raise RuntimeError(
        "NIFTY100_FALLBACK me exactly "
        f"100 symbols hone chahiye. "
        f"Abhi {len(NIFTY100_FALLBACK)} hain."
    )


# =========================================================
# GET NIFTY 100
# =========================================================

@st.cache_data(
    ttl=86400,
    show_spinner=False
)
def get_nifty100_symbols():

    # -----------------------------------------------------
    # 1. OFFICIAL NSE CSV
    # -----------------------------------------------------

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        # NSE session establish
        try:

            session.get(
                "https://www.nseindia.com",
                timeout=15
            )

        except Exception:

            pass


        response = session.get(
            NIFTY100_CSV_URL,
            timeout=20
        )

        response.raise_for_status()


        from io import StringIO

        df = pd.read_csv(
            StringIO(
                response.text
            )
        )


        # Find Symbol column
        symbol_col = None

        for col in df.columns:

            name = (
                str(col)
                .strip()
                .lower()
            )

            if name == "symbol":

                symbol_col = col
                break


        if symbol_col is not None:

            symbols = (
                df[symbol_col]
                .astype(str)
                .str.strip()
                .str.upper()
                .tolist()
            )


            symbols = [
                s
                for s in symbols
                if s
                and s != "NAN"
                and s != "NONE"
            ]


            symbols = list(
                dict.fromkeys(
                    symbols
                )
            )


            # Accept only a proper Nifty 100 list
            if len(symbols) >= 95:

                return symbols[:100]


    except Exception:

        pass


    # -----------------------------------------------------
    # 2. FALLBACK - FULL 100
    # -----------------------------------------------------

    return NIFTY100_FALLBACK.copy()

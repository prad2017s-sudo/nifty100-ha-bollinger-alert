# =========================================================
# NIFTY 100 LIST - FULL 100 STOCKS
# =========================================================

NIFTY100_CSV_URL = (
    "https://nsearchives.nseindia.com/"
    "content/indices/ind_nifty100list.csv"
)


# =========================================================
# NIFTY 100 FALLBACK
# =========================================================

NIFTY100_FALLBACK = [

    # -------------------------
    # NIFTY 50
    # -------------------------

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
    "CIPLA",
    "COALINDIA",
    "DRREDDY",
    "EICHERMOT",
    "ETERNAL",
    "GRASIM",
    "HCLTECH",
    "HDFCBANK",
    "HDFCLIFE",
    "HINDALCO",
    "HINDUNILVR",
    "ICICIBANK",
    "INDIGO",
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
    "TATASTEEL",
    "TCS",
    "TECHM",
    "TITAN",
    "TRENT",
    "ULTRACEMCO",
    "WIPRO",


    # -------------------------
    # NIFTY NEXT 50
    # -------------------------

    "ABB",
    "ADANIENSOL",
    "ADANIGREEN",
    "ADANIPOWER",
    "AMBUJACEM",
    "BAJAJHLDNG",
    "BANKBARODA",
    "BPCL",
    "BRITANNIA",
    "BOSCHLTD",
    "CANBK",
    "CGPOWER",
    "CHOLAFIN",
    "CUMMINSIND",
    "DIVISLAB",
    "DLF",
    "DMART",
    "GAIL",
    "GODREJCP",
    "HAL",
    "HINDZINC",
    "IOC",
    "IRFC",
    "JINDALSTEL",
    "MOTHERSON",
    "MUTHOOTFIN",
    "PIDILITIND",
    "PFC",
    "PNB",
    "SIEMENS",
    "SOLARINDS",
    "SRF",
    "TATAMOTORS",
    "TATAPOWER",
    "TORNTPHARM",
    "TVSMOTOR",
    "UNIONBANK",
    "VBL",
    "VEDL",
    "ZYDUSLIFE",
    "POLYCAB",
    "POWERINDIA",
    "VAML",
    "IDEA",
    "LICI",
    "HDFCAMC",
    "INDUSINDBK",
    "MARICO",
    "M&MFIN",
]


# =========================================================
# REMOVE DUPLICATES
# =========================================================

NIFTY100_FALLBACK = list(
    dict.fromkeys(
        NIFTY100_FALLBACK
    )
)


# =========================================================
# GET NIFTY 100 SYMBOLS
# =========================================================

@st.cache_data(
    ttl=86400,
    show_spinner=False
)
def get_nifty100_symbols():

    # -----------------------------------------------------
    # 1. OFFICIAL NSE NIFTY 100 CSV
    # -----------------------------------------------------

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        # Create NSE session/cookies
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

            if (
                str(col)
                .strip()
                .lower()
                == "symbol"
            ):

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


            # Proper Nifty 100 response
            if len(symbols) >= 95:

                return symbols[:100]


    except Exception:

        pass


    # -----------------------------------------------------
    # 2. EXISTING NSE API
    # -----------------------------------------------------

    try:

        session = requests.Session()

        session.headers.update(
            HEADERS
        )

        try:

            session.get(
                "https://www.nseindia.com",
                timeout=15
            )

        except Exception:

            pass


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

                symbols.append(
                    symbol
                )


        symbols = list(
            dict.fromkeys(
                symbols
            )
        )


        if len(symbols) >= 95:

            return symbols[:100]


    except Exception:

        pass


    # -----------------------------------------------------
    # 3. FINAL FALLBACK
    # -----------------------------------------------------

    return NIFTY100_FALLBACK.copy()

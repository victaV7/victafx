import os
import time
import threading
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# =========================================================
# VIC FX SIGNALS - BIG MOVE INTRADAY
# =========================================================

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
]

# =========================================================
# TIMEFRAMES
# =========================================================

TIMEFRAMES = {
    "MONTHLY": "1month",
    "WEEKLY": "1week",
    "DAILY": "1day",
    "4H": "4h",
    "1H": "1h",
    "15M": "15min",
    "5M": "5min",
}

OUTPUT_SIZE = {
    "1month": 80,
    "1week": 120,
    "1day": 180,
    "4h": 250,
    "1h": 250,
    "15min": 250,
    "5min": 250,
}

# =========================================================
# STRATEGY SETTINGS
# =========================================================

RSI_PERIOD = 14

FAST_EMA = 20
SLOW_EMA = 50
ATR_PERIOD = 14

# Your 1:2 RR
RR = 2.0

# Your 0.5R protection
PROTECT_R = 0.5

ZONE_LOOKBACK = 40

# Minimum quality score for BIG MOVE signal
MIN_SIGNAL_SCORE = 7

# API cache
CACHE_SECONDS = 45

data_cache = {}

latest_market = {
    "status": "starting",
    "signals": [],
}

last_signals = {}


# =========================================================
# LOGGING
# =========================================================

def log(message):
    now = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print(
        f"[{now} UTC] {message}",
        flush=True
    )


# =========================================================
# PRICE ROUNDING
# =========================================================

def round_price(pair, price):

    if "JPY" in pair:
        return round(price, 3)

    return round(price, 5)


# =========================================================
# TWELVE DATA
# =========================================================

def get_batch_data(interval, outputsize):

    if not API_KEY:
        return {}

    cache_key = f"{interval}:{outputsize}"

    cached = data_cache.get(cache_key)

    if cached:

        saved_time, saved_data = cached

        if time.time() - saved_time < CACHE_SECONDS:
            return saved_data

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": ",".join(PAIRS),
        "interval": interval,
        "outputsize": outputsize,
        "apikey": API_KEY,
        "order": "asc",
        "timezone": "UTC",
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        raw = response.json()

    except Exception as exc:

        log(
            f"DATA ERROR {interval}: {exc}"
        )

        return {}

    result = {}

    if not isinstance(raw, dict):
        return result

    for pair in PAIRS:

        item = raw.get(pair)

        if not isinstance(item, dict):
            continue

        values = item.get(
            "values",
            []
        )

        candles = []

        for row in values:

            try:

                candles.append({
                    "datetime": row.get(
                        "datetime"
                    ),
                    "open": float(
                        row["open"]
                    ),
                    "high": float(
                        row["high"]
                    ),
                    "low": float(
                        row["low"]
                    ),
                    "close": float(
                        row["close"]
                    ),
                })

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue

        if candles:
            result[pair] = candles

    data_cache[cache_key] = (
        time.time(),
        result
    )

    return result


# =========================================================
# EMA
# =========================================================

def ema(values, period):

    if len(values) < period:
        return None

    value = sum(
        values[:period]
    ) / period

    multiplier = 2.0 / (
        period + 1
    )

    for price in values[period:]:

        value = (
            (price - value)
            * multiplier
        ) + value

    return value


# =========================================================
# RSI
# =========================================================

def rsi(
    closes,
    period=RSI_PERIOD
):

    if len(closes) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(
        1,
        len(closes)
    ):

        change = (
            closes[i]
            - closes[i - 1]
        )

        gains.append(
            max(change, 0.0)
        )

        losses.append(
            max(-change, 0.0)
        )

    avg_gain = (
        sum(gains[:period])
        / period
    )

    avg_loss = (
        sum(losses[:period])
        / period
    )

    for i in range(
        period,
        len(gains)
    ):

        avg_gain = (
            (
                avg_gain
                * (period - 1)
            )
            + gains[i]
        ) / period

        avg_loss = (
            (
                avg_loss
                * (period - 1)
            )
            + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs_value = (
        avg_gain
        / avg_loss
    )

    return (
        100.0
        - (
            100.0
            / (1.0 + rs_value)
        )
    )


# =========================================================
# ATR
# =========================================================

def atr(
    candles,
    period=ATR_PERIOD
):

    if len(candles) < period + 1:
        return None

    ranges = []

    for i in range(
        1,
        len(candles)
    ):

        current = candles[i]
        previous = candles[i - 1]

        true_range = max(
            current["high"]
            - current["low"],

            abs(
                current["high"]
                - previous["close"]
            ),

            abs(
                current["low"]
                - previous["close"]
            )
        )

        ranges.append(
            true_range
        )

    if len(ranges) < period:
        return None

    return sum(
        ranges[-period:]
    ) / period


# =========================================================
# BULLISH STRUCTURE
# =========================================================

def bullish_structure(candles):

    if len(candles) < 20:
        return False

    recent = candles[-20:]

    first = recent[:10]
    second = recent[10:]

    first_high = max(
        x["high"]
        for x in first
    )

    second_high = max(
        x["high"]
        for x in second
    )

    first_low = min(
        x["low"]
        for x in first
    )

    second_low = min(
        x["low"]
        for x in second
    )

    return (
        second_high > first_high
        and
        second_low > first_low
    )


# =========================================================
# BEARISH STRUCTURE
# =========================================================

def bearish_structure(candles):

    if len(candles) < 20:
        return False

    recent = candles[-20:]

    first = recent[:10]
    second = recent[10:]

    first_high = max(
        x["high"]
        for x in first
    )

    second_high = max(
        x["high"]
        for x in second
    )

    first_low = min(
        x["low"]
        for x in first
    )

    second_low = min(
        x["low"]
        for x in second
    )

    return (
        second_high < first_high
        and
        second_low < first_low
    )


# =========================================================
# TIMEFRAME DIRECTION
# =========================================================

def timeframe_direction(candles):

    if len(candles) < (
        SLOW_EMA + 5
    ):

        return "NEUTRAL"

    closes = [
        x["close"]
        for x in candles
    ]

    fast = ema(
        closes,
        FAST_EMA
    )

    slow = ema(
        closes,
        SLOW_EMA
    )

    price = closes[-1]

    if (
        fast is None
        or slow is None
    ):

        return "NEUTRAL"

    if (
        fast > slow
        and price > fast
        and bullish_structure(candles)
    ):

        return "BULLISH"

    if (
        fast < slow
        and price < fast
        and bearish_structure(candles)
    ):

        return "BEARISH"

    return "NEUTRAL"


# =========================================================
# DEMAND ZONE
# =========================================================

def find_demand_zone(candles):

    if len(candles) < (
        ZONE_LOOKBACK
    ):

        return None

    current_atr = atr(candles)

    if not current_atr:
        return None

    recent = candles[
        -ZONE_LOOKBACK:
    ]

    for i in range(
        len(recent) - 4,
        0,
        -1
    ):

        candle = recent[i]

        body = abs(
            candle["close"]
            - candle["open"]
        )

        if body < (
            current_atr * 0.8
        ):

            continue

        if (
            candle["close"]
            >= candle["open"]
        ):

            continue

        following = recent[
            i + 1:i + 4
        ]

        if not following:
            continue

        move = (
            max(
                x["close"]
                for x in following
            )
            - candle["low"]
        )

        if move >= (
            current_atr * 0.8
        ):

            return {
                "low": candle["low"],
                "high": max(
                    candle["open"],
                    candle["close"]
                ),
            }

    return None


# =========================================================
# SUPPLY ZONE
# =========================================================

def find_supply_zone(candles):

    if len(candles) < (
        ZONE_LOOKBACK
    ):

        return None

    current_atr = atr(candles)

    if not current_atr:
        return None

    recent = candles[
        -ZONE_LOOKBACK:
    ]

    for i in range(
        len(recent) - 4,
        0,
        -1
    ):

        candle = recent[i]

        body = abs(
            candle["close"]
            - candle["open"]
        )

        if body < (
            current_atr * 0.8
        ):

            continue

        if (
            candle["close"]
            <= candle["open"]
        ):

            continue

        following = recent[
            i + 1:i + 4
        ]

        if not following:
            continue

        move = (
            candle["high"]
            - min(
                x["close"]
                for x in following
            )
        )

        if move >= (
            current_atr * 0.8
        ):

            return {
                "low": min(
                    candle["open"],
                    candle["close"]
                ),
                "high": candle["high"],
            }

    return None


# =========================================================
# 15 MINUTE CONFIRMATION
# =========================================================

def fifteen_minute_confirmation(
    candles,
    bias
):

    if len(candles) < 50:
        return False

    value = rsi([
        x["close"]
        for x in candles
    ])

    if value is None:
        return False

    if bias == "BULLISH":

        return (
            45 <= value <= 68
        )

    if bias == "BEARISH":

        return (
            32 <= value <= 55
        )

    return False


# =========================================================
# 5 MINUTE ENTRY
# =========================================================

def five_minute_entry(
    candles,
    bias
):

    if len(candles) < 60:
        return None

    value = rsi([
        x["close"]
        for x in candles
    ])

    current_atr = atr(
        candles
    )

    if (
        value is None
        or current_atr is None
    ):

        return None

    current = candles[-1]
    previous = candles[-2]

    # -----------------------------------------------------
    # BUY
    # -----------------------------------------------------

    if bias == "BULLISH":

        if (
            current["close"]
            > current["open"]

            and

            previous["close"]
            < previous["open"]

            and

            current["close"]
            > previous["high"]

            and

            50 <= value <= 70
        ):

            return {
                "direction": "BUY",
                "entry": current["close"],
                "atr": current_atr,
                "rsi": value,
            }

    # -----------------------------------------------------
    # SELL
    # -----------------------------------------------------

    if bias == "BEARISH":

        if (
            current["close"]
            < current["open"]

            and

            previous["close"]
            > previous["open"]

            and

            current["close"]
            < previous["low"]

            and

            30 <= value <= 50
        ):

            return {
                "direction": "SELL",
                "entry": current["close"],
                "atr": current_atr,
                "rsi": value,
            }

    return None


# =========================================================
# TOP-DOWN BIAS
# =========================================================

def top_down_bias(
    pair_data
):

    directions = {}

    for name in (
        "MONTHLY",
        "WEEKLY",
        "DAILY",
        "4H"
    ):

        directions[name] = (
            timeframe_direction(
                pair_data.get(
                    name,
                    []
                )
            )
        )

    bullish_count = sum(
        value == "BULLISH"
        for value in directions.values()
    )

    bearish_count = sum(
        value == "BEARISH"
        for value in directions.values()
    )

    if bullish_count >= 3:

        bias = "BULL

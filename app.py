import os
import time
import threading
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template

app = Flask(__name__)

# =========================================================
# VIC FX SIGNALS
# BIG MOVE INTRADAY
# =========================================================

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD"
]

# ---------------------------------------------------------
# TIMEFRAMES
# ---------------------------------------------------------

TIMEFRAMES = {
    "MONTHLY": "1month",
    "WEEKLY": "1week",
    "DAILY": "1day",
    "4H": "4h",
    "1H": "1h",
    "15M": "15min",
    "5M": "5min"
}

# ---------------------------------------------------------
# STRATEGY SETTINGS
# ---------------------------------------------------------

RSI_PERIOD = 14

RR = 2.0

# Your existing protection rule
PROTECT_R = 0.5

# Do not scalp
MIN_SIGNAL_SCORE = 7

# Supply / demand settings
ZONE_LOOKBACK = 40
ZONE_ATR_MULTIPLIER = 1.5

# Trend settings
FAST_EMA = 20
SLOW_EMA = 50

# ATR
ATR_PERIOD = 14

# Number of candles requested
OUTPUT_SIZES = {
    "1month": 80,
    "1week": 120,
    "1day": 180,
    "4h": 250,
    "1h": 250,
    "15min": 250,
    "5min": 250
}

# Prevent repeated alerts for same setup
last_signals = {}

# Cache market data so the website is not constantly hitting API
data_cache = {}

CACHE_SECONDS = 45


# =========================================================
# BASIC HELPERS
# =========================================================

def log(message):
    print(
        f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] "
        f"{message}",
        flush=True
    )


def safe_float(value):
    try:
        return float(value)
    except:
        return None


def pip_size(pair):
    if "JPY" in pair:
        return 0.01
    return 0.0001


# =========================================================
# TWELVE DATA
# =========================================================

def get_batch_data(interval, outputsize):
    """
    Fetch all five pairs for one timeframe.

    Twelve Data supports comma-separated symbols in a batch
    time-series request.
    """

    if not API_KEY:
        return {}

    cache_key = f"{interval}_{outputsize}"

    if cache_key in data_cache:
        saved_time, saved_data = data_cache[cache_key]

        if time.time() - saved_time < CACHE_SECONDS:
            return saved_data

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": ",".join(PAIRS),
        "interval": interval,
        "outputsize": outputsize,
        "apikey": API_KEY,
        "order": "asc",
        "timezone": "UTC"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()

        raw = response.json()

        # -------------------------------------------------
        # Twelve Data can return:
        # {"EUR/USD": {...}, "GBP/USD": {...}}
        # -------------------------------------------------

        result = {}

        if isinstance(raw, dict):

            for pair in PAIRS:

                pair_data = raw.get(pair)

                if not pair_data:
                    continue

                if not isinstance(pair_data, dict):
                    continue

                if "values" not in pair_data:
                    continue

                candles = []

                for item in pair_data["values"]:

                    try:
                        candles.append({
                            "datetime": item.get("datetime"),
                            "open": float(item["open"]),
                            "high": float(item["high"]),
                            "low": float(item["low"]),
                            "close": float(item["close"])
                        })
                    except:
                        continue

                if candles:
                    result[pair] = candles

        data_cache[cache_key] = (
            time.time(),
            result
        )

        return result

    except Exception as e:
        log(f"DATA ERROR {interval}: {e}")
        return {}


# =========================================================
# INDICATORS
# =========================================================

def calculate_ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    ema = sum(values[:period]) / period

    for price in values[period:]:
        ema = (
            (price - ema) * multiplier
        ) + ema

    return ema


def calculate_rsi(closes, period=14):

    if len(closes) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]

        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):

        avg_gain = (
            (avg_gain * (period - 1)) + gains[i]
        ) / period

        avg_loss = (
            (avg_loss * (period - 1)) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def calculate_atr(candles, period=14):

    if len(candles) < period + 1:
        return None

    true_ranges = []

    for i in range(1, len(candles)):

        current = candles[i]
        previous = candles[i - 1]

        tr1 = current["high"] - current["low"]

        tr2 = abs(
            current["high"] - previous["close"]
        )

        tr3 = abs(
            current["low"] - previous["close"]
        )

        true_range = max(
            tr1,
            tr2,
            tr3
        )

        true_ranges.append(true_range)

    if len(true_ranges) < period:
        return None

    return sum(true_ranges[-period:]) / period


# =========================================================
# MARKET STRUCTURE
# =========================================================

def bullish_structure(candles):

    if len(candles) < 20:
        return False

    recent = candles[-20:]

    highs = [x["high"] for x in recent]
    lows = [x["low"] for x in recent]

    midpoint = len(recent) // 2

    first_half_high = max(highs[:midpoint])
    second_half_high = max(highs[midpoint:])

    first_half_low = min(lows[:midpoint])
    second_half_low = min(lows[midpoint:])

    return (
        second_half_high > first_half_high
        and
        second_half_low > first_half_low
    )


def bearish_structure(candles):

    if len(candles) < 20:
        return False

    recent = candles[-20:]

    highs = [x["high"] for x in recent]
    lows = [x["low"] for x in recent]

    midpoint = len(recent) // 2

    first_half_high = max(highs[:midpoint])
    second_half_high = max(highs[midpoint:])

    first_half_low = min(lows[:midpoint])
    second_half_low = min(lows[midpoint:])

    return (
        second_half_high < first_half_high
        and
        second_half_low < first_half_low
    )


# =========================================================
# SUPPLY / DEMAND
# =========================================================

def find_demand_zone(candles):

    if len(candles) < ZONE_LOOKBACK:
        return None

    atr = calculate_atr(candles, ATR_PERIOD)

    if not atr:
        return None

    recent = candles[-ZONE_LOOKBACK:]

    # Find a strong bearish candle followed by bullish movement.
    for i in range(len(recent) - 5, 1, -1):

        candle = recent[i]

        body = abs(
            candle["close"] - candle["open"]
        )

        if body > atr * ZONE_ATR_MULTIPLIER:

            if candle["close"] < candle["open"]:

                following = recent[i + 1:i + 4]

                if following:

                    bullish_move = (
                        max(x["close"] for x in following)
                        - candle["low"]
                    )

                    if bullish_move > atr * 0.8:

                        return {
                            "low": candle["low"],
                            "high": max(
                                candle["open"],
                                candle["close"]
                            )
                        }

    return None


def find_supply_zone(candles):

    if len(candles) < ZONE_LOOKBACK:
        return None

    atr = calculate_atr(candles, ATR_PERIOD)

    if not atr:
        return None

    recent = candles[-ZONE_LOOKBACK:]

    for i in range(len(recent) - 5, 1, -1):

        candle = recent[i]

        body = abs(
            candle["close"] - candle["open"]
        )

        if body > atr * ZONE_ATR_MULTIPLIER:

            if candle["close"] > candle["open"]:

                following = recent[i + 1:i + 4]

                if following:

                    bearish_move = (
                        candle["high"]
                        - min(
                            x["close"]
                            for x in following
                        )
                    )

                    if bearish_move > atr * 0.8:

                        return {
                            "low": min(
                                candle["open"],
                                candle["close"]
                            ),
                            "high": candle["high"]
                        }

    return None


def price_inside_zone(price, zone):

    if not zone:
        return False

    return (
        zone["low"] <= price <= zone["high"]
    )


# =========================================================
# HIGHER TIMEFRAME BIAS
# =========================================================

def timeframe_direction(candles):

    if len(candles) < SLOW_EMA + 5:
        return "NEUTRAL"

    closes = [
        x["close"]
        for x in candles
    ]

    fast = calculate_ema(
        closes,
        FAST_EMA
    )

    slow = calculate_ema(
        closes,
        SLOW_EMA
    )

    if fast is None or slow is None:
        return "NEUTRAL"

    price = closes[-1]

    bull_structure = bullish_structure(candles)
    bear_structure = bearish_structure(candles)

    if (
        fast > slow
        and price > fast
        and bull_structure
    ):
        return "BULLISH"

    if (
        fast < slow
        and price < fast
        and bear_structure
    ):
        return "BEARISH"

    return "NEUTRAL"


def get_top_down_bias(pair_data):

    directions = {}

    for name in [
        "MONTHLY",
        "WEEKLY",
        "DAILY",
        "4H"
    ]:

        candles = pair_data.get(name, [])

        directions[name] = timeframe_direction(
            candles
        )

    bullish = sum(
        1
        for x in directions.values()
        if x == "BULLISH"
    )

    bearish = sum(
        1
        for x in directions.values()
        if x == "BEARISH"
    )

    if bullish >= 3:
        final_bias = "BULLISH"

    elif bearish >= 3:
        final_bias = "BEARISH"

    else:
        final_bias = "NEUTRAL"

    return final_bias, directions


# =========================================================
# 1H ACTIONABLE STRUCTURE
# =========================================================

def actionable_1h(pair_data, bias):

    candles = pair_data.get("1H", [])

    if len(candles) < 60:
        return False

    if bias == "BULLISH":
        return bullish_structure(candles)

    if bias == "BEARISH":
        return bearish_structure(candles)

    return False


# =========================================================
# 15M CONFIRMATION
# =========================================================

def fifteen_minute_confirmation(pair_data, bias):

    candles = pair_data.get("15M", [])

    if len(candles) < 50:
        return False

    closes = [
        x["close"]
        for x in candles
    ]

    rsi = calculate_rsi(
        closes,
        RSI_PERIOD
    )

    if rsi is None:
        return False

    if bias == "BULLISH":

        # RSI is not required to be deeply oversold.
        # We want momentum to recover without buying
        # an extreme spike.

        return 45 <= rsi <= 68

    if bias == "BEARISH":

        return 32 <= rsi <= 55

    return False


# =========================================================
# 5M ENTRY
# =========================================================

def five_minute_signal(pair_data, bias):

    candles = pair_data.get("5M", [])

    if len(candles) < 60:
        return None

    closes = [
        x["close"]
        for x in candles
    ]

    rsi = calculate_rsi(
        closes,
        RSI_PERIOD
    )

    atr = calculate_atr(
        candles,
        ATR_PERIOD
    )

    if rsi is None or atr is None:
        return None

    current = candles[-1]
    previous = candles[-2]

    # -----------------------------------------------------
    # BUY
    # -----------------------------------------------------

    if bias == "BULLISH":

        bullish_candle = (
            current["close"] > current["open"]
        )

        previous_bearish = (
            previous["close"] < previous["open"]
        )

        momentum = (
            current["close"] > previous["high"]
        )

        rsi_ok = (
            50 <= rsi <= 70
        )

        if (
            bullish_candle
            and previous_bearish
            and momentum
            and rsi_ok
        ):

            return {
                "direction": "BUY",
                "price": current["close"],
                "atr": atr,
                "rsi": rsi
            }

    # -----------------------------------------------------
    # SELL
    # -----------------------------------------------------

    if bias == "BEARISH":

        bearish_candle = (
            current["close"] < current["open"]
        )

        previous_bullish = (
            previous["close"] > previous["open"]
        )

        momentum = (
            current["close"] < previous["low"]
        )

        rsi_ok = (
            30 <= rsi <= 50
        )

        if (
            bearish_candle
            and previous_bullish
            and momentum
            and rsi_ok
        ):

            return {
                "direction": "SELL",
                "price": current["close"],
                "atr": atr,
                "rsi": rsi
            }

    return None


# =========================================================
# BUILD TRADE
# =========================================================

def build_trade(pair, pair_data, entry_signal):

    direction = entry_signal["direction"]

    entry = entry_signal["price"]

    atr = entry_signal["atr"]

    # Use 5M ATR for a realistic intraday stop.
    stop_distance = atr * 1.5

    # Avoid an unrealistically tiny stop.
    minimum_distance = pip_size(pair) * 15

    stop_distance = max(
        stop_distance,
        minimum_distance
    )

    if direction == "BUY":

        sl = entry - stop_distance

        tp = entry + (
            stop_distance * RR
        )

    else:

        sl = entry + stop_distance

        tp = entry - (
            stop_distance * RR
        )

    return {
        "pair": pair,
        "direction": direction,
        "entry": round_price(pair, entry),
        "stop_loss": round_price(pair, sl),
        "take_profit": round_price(pair, tp),
        "risk_distance": round_price(
            pair,
            stop_distance
        ),
        "rr": RR,
        "protect_at_r": PROTECT_R,
        "rsi_5m": round(
            entry_signal["rsi"],
            2
        )
    }


def round_price(pair, price):

    if "JPY" in pair:
        return round(price, 3)

    return round(price, 5)


# =========================================================
# SIGNAL SCORE
# =========================================================

def calculate_score(
    pair_data,
    bias,
    directions,
    trade
):

    score = 0
    reasons = []

    # -----------------------------------------------------
    # Higher timeframe alignment
    # -----------------------------------------------------

    if bias in ["BULLISH", "BEARISH"]:

        score += 2
        reasons.append(
            "Higher-timeframe bias confirmed"
        )

    # Weekly
    if directions.get("WEEKLY") == bias:

        score += 1
        reasons.append(
            "Weekly agrees"
        )

    # Daily
    if directions.get("DAILY") == bias:

        score += 1
        reasons.append(
            "Daily agrees"
        )

    # 4H
    if directions.get("4H") == bias:

        score += 1
        reasons.append(
            "4H agrees"
        )

    # 1H structure
    if actionable_1h(
        pair_data,
        bias
    ):

        score += 1
        reasons.append(
            "1H structure confirmed"
        )

    # 15M
    if fifteen_minute_confirmation(
        pair_data,
        bias
    ):

        score += 1
        reasons.append(
            "15M confirmation"
        )

    # 5M entry
    score += 1

    reasons.append(
        "5M entry confirmed"
    )

    # RSI
    if 40 <= trade["rsi_5m"] <= 70:

        score += 1
        reasons.append(
            "RSI supports momentum"
        )

    return score, reasons


# =========================================================
# ANALYZE PAIR
# =========================================================

def analyze_pair(pair, all_data):

    pair_data = {}

    for timeframe_name, interval in TIMEFRAMES.items():

        timeframe_data = all_data.get(
            interval,
            {}
        )

        pair_data[timeframe_name] = (
            timeframe_data.get(pair, [])
        )

    # Need enough 5M data
    if len(pair_data["5M"]) < 60:
        return {
            "pair": pair,
            "signal": "WAIT",
            "reason": "Not enough 5M data"
        }

    bias, directions = get_top_down_bias(
        pair_data
    )

    if bias == "NEUTRAL":

        return {
            "pair": pair,
            "signal": "WAIT",
            "bias": bias,
            "timeframes": directions,
            "reason": "Higher timeframes not aligned"
        }

    # -----------------------------------------------------
    # 1H
    # -----------------------------------------------------

    if not actionable_1h(
        pair_data,
        bias
    ):

        return {
            "pair": pair,
            "signal": "WAIT",
            "bias": bias,
            "timeframes": directions,
            "reason": "1H structure not confirmed"
        }

    # -----------------------------------------------------
    # 15M
    # -----------------------------------------------------

    if not fifteen_minute_confirmation(
        pair_data,
        bias
    ):

        return {
            "pair": pair,
            "signal": "WAIT",
            "bias": bias,
            "timeframes": directions,
            "reason": "15M confirmation missing"
        }

    # -----------------------------------------------------
    # Supply / Demand
    # -----------------------------------------------------

    if bias == "BULLISH":

        zone = find_demand_zone(
            pair_data["1H"]
        )

    else:

        zone = find_supply_zone(
            pair_data["1H"]
        )

    if not zone:

        return {
            "pair": pair,
            "signal": "WAIT",
            "bias": bias,
            "timeframes": directions,
            "reason": "No strong supply/demand zone"
        }

    current_price = pair_data["5M"][-1]["close"]

    # Price should be reasonably close to the zone.
    zone_distance = abs(
        current_price
        - (
            (zone["low"] + zone["high"])
         

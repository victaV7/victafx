import os
import time
import threading
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# =========================================================
# VIC FX SIGNALS - BIG MOVE INTRADAY
# =========================================================

API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CHF",
    "USD/CAD",
    "AUD/USD",
    "NZD/USD",
    "EUR/GBP",
    "EUR/JPY",
    "GBP/JPY",
    "AUD/JPY",
    "NZD/JPY",
]

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

RSI_PERIOD = 14
FAST_EMA = 20
SLOW_EMA = 50
ATR_PERIOD = 14
RR = 2.0
PROTECT_R = 0.5
ZONE_LOOKBACK = 40
MIN_SIGNAL_SCORE = 7
SL_ATR_MULTIPLIER = 1.0
CACHE_SECONDS = 45
SCAN_SECONDS = 60

cache = {}
last_scan = 0.0
scan_lock = threading.Lock()

latest_market = {
    "status": "starting",
    "signals": [],
    "pairs": [],
    "updated": None,
    "message": "Starting market scanner...",
}

# Free-plan safeguards: Twelve Data Basic is 8 credits/minute and 800/day.
# We use a conservative in-memory budget and keep chart requests cached.
API_LOCK = threading.Lock()
api_usage_minute = {"key": None, "credits": 0}
api_usage_day = {"key": None, "credits": 0}
CHART_DAILY_LIMIT = 180
chart_daily_usage = {"key": None, "credits": 0}
market_store = {interval: {} for interval in TIMEFRAMES.values()}
chart_cache = {}
CHART_CACHE_SECONDS = 900
FREE_DAILY_BUDGET = 760  # leave headroom below the documented 800/day
SCAN_INTERVAL_SECONDS = 3 * 60 * 60  # full sweep plus staging is about 3h14m


# =========================================================
# HELPERS
# =========================================================

def log(message):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now} UTC] {message}", flush=True)


def round_price(pair, price):
    return round(price, 3 if "JPY" in pair else 5)


def closes(candles):
    return [c["close"] for c in candles]


# =========================================================
# TWELVE DATA
# =========================================================

def _quota_key():
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M"), now.strftime("%Y-%m-%d")


def _can_spend(credits, purpose="scan"):
    minute_key, day_key = _quota_key()
    if api_usage_minute["key"] != minute_key:
        api_usage_minute.update(key=minute_key, credits=0)
    if api_usage_day["key"] != day_key:
        api_usage_day.update(key=day_key, credits=0)
    if api_usage_minute["credits"] + credits > 8:
        return False, "Twelve Data free-plan limit is 8 credits/minute; retry next minute"
    if api_usage_day["credits"] + credits > FREE_DAILY_BUDGET:
        return False, "Local safety limit reached for today's Twelve Data budget"
    if purpose == "chart":
        if chart_daily_usage["key"] != day_key:
            chart_daily_usage.update(key=day_key, credits=0)
        if chart_daily_usage["credits"] + credits > CHART_DAILY_LIMIT:
            return False, "Chart refresh budget reached for today; cached candles remain available"
    return True, ""


def get_data(interval, outputsize, symbols=None, purpose="scan"):
    """Fetch one small batch, respecting the free-plan 8-credit/minute cap."""
    if not API_KEY:
        return {}
    symbols = list(symbols or PAIRS)
    if not symbols:
        return {}
    cache_key = f"{interval}:{outputsize}:{','.join(symbols)}"
    old = cache.get(cache_key)
    ttl = CHART_CACHE_SECONDS if purpose == "chart" else 60
    if old and time.time() - old[0] < ttl:
        return old[1]

    with API_LOCK:
        allowed, reason = _can_spend(len(symbols), purpose)
        if not allowed:
            log(f"API THROTTLE {interval}: {reason}")
            return {}
        # Reserve locally before the request so simultaneous chart/scanner calls cannot overspend.
        minute_key, day_key = _quota_key()
        api_usage_minute["credits"] += len(symbols)
        api_usage_day["credits"] += len(symbols)
        if purpose == "chart":
            chart_daily_usage["credits"] += len(symbols)

    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": ",".join(symbols),
        "interval": interval,
        "outputsize": min(int(outputsize), 250),
        "apikey": API_KEY,
        "order": "asc",
        "timezone": "UTC",
    }
    try:
        response = requests.get(url, params=params, timeout=25)
        raw = response.json()
        if response.status_code == 429 or (isinstance(raw, dict) and raw.get("code") == 429):
            log(f"DATA ERROR {interval}: Twelve Data returned HTTP 429. Request is throttled; cached data will be kept.")
            return {}
        response.raise_for_status()
    except Exception as exc:
        log(f"DATA ERROR {interval}: {exc}")
        return {}

    result = {}
    if not isinstance(raw, dict):
        return result
    for pair in symbols:
        item = raw.get(pair)
        if not isinstance(item, dict) or not item.get("values"):
            continue
        candles = []
        for row in item.get("values", []):
            try:
                candles.append({
                    "datetime": row.get("datetime"),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
        if candles:
            result[pair] = candles
    cache[cache_key] = (time.time(), result)
    return result


# =========================================================
# INDICATORS
# =========================================================

def ema(values, period):
    if len(values) < period:
        return None

    value = sum(values[:period]) / period
    multiplier = 2.0 / (period + 1)

    for price in values[period:]:
        value = ((price - value) * multiplier) + value

    return value


def rsi(values, period=RSI_PERIOD):
    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def atr(candles, period=ATR_PERIOD):
    if len(candles) < period + 1:
        return None

    ranges = []
    for i in range(1, len(candles)):
        current = candles[i]
        previous = candles[i - 1]
        tr = max(
            current["high"] - current["low"],
            abs(current["high"] - previous["close"]),
            abs(current["low"] - previous["close"]),
        )
        ranges.append(tr)

    if len(ranges) < period:
        return None

    return sum(ranges[-period:]) / period


# =========================================================
# MARKET STRUCTURE
# =========================================================

def bullish_structure(candles):
    if len(candles) < 20:
        return False

    first = candles[-20:-10]
    second = candles[-10:]

    return (
        max(c["high"] for c in second) > max(c["high"] for c in first)
        and min(c["low"] for c in second) > min(c["low"] for c in first)
    )


def bearish_structure(candles):
    if len(candles) < 20:
        return False

    first = candles[-20:-10]
    second = candles[-10:]

    return (
        max(c["high"] for c in second) < max(c["high"] for c in first)
        and min(c["low"] for c in second) < min(c["low"] for c in first)
    )


def timeframe_direction(candles):
    if len(candles) < SLOW_EMA + 5:
        return "NEUTRAL"

    values = closes(candles)
    fast = ema(values, FAST_EMA)
    slow = ema(values, SLOW_EMA)
    price = values[-1]

    if fast is None or slow is None:
        return "NEUTRAL"

    if fast > slow and price > fast and bullish_structure(candles):
        return "BULLISH"

    if fast < slow and price < fast and bearish_structure(candles):
        return "BEARISH"

    return "NEUTRAL"


# =========================================================
# SUPPLY / DEMAND
# =========================================================

def find_demand_zone(candles):
    if len(candles) < ZONE_LOOKBACK:
        return None

    current_atr = atr(candles)
    if not current_atr:
        return None

    recent = candles[-ZONE_LOOKBACK:]

    for i in range(len(recent) - 4, 0, -1):
        candle = recent[i]
        body = abs(candle["close"] - candle["open"])

        if body < current_atr * 0.8:
            continue
        if candle["close"] >= candle["open"]:
            continue

        following = recent[i + 1:i + 4]
        if not following:
            continue

        move = max(c["close"] for c in following) - candle["low"]
        if move >= current_atr * 0.8:
            return {
                "low": candle["low"],
                "high": max(candle["open"], candle["close"]),
            }

    return None


def find_supply_zone(candles):
    if len(candles) < ZONE_LOOKBACK:
        return None

    current_atr = atr(candles)
    if not current_atr:
        return None

    recent = candles[-ZONE_LOOKBACK:]

    for i in range(len(recent) - 4, 0, -1):
        candle = recent[i]
        body = abs(candle["close"] - candle["open"])

        if body < current_atr * 0.8:
            continue
        if candle["close"] <= candle["open"]:
            continue

        following = recent[i + 1:i + 4]
        if not following:
            continue

        move = candle["high"] - min(c["close"] for c in following)
        if move >= current_atr * 0.8:
            return {
                "low": min(candle["open"], candle["close"]),
                "high": candle["high"],
            }

    return None


# =========================================================
# ENTRY CONFIRMATION
# =========================================================

def fifteen_minute_confirmation(candles, bias):
    if len(candles) < 50:
        return False

    value = rsi(closes(candles))
    if value is None:
        return False

    if bias == "BULLISH":
        return 45 <= value <= 68

    if bias == "BEARISH":
        return 32 <= value <= 55

    return False


def five_minute_entry(candles, bias):
    if len(candles) < 60:
        return None

    value = rsi(closes(candles))
    current_atr = atr(candles)

    if value is None or current_atr is None:
        return None

    current = candles[-1]
    previous = candles[-2]

    if bias == "BULLISH":
        if (
            current["close"] > current["open"]
            and previous["close"] < previous["open"]
            and current["close"] > previous["high"]
            and 50 <= value <= 70
        ):
            return {
                "direction": "BUY",
                "entry": current["close"],
                "atr": current_atr,
                "rsi": value,
            }

    if bias == "BEARISH":
        if (
            current["close"] < current["open"]
            and previous["close"] > previous["open"]
            and current["close"] < previous["low"]
            and 30 <= value <= 50
        ):
            return {
                "direction": "SELL",
                "entry": current["close"],
                "atr": current_atr,
                "rsi": value,
            }

    return None


# =========================================================
# TOP-DOWN ANALYSIS
# =========================================================

def top_down_bias(pair_data):
    directions = {}

    for name in ("MONTHLY", "WEEKLY", "DAILY", "4H"):
        directions[name] = timeframe_direction(pair_data.get(name, []))

    bullish = sum(v == "BULLISH" for v in directions.values())
    bearish = sum(v == "BEARISH" for v in directions.values())

    if bullish >= 3:
        return "BULLISH", directions

    if bearish >= 3:
        return "BEARISH", directions

    return "NEUTRAL", directions


def signal_score(pair_data, bias, directions, entry):
    score = 0
    reasons = []

    weights = {
        "MONTHLY": 1,
        "WEEKLY": 2,
        "DAILY": 2,
        "4H": 2,
        "1H": 1,
    }

    for name, weight in weights.items():
        if directions.get(name) == bias:
            score += weight
            reasons.append(f"{name} agrees")

    if fifteen_minute_confirmation(pair_data.get("15M", []), bias):
        score += 1
        reasons.append("15M confirmation")

    candles_5m = pair_data.get("5M", [])

    if bias == "BULLISH" and find_demand_zone(candles_5m):
        score += 1
        reasons.append("Demand zone")

    if bias == "BEARISH" and find_supply_zone(candles_5m):
        score += 1
        reasons.append("Supply zone")

    if entry:
        value = entry["rsi"]
        if bias == "BULLISH" and 50 <= value <= 70:
            score += 1
            reasons.append("Bullish RSI")
        elif bias == "BEARISH" and 30 <= value <= 50:
            score += 1
            reasons.append("Bearish RSI")

    return score, reasons


# =========================================================
# TRADE LEVELS
# =========================================================

def build_trade(pair, entry_data):
    if not entry_data:
        return None

    entry = entry_data["entry"]
    direction = entry_data["direction"]
    risk = entry_data["atr"] * SL_ATR_MULTIPLIER

    if risk <= 0:
        return None

    if direction == "BUY":
        stop = entry - risk
        target = entry + risk * RR
        protection = entry + risk * PROTECT_R
    else:
        stop = entry + risk
        target = entry - risk * RR
        protection = entry - risk * PROTECT_R

    return {
        "pair": pair,
        "direction": direction,
        "entry": round_price(pair, entry),
        "stop_loss": round_price(pair, stop),
        "take_profit": round_price(pair, target),
        "protection_activation": round_price(pair, protection),
        "risk_distance": round_price(pair, risk),
        "rr": RR,
        "protect_r": PROTECT_R,
    }


# =========================================================
# PAIR ANALYSIS
# =========================================================

def analyze_pair(pair, market_data):
    pair_data = {}

    for name, interval in TIMEFRAMES.items():
        pair_data[name] = market_data.get(interval, {}).get(pair, [])

    bias, directions = top_down_bias(pair_data)

    if bias == "NEUTRAL":
        return {
            "pair": pair,
            "status": "WAIT",
            "bias": bias,
            "directions": directions,
            "score": 0,
            "reasons": ["Higher timeframes are not aligned"],
        }

    entry = five_minute_entry(pair_data["5M"], bias)
    score, reasons = signal_score(pair_data, bias, directions, entry)

    if not entry:
        return {
            "pair": pair,
            "status": "WAIT",
            "bias": bias,
            "directions": directions,
            "score": score,
            "reasons": reasons + ["Waiting for 5M entry confirmation"],
        }

    if score < MIN_SIGNAL_SCORE:
        return {
            "pair": pair,
            "status": "WAIT",
            "bias": bias,
            "directions": directions,
            "score": score,
            "reasons": reasons + ["Signal quality below minimum"],
        }

    trade = build_trade(pair, entry)
    if not trade:
        return {
            "pair": pair,
            "status": "WAIT",
            "bias": bias,
            "directions": directions,
            "score": score,
            "reasons": ["Could not calculate trade levels"],
        }

    trade.update({
        "status": "SIGNAL",
        "bias": bias,
        "score": score,
        "rsi": round(entry["rsi"], 2),
        "atr": round(entry["atr"], 6),
        "directions": directions,
        "reasons": reasons,
        "time": datetime.now(timezone.utc).isoformat(),
    })

    return trade


# =========================================================
# MARKET SCAN
# =========================================================

def _refresh_analysis():
    global latest_market, last_scan
    results, signals = [], []
    # Never interpret missing timeframe data as a valid neutral market.
    for pair in PAIRS:
        available = [market_store.get(interval, {}).get(pair, []) for interval in TIMEFRAMES.values()]
        if any(len(candles) < 20 for candles in available):
            results.append({"pair": pair, "status": "WAIT", "bias": "DATA LOADING",
                            "score": 0, "reasons": ["Waiting for the next free-plan data refresh"]})
            continue
        try:
            result = analyze_pair(pair, market_store)
            results.append(result)
            if result.get("status") == "SIGNAL":
                signals.append(result)
        except Exception as exc:
            log(f"ANALYSIS ERROR {pair}: {exc}")
            results.append({"pair": pair, "status": "ERROR", "message": str(exc)})
    last_scan = time.time()
    latest_market = {
        "status": "ok" if any(market_store.get(i) for i in TIMEFRAMES.values()) else "starting",
        "signals": signals,
        "pairs": results,
        "updated": datetime.now(timezone.utc).isoformat(),
        "message": "Free-plan mode: staged refresh; signal scan updates after timeframe data is available",
    }


def scan_market():
    if not API_KEY:
        log("ERROR: TWELVE_DATA_API_KEY is missing")
        return
    log("Starting low-usage staged market refresh")
    # 12 pairs are split into batches of 8 and 4. One batch per minute keeps
    # each minute at or below the Basic plan's 8 credits/minute.
    batches = [PAIRS[:8], PAIRS[8:]]
    for name, interval in TIMEFRAMES.items():
        for batch in batches:
            # Respect UTC minute reset; no rapid retries on a full quota.
            minute_key, _ = _quota_key()
            wait = 60 - (time.time() % 60) + 1
            allowed, reason = _can_spend(len(batch), "scan")
            if not allowed and "next minute" in reason:
                time.sleep(max(1, wait))
            allowed, reason = _can_spend(len(batch), "scan")
            if not allowed:
                log(f"Skipping batch {interval}: {reason}")
                continue
            log(f"Loading {name} ({interval}) for {len(batch)} pairs")
            data = get_data(interval, OUTPUT_SIZE[interval], batch, "scan")
            for pair, candles in data.items():
                market_store.setdefault(interval, {})[pair] = candles
            _refresh_analysis()
            # Keep one batch per minute even if a request finishes quickly.
            elapsed = time.time() % 60
            time.sleep(max(1, 61 - elapsed))
    log("Staged market refresh complete")


def background_worker():
    log("VIC FX free-plan background worker started")
    while True:
        try:
            scan_market()
        except Exception as exc:
            log(f"BACKGROUND ERROR: {exc}")
        # Full scan uses roughly 84 credits. Three-hour cadence leaves room for
        # chart requests under the free 800-credit daily allowance.
        time.sleep(SCAN_INTERVAL_SECONDS)


# Gunicorn imports app:app, so start the worker on import.
_worker = threading.Thread(
    target=background_worker

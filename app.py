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

def get_data(interval, outputsize):
    if not API_KEY:
        return {}

    key = f"{interval}:{outputsize}"
    old = cache.get(key)
    if old and time.time() - old[0] < CACHE_SECONDS:
        return old[1]

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
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        raw = response.json()
    except Exception as exc:
        log(f"DATA ERROR {interval}: {exc}")
        return {}

    result = {}
    if not isinstance(raw, dict):
        return result

    for pair in PAIRS:
        item = raw.get(pair)
        if not isinstance(item, dict):
            continue

        values = item.get("values", [])
        candles = []

        for row in values:
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

    cache[key] = (time.time(), result)
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

def scan_market():
    global latest_market, last_scan

    if not API_KEY:
        latest_market = {
            "status": "error",
            "signals": [],
            "pairs": [],
            "updated": datetime.now(timezone.utc).isoformat(),
            "message": "TWELVE_DATA_API_KEY is missing",
        }
        return

    if not scan_lock.acquire(blocking=False):
        return

    try:
        log("Starting market scan...")
        market_data = {}

        for name, interval in TIMEFRAMES.items():
            log(f"Loading {name} ({interval})")
            market_data[interval] = get_data(interval, OUTPUT_SIZE[interval])

        results = []
        signals = []

        for pair in PAIRS:
            try:
                result = analyze_pair(pair, market_data)
                results.append(result)
                if result.get("status") == "SIGNAL":
                    signals.append(result)
            except Exception as exc:
                log(f"ANALYSIS ERROR {pair}: {exc}")
                results.append({
                    "pair": pair,
                    "status": "ERROR",
                    "message": str(exc),
                })

        last_scan = time.time()
        latest_market = {
            "status": "ok",
            "signals": signals,
            "pairs": results,
            "updated": datetime.now(timezone.utc).isoformat(),
            "message": f"Scanned {len(PAIRS)} pairs",
        }

        log(f"Scan complete. Signals: {len(signals)}")

    finally:
        scan_lock.release()


# =========================================================
# BACKGROUND WORKER
# =========================================================

def background_worker():
    log("VIC FX background worker started")

    while True:
        try:
            scan_market()
        except Exception as exc:
            log(f"BACKGROUND ERROR: {exc}")

        time.sleep(SCAN_SECONDS)


# Gunicorn imports app:app, so start the worker on import.
_worker = threading.Thread(
    target=background_worker,
    name="vic-fx-scanner",
    daemon=True,
)
_worker.start()


# =========================================================
# ROUTES
# =========================================================

@app.route("/")
def home():
    try:
        return render_template("index.html")
    except Exception:
        return jsonify({
            "name": "VIC FX SIGNALS",
            "status": "online",
            "message": "index.html was not found; API is still running",
        })


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "bot": "VIC FX SIGNALS",
        "pairs": len(PAIRS),
        "api_key_present": bool(API_KEY),
        "last_scan": last_scan,
        "time": datetime.now(timezone.utc).isoformat(),
    })


@app.route("/api/market")
def api_market():
    return jsonify(latest_market)


@app.route("/api/signals")
def api_signals():
    return jsonify({
        "status": latest_market.get("status"),
        "signals": latest_market.get("signals", []),
        "updated": latest_market.get("updated"),
        "message": latest_market.get("message"),
    })


@app.route("/api/pairs")
def api_pairs():
    return jsonify({
        "pairs": PAIRS,
        "count": len(PAIRS),
    })


@app.route("/api/chart")
def api_chart():
    """Return real Twelve Data OHLC candles for the website chart."""
    pair = request.args.get("pair", "EUR/USD").upper().replace(" ", "")
    interval = request.args.get("interval", "5min")
    allowed_intervals = {"1month", "1week", "1day", "4h", "1h", "15min", "5min"}
    if pair not in PAIRS:
        return jsonify({"error": "Unsupported currency pair", "candles": []}), 400
    if interval not in allowed_intervals:
        return jsonify({"error": "Unsupported timeframe", "candles": []}), 400
    data = get_data(interval, OUTPUT_SIZE.get(interval, 250))
    candles = data.get(pair, [])
    output = []
    for candle in candles:
        try:
            dt = datetime.strptime(candle["datetime"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            output.append({
                "time": int(dt.timestamp()),
                "open": candle["open"],
                "high": candle["high"],
                "low": candle["low"],
                "close": candle["close"],
            })
        except (TypeError, ValueError, KeyError):
            continue
    return jsonify({"pair": pair, "interval": interval, "candles": output, "count": len(output)})


# =========================================================
# LOCAL DEVELOPMENT
# =========================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)

import os
import time
import threading
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template

app = Flask(__name__)

API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

PAIRS = [
    "EUR/USD","GBP/USD","USD/JPY","USD/CHF",
    "USD/CAD","AUD/USD","NZD/USD","EUR/GBP",
    "EUR/JPY","GBP/JPY","AUD/JPY","NZD/JPY"
]

RSI_PERIOD = 14
RR = 2.0
PROTECT_R = 0.5
MIN_SCORE = 7

cache = {}
latest = {
    "status": "starting",
    "signals": [],
    "pairs": [],
    "updated": None,
    "message": "Starting..."
}

lock = threading.Lock()
pair_index = 0


def log(x):
    print(
        f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC] {x}",
        flush=True
    )


# =========================================================
# DATA
# =========================================================

def get_data(pair, interval, size):
    key = f"{pair}:{interval}"

    if key in cache:
        return cache[key]

    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": pair,
                "interval": interval,
                "outputsize": size,
                "apikey": API_KEY,
                "timezone": "UTC"
            },
            timeout=20
        )

        data = r.json()

        if "values" not in data:
            log(f"{pair} {interval}: {data}")
            return []

        candles = []

        for x in reversed(data["values"]):
            try:
                candles.append({
                    "datetime": x["datetime"],
                    "open": float(x["open"]),
                    "high": float(x["high"]),
                    "low": float(x["low"]),
                    "close": float(x["close"])
                })
            except:
                pass

        cache[key] = candles
        return candles

    except Exception as e:
        log(f"DATA ERROR {pair} {interval}: {e}")
        return []


def aggregate(candles, minutes):
    if not candles:
        return []

    out = {}

    for c in candles:
        try:
            dt = datetime.fromisoformat(
                c["datetime"].replace("Z", "+00:00")
            )
            stamp = int(dt.timestamp() // (minutes * 60))
        except:
            continue

        if stamp not in out:
            out[stamp] = {
                "datetime": c["datetime"],
                "open": c["open"],
                "high": c["high"],
                "low": c["low"],
                "close": c["close"]
            }
        else:
            out[stamp]["high"] = max(out[stamp]["high"], c["high"])
            out[stamp]["low"] = min(out[stamp]["low"], c["low"])
            out[stamp]["close"] = c["close"]

    return list(out.values())


# =========================================================
# INDICATORS
# =========================================================

def rsi(candles):
    if len(candles) < RSI_PERIOD + 1:
        return None

    closes = [x["close"] for x in candles]

    gains = []
    losses = []

    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))

    gain = sum(gains[:RSI_PERIOD]) / RSI_PERIOD
    loss = sum(losses[:RSI_PERIOD]) / RSI_PERIOD

    for i in range(RSI_PERIOD, len(gains)):
        gain = ((gain * 13) + gains[i]) / 14
        loss = ((loss * 13) + losses[i]) / 14

    if loss == 0:
        return 100

    return 100 - (100 / (1 + gain / loss))


def ema(candles, period):
    if len(candles) < period:
        return None

    prices = [x["close"] for x in candles]
    value = sum(prices[:period]) / period
    mult = 2 / (period + 1)

    for p in prices[period:]:
        value += (p - value) * mult

    return value


def atr(candles):
    if len(candles) < 15:
        return None

    tr = []

    for i in range(1, len(candles)):
        a = candles[i]
        b = candles[i - 1]

        tr.append(max(
            a["high"] - a["low"],
            abs(a["high"] - b["close"]),
            abs(a["low"] - b["close"])
        ))

    return sum(tr[-14:]) / 14


# =========================================================
# TREND
# =========================================================

def direction(candles):
    if len(candles) < 55:
        return "NEUTRAL"

    fast = ema(candles, 20)
    slow = ema(candles, 50)
    price = candles[-1]["close"]

    if fast > slow and price > fast:
        return "BULLISH"

    if fast < slow and price < fast:
        return "BEARISH"

    return "NEUTRAL"


# =========================================================
# SUPPLY / DEMAND
# =========================================================

def demand(candles):
    if len(candles) < 40:
        return False

    a = atr(candles)
    if not a:
        return False

    for c in candles[-30:-3]:
        body = abs(c["close"] - c["open"])

        if c["close"] < c["open"] and body >= a * 0.8:
            return True

    return False


def supply(candles):
    if len(candles) < 40:
        return False

    a = atr(candles)
    if not a:
        return False

    for c in candles[-30:-3]:
        body = abs(c["close"] - c["open"])

        if c["close"] > c["open"] and body >= a * 0.8:
            return True

    return False


# =========================================================
# PAIR ANALYSIS
# =========================================================

def analyze(pair, m5, daily):
    if len(m5) < 100 or len(daily) < 60:
        return {
            "pair": pair,
            "status": "WAIT",
            "message": "Loading market data"
        }

    m15 = aggregate(m5, 15)
    h1 = aggregate(m5, 60)
    h4 = aggregate(m5, 240)

    weekly = aggregate(daily, 10080)
    monthly = aggregate(daily, 43200)

    dirs = {
        "MONTHLY": direction(monthly),
        "WEEKLY": direction(weekly),
        "DAILY": direction(daily),
        "4H": direction(h4),
        "1H": direction(h1)
    }

    bull = sum(x == "BULLISH" for x in dirs.values())
    bear = sum(x == "BEARISH" for x in dirs.values())

    if bull >= 3:
        bias = "BULLISH"
    elif bear >= 3:
        bias = "BEARISH"
    else:
        return {
            "pair": pair,
            "status": "WAIT",
            "bias": "NEUTRAL",
            "directions": dirs,
            "score": 0
        }

    score = 0
    reasons = []

    for name, d in dirs.items():
        if d == bias:
            score += 1
            reasons.append(name)

    r15 = rsi(m15)
    r5 = rsi(m5)
    a = atr(m5)

    if not r15 or not r5 or not a:
        return {
            "pair": pair,
            "status": "WAIT",
            "bias": bias,
            "directions": dirs,
            "score": score
        }

    if bias == "BULLISH":
        if 45 <= r15 <= 68:
            score += 1
            reasons.append("15M confirmation")

        if demand(m5):
            score += 1
            reasons.append("Demand zone")

        entry_ok = (
            m5[-1]["close"] > m5[-1]["open"]
            and m5[-2]["close"] < m5[-2]["open"]
            and m5[-1]["close"] > m5[-2]["high"]
            and 50 <= r5 <= 70
        )

        if entry_ok:
            score += 2
            reasons.append("5M BUY confirmation")

    else:
        if 32 <= r15 <= 55:
            score += 1
            reasons.append("15M confirmation")

        if supply(m5):
            score += 1
            reasons.append("Supply zone")

        entry_ok = (
            m5[-1]["close"] < m5[-1]["open"]
            and m5[-2]["close"] > m5[-2]["open"]
            and m5[-1]["close"] < m5[-2]["low"]
            and 30 <= r5 <= 50
        )

        if entry_ok:
            score += 2
            reasons.append("5M SELL confirmation")

    if score < MIN_SCORE or not entry_ok:
        return {
            "pair": pair,
            "status": "WAIT",
            "bias": bias,
            "directions": dirs,
            "score": score,
            "rsi": round(r5, 2),
            "reasons": reasons
        }

    entry = m5[-1]["close"]
    risk = a

    if bias == "BULLISH":
        stop = entry - risk
        target = entry + risk * RR
        protect = entry + risk * PROTECT_R
        signal = "BUY"
    else:
        stop = entry + risk
        target = entry - risk * RR
        protect = entry - risk * PROTECT_R
        signal = "SELL"

    digits = 3 if "JPY" in pair else 5

    return {
        "pair": pair,
        "status": "SIGNAL",
        "direction": signal,
        "bias": bias,
        "score": score,
        "entry": round(entry, digits),
        "stop_loss": round(stop, digits),
        "take_profit": round(target, digits),
        "protection_activation": round(protect, digits),
        "rsi": round(r5, 2),
        "rr": RR,
        "protect_r": PROTECT_R,
        "directions": dirs,
        "reasons": reasons,
        "time": datetime.now(timezone.utc).isoformat()
    }


# =========================================================
# SCANNER
# =========================================================

def scan():
    global pair_index, latest

    if not API_KEY:
        latest["status"] = "error"
        latest["message"] = "TWELVE_DATA_API_KEY is missing"
        return

    batch = PAIRS[pair_index:pair_index + 3]

    if len(batch) < 3:
        batch += PAIRS[:3 - len(batch)]

    pair_index = (pair_index + 3) % len(PAIRS)

    log("Loading: " + ", ".join(batch))

    for pair in batch:

        m5 = get_data(pair, "5min", 5000)

        # Wait briefly so requests are not fired together
        time.sleep(1)

        daily = get_data(pair, "1day", 300)

        if not m5 or not daily:
            continue

        result = analyze(pair, m5, daily)

        latest["pairs"] = [
            x for x in latest["pairs"]
            if x.get("pair") != pair
        ]

        latest["pairs"].append(result)

    latest["signals"] = [
        x for x in latest["pairs"]
        if x.get("status") == "SIGNAL"
    ]

    latest["status"] = "ok"
    latest["updated"] = datetime.now(timezone.utc).isoformat()
    latest["message"] = f"Monitoring {len(PAIRS)} pairs"

    log("Scan complete")


def worker():
    while True:
        try:
            scan()
        except Exception as e:
            log(f"SCAN ERROR: {e}")

        # 3 pairs/minute = 6 API credits/minute
        time.sleep(60)


threading.Thread(
    target=worker,
    daemon=True
).start()


# =========================================================
# WEB
# =========================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "online",
        "bot": "VIC FX SIGNALS",
        "pairs": len(PAIRS),
        "api_key_present": bool(API_KEY),
        "time": datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/market")
def market():
    return jsonify(latest)


@app.route("/api/signals")
def signals():
    return jsonify({
        "status": latest["status"],
        "signals": latest["signals"],
        "updated": latest["updated"],
        "message": latest["message"]
    })


@app.route("/api/pairs")
def pairs():
    return jsonify({
        "pairs": PAIRS,
        "count": len(PAIRS)
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

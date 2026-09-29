import os
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# =========================================================
# SETTINGS
# =========================================================

TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD"
]

TIMEFRAME = "5min"
OUTPUT_SIZE = 100

RSI_PERIOD = 14
RR = 2.0
PROTECT_R = 0.5


# =========================================================
# GET MARKET DATA
# =========================================================

def get_data(symbol):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "outputsize": OUTPUT_SIZE,
        "apikey": TWELVE_DATA_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        data = response.json()

        if "values" not in data:
            return None

        values = data["values"]

        values.reverse()

        candles = []

        for x in values:
            candles.append({
                "open": float(x["open"]),
                "high": float(x["high"]),
                "low": float(x["low"]),
                "close": float(x["close"])
            })

        return candles

    except Exception:
        return None


# =========================================================
# RSI
# =========================================================

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
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


# =========================================================
# SIGNAL
# =========================================================

def generate_signal(symbol):

    candles = get_data(symbol)

    if not candles or len(candles) < 30:
        return {
            "pair": symbol,
            "signal": "NO DATA"
        }

    closes = [x["close"] for x in candles]

    rsi = calculate_rsi(closes, RSI_PERIOD)

    if rsi is None:
        return {
            "pair": symbol,
            "signal": "NO DATA"
        }

    current = candles[-1]

    # Recent supply and demand zones
    recent = candles[-21:-1]

    demand = min(x["low"] for x in recent)
    supply = max(x["high"] for x in recent)

    price = current["close"]

    # Distance from zones
    demand_distance = abs(price - demand)
    supply_distance = abs(supply - price)

    # BUY CONDITIONS
    buy_condition = (
        price <= demand * 1.002
        and rsi <= 40
    )

    # SELL CONDITIONS
    sell_condition = (
        price >= supply * 0.998
        and rsi >= 60
    )

    if buy_condition:

        entry = price
        stop = demand

        risk = entry - stop

        if risk <= 0:
            return {
                "pair": symbol,
                "signal": "WAIT",
                "price": price,
                "rsi": round(rsi, 2)
            }

        take_profit = entry + (risk * RR)
        protect_price = entry + (risk * PROTECT_R)

        return {
            "pair": symbol,
            "signal": "BUY",
            "entry": round(entry, 5),
            "stop_loss": round(stop, 5),
            "take_profit": round(take_profit, 5),
            "profit_protection": round(protect_price, 5),
            "rsi": round(rsi, 2),
            "risk_reward": "1:2"
        }

    if sell_condition:

        entry = price
        stop = supply

        risk = stop - entry

        if risk <= 0:
            return {
                "pair": symbol,
                "signal": "WAIT",
                "price": price,
                "rsi": round(rsi, 2)
            }

        take_profit = entry - (risk * RR)
        protect_price = entry - (risk * PROTECT_R)

        return {
            "pair": symbol,
            "signal": "SELL",
            "entry": round(entry, 5),
            "stop_loss": round(stop, 5),
            "take_profit": round(take_profit, 5),
            "profit_protection": round(protect_price, 5),
            "rsi": round(rsi, 2),
            "risk_reward": "1:2"
        }

    return {
        "pair": symbol,
        "signal": "WAIT",
        "price": round(price, 5),
        "rsi": round(rsi, 2),
        "demand": round(demand, 5),
        "supply": round(supply, 5)
    }


# =========================================================
# WEB ROUTES
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "status": "ONLINE",
        "message": "Forex signal bot is running",
        "pairs": PAIRS,
        "timeframe": TIMEFRAME
    })


@app.route("/signals")
def signals():

    results = []

    for pair in PAIRS:
        results.append(generate_signal(pair))

    return jsonify({
        "status": "success",
        "timeframe": TIMEFRAME,
        "signals": results
    })


@app.route("/signal/<path:symbol>")
def single_signal(symbol):

    return jsonify(generate_signal(symbol))


# =========================================================
# RENDER SERVER
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
                               )

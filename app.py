import os
import requests
from datetime import datetime
from flask import Flask, jsonify, render_template

app = Flask(__name__)

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD"
]

INTERVAL = "5min"
OUTPUT_SIZE = 100
RSI_PERIOD = 14
RR = 2.0
PROTECT_R = 0.5


def get_candles(symbol):

    if not API_KEY:
        return None

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": INTERVAL,
        "outputsize": OUTPUT_SIZE,
        "apikey": API_KEY
    }

    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()

        if "values" not in data:
            print("Twelve Data:", data)
            return None

        values = list(reversed(data["values"]))

        candles = []

        for x in values:
            candles.append({
                "time": x["datetime"],
                "open": float(x["open"]),
                "high": float(x["high"]),
                "low": float(x["low"]),
                "close": float(x["close"])
            })

        return candles

    except Exception as e:
        print("API error:", e)
        return None


def rsi(closes, period=14):

    if len(closes) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]

        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):

        avg_gain = (
            avg_gain * (period - 1) + gains[i]
        ) / period

        avg_loss = (
            avg_loss * (period - 1) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def make_signal(pair, candles):

    if not candles or len(candles) < 30:
        return {
            "pair": pair,
            "signal": "NO DATA"
        }

    closes = [x["close"] for x in candles]

    current = closes[-1]

    value_rsi = rsi(
        closes,
        RSI_PERIOD
    )

    recent = candles[-21:-1]

    demand = min(
        x["low"] for x in recent
    )

    supply = max(
        x["high"] for x in recent
    )

    result = {
        "pair": pair,
        "signal": "WAIT",
        "price": round(current, 5),
        "rsi": round(value_rsi, 2),
        "demand": round(demand, 5),
        "supply": round(supply, 5)
    }

    # BUY near demand + oversold RSI
    if current <= demand * 1.002 and value_rsi <= 40:

        entry = current
        stop = demand
        risk = entry - stop

        if risk > 0:

            result.update({
                "signal": "BUY",
                "entry": round(entry, 5),
                "stop": round(stop, 5),
                "tp": round(entry + risk * RR, 5),
                "protect": round(
                    entry + risk * PROTECT_R,
                    5
                ),
                "rr": "1:2"
            })

    # SELL near supply + high RSI
    elif current >= supply * 0.998 and value_rsi >= 60:

        entry = current
        stop = supply
        risk = stop - entry

        if risk > 0:

            result.update({
                "signal": "SELL",
                "entry": round(entry, 5),
                "stop": round(stop, 5),
                "tp": round(entry - risk * RR, 5),
                "protect": round(
                    entry - risk * PROTECT_R,
                    5
                ),
                "rr": "1:2"
            })

    return result


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/dashboard")
def dashboard():

    output = []

    for pair in PAIRS:

        candles = get_candles(pair)

        signal = make_signal(
            pair,
            candles
        )

        output.append({
            "signal": signal,
            "candles": candles or []
        })

    return jsonify({
        "status": "ONLINE",
        "timeframe": INTERVAL,
        "updated": datetime.utcnow().strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        ),
        "pairs": output
    })


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
)

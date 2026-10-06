import os
import time
import threading
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

PAIRS = [
    "EUR/USD","GBP/USD","USD/JPY","USD/CHF",
    "USD/CAD","AUD/USD","NZD/USD","EUR/GBP",
    "EUR/JPY","GBP/JPY","AUD/JPY","NZD/JPY"
]

RR = 2.0
PROTECT_R = 0.5
RSI_PERIOD = 14

cache = {}
results = {}
index = 0
lock = threading.Lock()


def fetch(symbol, interval, size):
    key = (symbol, interval)
    now = time.time()

    ttl = 240 if interval == "5min" else 1800

    if key in cache and now - cache[key][0] < ttl:
        return cache[key][1]

    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": size,
                "apikey": KEY,
                "timezone": "UTC",
                "order": "asc"
            },
            timeout=15
        )

        data = r.json()

        if "values" not in data:
            print("TD ERROR:", symbol, interval, data, flush=True)
            return []

        candles = []

        for x in data["values"]:
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

        cache[key] = (now, candles)
        return candles

    except Exception as e:
        print("REQUEST ERROR:", symbol, interval, e, flush=True)
        return []


def aggregate(candles, minutes):
    out = {}

    for x in candles:
        try:
            t = datetime.fromisoformat(
                x["datetime"].replace("Z", "+00:00")
            ).timestamp()

            key = int(t // (minutes * 60))
        except:
            continue

        if key not in out:
            out[key] = dict(x)
        else:
            out[key]["high"] = max(out[key]["high"], x["high"])
            out[key]["low"] = min(out[key]["low"], x["low"])
            out[key]["close"] = x["close"]

    return list(out.values())


def ema(candles, period):
    if len(candles) < period:
        return None

    value = sum(x["close"] for x in candles[:period]) / period
    multiplier = 2 / (period + 1)

    for x in candles[period:]:
        value += (x["close"] - value) * multiplier

    return value


def rsi(candles):
    if len(candles) < RSI_PERIOD + 1:
        return None

    prices = [x["close"] for x in candles]
    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    gain = sum(gains[:14]) / 14
    loss = sum(losses[:14]) / 14

    for i in range(14, len(gains)):
        gain = (gain * 13 + gains[i]) / 14
        loss = (loss * 13 + losses[i]) / 14

    if loss == 0:
        return 100

    return 100 - (100 / (1 + gain / loss))


def atr(candles):
    if len(candles) < 15:
        return None

    tr = []

    for i in range(1, len(candles)):
        h = candles[i]["high"]
        l = candles[i]["low"]
        pc = candles[i - 1]["close"]

        tr.append(
            max(
                h - l,
                abs(h - pc),
                abs(l - pc)
            )
        )

    return sum(tr[-14:]) / 14


def trend(candles):
    if len(candles) < 12:
        return "NEUTRAL"

    fast = ema(candles, 5)
    slow = ema(candles, 10)

    if not fast or not slow:
        return "NEUTRAL"

    price = candles[-1]["close"]

    if fast > slow and price > fast:
        return "BULLISH"

    if fast < slow and price < fast:
        return "BEARISH"

    return "NEUTRAL"


def zone(candles, side):
    if len(candles) < 30:
        return False

    a = atr(candles)

    if not a:
        return False

    for x in candles[-25:-2]:
        body = abs(x["close"] - x["open"])

        if side == "BUY":
            if x["close"] < x["open"] and body >= a * 0.8:
                return True

        if side == "SELL":
            if x["close"] > x["open"] and body >= a * 0.8:
                return True

    return False


def analyze(pair):

    m5 = fetch(pair, "5min", 250)
    daily = fetch(pair, "1day", 120)
    weekly = fetch(pair, "1week", 30)
    monthly = fetch(pair, "1month", 24)

    if len(m5) < 60 or len(daily) < 20:
        return {
            "pair": pair,
            "status": "WAIT",
            "message": "Waiting for market data"
        }

    m15 = aggregate(m5, 15)
    h1 = aggregate(m5, 60)
    h4 = aggregate(m5, 240)

    directions = {
        "MONTHLY": trend(monthly),
        "WEEKLY": trend(weekly),
        "DAILY": trend(daily),
        "4H": trend(h4),
        "1H": trend(h1)
    }

    bullish = sum(v == "BULLISH" for v in directions.values())
    bearish = sum(v == "BEARISH" for v in directions.values())

    if bullish >= 3:
        bias = "BULLISH"
    elif bearish >= 3:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    r5 = rsi(m5)
    r15 = rsi(m15)
    a = atr(m5)

    base = {
        "pair": pair,
        "status": "WAIT",
        "bias": bias,
        "directions": directions,
        "rsi": round(r5, 2) if r5 else None
    }

    if bias == "NEUTRAL" or not r5 or not r15 or not a:
        return base

    score = sum(
        v == bias for v in directions.values()
    )

    reasons = [
        k for k, v in directions.items()
        if v == bias
    ]

    if bias == "BULLISH":

        if 45 <= r15 <= 68:
            score += 1
            reasons.append("15M confirmation")

        if zone(m5, "BUY"):
            score += 1
            reasons.append("Demand zone")

        entry_ok = (
            m5[-1]["close"] > m5[-1]["open"]
            and
            m5[-2]["close"] < m5[-2]["open"]
            and
            m5[-1]["close"] > m5[-2]["high"]
            and
            50 <= r5 <= 70
        )

        side = "BUY"

    else:

        if 32 <= r15 <= 55:
            score += 1
            reasons.append("15M confirmation")

        if zone(m5, "SELL"):
            score += 1
            reasons.append("Supply zone")

        entry_ok = (
            m5[-1]["close"] < m5[-1]["open"]
            and
            m5[-2]["close"] > m5[-2]["open"]
            and
            m5[-1]["close"] < m5[-2]["low"]
            and
            30 <= r5 <= 50
        )

        side = "SELL"

    if score < 6 or not entry_ok:
        base["score"] = score
        base["reasons"] = reasons
        return base

    entry = m5[-1]["close"]
    risk = a

    if side == "BUY":
        stop = entry - risk
        target = entry + (risk * RR)
        protect = entry + (risk * PROTECT_R)

    else:
        stop = entry + risk
        target = entry - (risk * RR)
        protect = entry - (risk * PROTECT_R)

    digits = 3 if "JPY" in pair else 5

    return {
        "pair": pair,
        "status": "SIGNAL",
        "direction": side,
        "bias": bias,
        "score": score,
        "entry": round(entry, digits),
        "stop_loss": round(stop, digits),
        "take_profit": round(target, digits),
        "protection_activation": round(protect, digits),
        "rsi": round(r5, 2),
        "rr": RR,
        "protect_r": PROTECT_R,
        "directions": directions,
        "reasons": reasons,
        "time": datetime.now(timezone.utc).isoformat()
    }


def scan():

    global index

    if not KEY:
        print(
            "ERROR: TWELVE_DATA_API_KEY is missing",
            flush=True
        )
        return

    batch = PAIRS[index:index + 2]

    index = (index + 2) % len(PAIRS)

    print(
        "Loading:",
        ", ".join(batch),
        flush=True
    )

    for pair in batch:

        result = analyze(pair)

        with lock:
            results[pair] = result

        time.sleep(1)

    print("Scan complete", flush=True)


def worker():

    while True:

        try:
            scan()

        except Exception as e:
            print(
                "SCAN ERROR:",
                e,
                flush=True
            )

        time.sleep(60)


HTML = """
<!DOCTYPE html>
<html>
<head>

<meta name="viewport"
content="width=device-width,initial-scale=1">

<title>VIC FX SIGNALS</title>

<style>

body{
margin:0;
background:#090b0f;
color:#eee;
font-family:Arial;
padding:18px
}

h1{
margin:0;
color:#00e5a0
}

.sub{
color:#aaa;
margin:6px 0 18px
}

.bar{
padding:12px;
background:#151922;
border-radius:10px
}

.grid{
display:grid;
grid-template-columns:
repeat(auto-fit,minmax(250px,1fr));
gap:12px;
margin-top:14px
}

.card{
background:#121620;
border:1px solid #292e39;
border-radius:12px;
padding:15px
}

.buy{
color:#00e5a0
}

.sell{
color:#ff5964
}

.small{
color:#9da3ad;
font-size:13px;
line-height:1.7
}

.price{
font-size:22px;
font-weight:bold;
margin:8px 0
}

</style>

</head>

<body>

<h1>⚡ VIC FX SIGNALS</h1>

<div class="sub">
INTRADAY • TOP-DOWN • 5M ENTRY • RSI • SUPPLY & DEMAND
</div>

<div class="bar" id="status">
Connecting...
</div>

<div class="grid" id="grid"></div>

<script>

async function load(){

try{

let r = await fetch(
'/api/market?x=' + Date.now()
);

if(!r.ok) throw 0;

let d = await r.json();

document.getElementById("status")
.innerHTML =
"🟢 ONLINE • " +
(d.updated || "Scanning...");

let a = d.pairs || [];

document.getElementById("grid")
.innerHTML = a.map(x => {

let c =
x.status === "SIGNAL"
?
(x.direction === "BUY" ? "buy" : "sell")
:
"";

return `
<div class="card">

<b>${x.pair}</b>

<span class="${c}">
${x.direction || x.status}
</span>

<div class="small">
Bias: ${x.bias || "—"}
<br>
RSI: ${x.rsi || "—"}
<br>
Score: ${x.score || 0}
</div>

${
x.status === "SIGNAL"

?

`

<div class="price">
${x.entry}
</div>

<div class="small">
SL: ${x.stop_loss}
<br>
TP: ${x.take_profit}
<br>
Protect +0.5R:
${x.protection_activation}
</div>

`

:

`

<div class="small">
Waiting for a confirmed entry.
</div>

`

}

</div>
`;

}).join("");

}

catch(e){

document.getElementById("status")
.innerHTML =
"🔴 CONNECTION ERROR";

}

}

load();

setInterval(load,15000);

</script>

</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "api_key_present": bool(KEY),
        "pairs": len(PAIRS)
    })


@app.route("/api/market")
def market():

    with lock:
        values = list(results.values())

    return jsonify({
        "status": "ok" if KEY else "error",
        "pairs": values,
        "signals": [
            x for x in values
            if x.get("status") == "SIGNAL"
        ],
        "updated":
            datetime.now(timezone.utc).isoformat()
    })


@app.route("/api/signals")
def signals():

    with lock:
        values = list(results.values())

    return jsonify({
        "status": "ok",
        "signals": [
            x for x in values
            if x.get("status") == "SIGNAL"
        ]
    })


@app.route("/api/pairs")
def pairs():

    return jsonify({
        "pairs": PAIRS,
        "count": len(PAIRS)
    })


if __name__ == "__main__":

    threading.Thread(
        target=worker,
        daemon=True
    ).start()

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000"))
    )

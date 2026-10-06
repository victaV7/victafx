import os, time, threading, requests
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

# SHOW ALL PAIRS IMMEDIATELY
results = {
    p: {
        "pair": p,
        "status": "WAIT",
        "message": "Loading market data..."
    } for p in PAIRS
}

cache = {}
pair_index = 0
lock = threading.Lock()


def td(symbol, interval, size):
    key = (symbol, interval)
    now = time.time()

    if key in cache and now - cache[key][0] < 300:
        return cache[key][1]

    try:
        r = requests.get(
            "https://api.twelvedata.com/time_series",
            params={
                "symbol": symbol,
                "interval": interval,
                "outputsize": size,
                "apikey": KEY,
                "timezone": "UTC"
            },
            timeout=15
        )

        data = r.json()

        if "values" not in data:
            print("TD ERROR:", symbol, interval, data, flush=True)
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

        cache[key] = (now, candles)
        return candles

    except Exception as e:
        print("REQUEST ERROR:", symbol, interval, e, flush=True)
        return []


def aggregate(c, minutes):
    out = {}

    for x in c:
        try:
            t = datetime.fromisoformat(
                x["datetime"].replace("Z", "+00:00")
            ).timestamp()

            k = int(t // (minutes * 60))

            if k not in out:
                out[k] = dict(x)
            else:
                out[k]["high"] = max(out[k]["high"], x["high"])
                out[k]["low"] = min(out[k]["low"], x["low"])
                out[k]["close"] = x["close"]

        except:
            pass

    return list(out.values())


def ema(c, n):
    if len(c) < n:
        return None

    v = sum(x["close"] for x in c[:n]) / n
    m = 2 / (n + 1)

    for x in c[n:]:
        v += (x["close"] - v) * m

    return v


def rsi(c):
    if len(c) < 15:
        return None

    p = [x["close"] for x in c]
    gains = []
    losses = []

    for i in range(1, len(p)):
        d = p[i] - p[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))

    g = sum(gains[:14]) / 14
    l = sum(losses[:14]) / 14

    for i in range(14, len(gains)):
        g = (g * 13 + gains[i]) / 14
        l = (l * 13 + losses[i]) / 14

    if l == 0:
        return 100

    return 100 - 100 / (1 + g / l)


def atr(c):
    if len(c) < 15:
        return None

    tr = []

    for i in range(1, len(c)):
        h = c[i]["high"]
        lo = c[i]["low"]
        pc = c[i - 1]["close"]

        tr.append(max(
            h - lo,
            abs(h - pc),
            abs(lo - pc)
        ))

    return sum(tr[-14:]) / 14


def trend(c):
    if len(c) < 12:
        return "NEUTRAL"

    e1 = ema(c, 5)
    e2 = ema(c, 10)
    price = c[-1]["close"]

    if e1 > e2 and price > e1:
        return "BULLISH"

    if e1 < e2 and price < e1:
        return "BEARISH"

    return "NEUTRAL"


def zone(c, side):
    if len(c) < 30:
        return False

    a = atr(c)

    if not a:
        return False

    for x in c[-25:-2]:

        body = abs(x["close"] - x["open"])

        if side == "BUY":
            if x["close"] < x["open"] and body >= a * .8:
                return True

        else:
            if x["close"] > x["open"] and body >= a * .8:
                return True

    return False


def analyze(pair):

    m5 = td(pair, "5min", 250)
    daily = td(pair, "1day", 120)
    weekly = td(pair, "1week", 30)
    monthly = td(pair, "1month", 24)

    if len(m5) < 50:
        return {
            "pair": pair,
            "status": "WAIT",
            "message": "Waiting for 5M data"
        }

    m15 = aggregate(m5, 15)
    h1 = aggregate(m5, 60)
    h4 = aggregate(m5, 240)

    dirs = {
        "MONTHLY": trend(monthly),
        "WEEKLY": trend(weekly),
        "DAILY": trend(daily),
        "4H": trend(h4),
        "1H": trend(h1)
    }

    bull = list(dirs.values()).count("BULLISH")
    bear = list(dirs.values()).count("BEARISH")

    if bull >= 3:
        bias = "BULLISH"
    elif bear >= 3:
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
        "directions": dirs,
        "rsi": round(r5, 2) if r5 else None,
        "message": "Waiting for entry confirmation"
    }

    if bias == "NEUTRAL" or not r5 or not r15 or not a:
        return base

    score = bull if bias == "BULLISH" else bear
    reasons = []

    if bias == "BULLISH":

        if 45 <= r15 <= 68:
            score += 1
            reasons.append("15M RSI")

        if zone(m5, "BUY"):
            score += 1
            reasons.append("Demand")

        entry_ok = (
            m5[-1]["close"] > m5[-1]["open"] and
            m5[-2]["close"] < m5[-2]["open"] and
            m5[-1]["close"] > m5[-2]["high"] and
            50 <= r5 <= 70
        )

        side = "BUY"

    else:

        if 32 <= r15 <= 55:
            score += 1
            reasons.append("15M RSI")

        if zone(m5, "SELL"):
            score += 1
            reasons.append("Supply")

        entry_ok = (
            m5[-1]["close"] < m5[-1]["open"] and
            m5[-2]["close"] > m5[-2]["open"] and
            m5[-1]["close"] < m5[-2]["low"] and
            30 <= r5 <= 50
        )

        side = "SELL"

    if score < 6 or not entry_ok:
        base["score"] = score
        return base

    entry = m5[-1]["close"]

    if side == "BUY":
        sl = entry - a
        tp = entry + a * RR
        protect = entry + a * PROTECT_R
    else:
        sl = entry + a
        tp = entry - a * RR
        protect = entry - a * PROTECT_R

    digits = 3 if "JPY" in pair else 5

    return {
        "pair": pair,
        "status": "SIGNAL",
        "direction": side,
        "bias": bias,
        "score": score,
        "entry": round(entry, digits),
        "stop_loss": round(sl, digits),
        "take_profit": round(tp, digits),
        "protection_activation": round(protect, digits),
        "rsi": round(r5, 2),
        "rr": RR,
        "protect_r": PROTECT_R,
        "directions": dirs,
        "reasons": reasons,
        "time": datetime.now(timezone.utc).isoformat()
    }


def scanner():

    global pair_index

    while True:

        if not KEY:
            print("ERROR: TWELVE_DATA_API_KEY missing", flush=True)
            time.sleep(60)
            continue

        pair = PAIRS[pair_index]
        pair_index = (pair_index + 1) % len(PAIRS)

        print("Loading:", pair, flush=True)

        try:
            result = analyze(pair)

            with lock:
                results[pair] = result

            print("Finished:", pair, flush=True)

        except Exception as e:
            print("SCAN ERROR:", e, flush=True)

        # One pair at a time = much less API pressure
        time.sleep(20)


HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIC FX SIGNALS</title>

<style>
body{
margin:0;
padding:18px;
background:#080a0e;
color:white;
font-family:Arial
}

h1{
color:#00e6a0;
margin-bottom:5px
}

.sub{
color:#aaa;
margin-bottom:18px
}

.status{
background:#151922;
padding:14px;
border-radius:12px;
margin-bottom:15px
}

.grid{
display:grid;
grid-template-columns:
repeat(auto-fit,minmax(250px,1fr));
gap:12px
}

.card{
background:#121620;
border:1px solid #292e39;
border-radius:13px;
padding:15px
}

.pair{
font-size:19px;
font-weight:bold
}

.wait{
color:#ffc107
}

.buy{
color:#00e6a0;
font-size:22px;
font-weight:bold
}

.sell{
color:#ff5260;
font-size:22px;
font-weight:bold
}

.data{
color:#aaa;
font-size:13px;
line-height:1.7;
margin-top:8px
}

.price{
font-size:20px;
margin:8px 0
}
</style>
</head>

<body>

<h1>⚡ VIC FX SIGNALS</h1>

<div class="sub">
INTRADAY • TOP-DOWN • 5M ENTRY • RSI • SUPPLY & DEMAND
</div>

<div class="status" id="status">
🟢 ONLINE • Loading market data...
</div>

<div class="grid" id="cards"></div>

<script>

async function update(){

try{

const r = await fetch(
"/api/market?t=" + Date.now()
);

const d = await r.json();

document.getElementById("status").innerHTML =
"🟢 ONLINE • " + d.updated;

const cards = d.pairs || [];

document.getElementById("cards").innerHTML =
cards.map(x => {

if(x.status === "SIGNAL"){

let cls =
x.direction === "BUY"
? "buy"
: "sell";

return `
<div class="card">

<div class="pair">${x.pair}</div>

<div class="${cls}">
${x.direction}
</div>

<div class="price">
Entry: ${x.entry}
</div>

<div class="data">
Bias: ${x.bias}<br>
RSI: ${x.rsi}<br>
Score: ${x.score}<br>
SL: ${x.stop_loss}<br>
TP: ${x.take_profit}<br>
Protect +0.5R: ${x.protection_activation}
</div>

</div>
`;

}

return `
<div class="card">

<div class="pair">${x.pair}</div>

<div class="wait">
⏳ WAIT
</div>

<div class="data">
${x.message || "Scanning..."}
<br>
Bias: ${x.bias || "Loading"}
<br>
RSI: ${x.rsi || "Loading"}
</div>

</div>
`;

}).join("");

}

catch(e){

document.getElementById("status").innerHTML =
"🔴 CONNECTION ERROR";

}

}

update();

setInterval(update,15000);

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
        data = list(results.values())

    return jsonify({
        "status": "ok",
        "pairs": data,
        "signals": [
            x for x in data
            if x.get("status") == "SIGNAL"
        ],
        "updated": datetime.now(
            timezone.utc
        ).isoformat()
    })


@app.route("/api/signals")
def signals():

    with lock:
        data = list(results.values())

    return jsonify({
        "status": "ok",
        "signals": [
            x for x in data
            if x.get("status") == "SIGNAL"
        ]
    })


# Start market scanner on Render
threading.Thread(
    target=scanner,
    daemon=True
).start()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000"))
)

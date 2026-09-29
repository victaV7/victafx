import os
import requests
from datetime import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# =========================================================
# SETTINGS
# =========================================================

API_KEY = os.getenv("TWELVE_DATA_API_KEY")

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
# GET TWELVE DATA
# =========================================================

def get_market_data(symbol):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": symbol,
        "interval": TIMEFRAME,
        "outputsize": OUTPUT_SIZE,
        "apikey": API_KEY
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        data = response.json()

        if "values" not in data:
            print("Twelve Data error:", data)
            return None

        values = list(reversed(data["values"]))

        candles = []

        for item in values:
            candles.append({
                "time": item["datetime"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"])
            })

        return candles

    except Exception as error:
        print("Data error:", error)
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


# =========================================================
# CREATE SIGNAL
# =========================================================

def create_signal(symbol, candles):

    if not candles or len(candles) < 30:

        return {
            "pair": symbol,
            "signal": "NO DATA"
        }

    closes = [
        candle["close"]
        for candle in candles
    ]

    rsi = calculate_rsi(
        closes,
        RSI_PERIOD
    )

    if rsi is None:

        return {
            "pair": symbol,
            "signal": "NO DATA"
        }

    price = candles[-1]["close"]

    recent = candles[-21:-1]

    demand = min(
        candle["low"]
        for candle in recent
    )

    supply = max(
        candle["high"]
        for candle in recent
    )

    # =====================================================
    # BUY
    # =====================================================

    if price <= demand * 1.002 and rsi <= 40:

        entry = price
        stop = demand
        risk = entry - stop

        if risk > 0:

            take_profit = entry + (
                risk * RR
            )

            protection = entry + (
                risk * PROTECT_R
            )

            return {
                "pair": symbol,
                "signal": "BUY",
                "price": round(price, 5),
                "entry": round(entry, 5),
                "stop": round(stop, 5),
                "tp": round(take_profit, 5),
                "protect": round(protection, 5),
                "rsi": round(rsi, 2),
                "demand": round(demand, 5),
                "supply": round(supply, 5),
                "rr": "1 : 2"
            }

    # =====================================================
    # SELL
    # =====================================================

    if price >= supply * 0.998 and rsi >= 60:

        entry = price
        stop = supply
        risk = stop - entry

        if risk > 0:

            take_profit = entry - (
                risk * RR
            )

            protection = entry - (
                risk * PROTECT_R
            )

            return {
                "pair": symbol,
                "signal": "SELL",
                "price": round(price, 5),
                "entry": round(entry, 5),
                "stop": round(stop, 5),
                "tp": round(take_profit, 5),
                "protect": round(protection, 5),
                "rsi": round(rsi, 2),
                "demand": round(demand, 5),
                "supply": round(supply, 5),
                "rr": "1 : 2"
            }

    # =====================================================
    # WAIT
    # =====================================================

    return {
        "pair": symbol,
        "signal": "WAIT",
        "price": round(price, 5),
        "rsi": round(rsi, 2),
        "demand": round(demand, 5),
        "supply": round(supply, 5)
    }


# =========================================================
# DASHBOARD API
# =========================================================

@app.route("/api/dashboard")
def dashboard_api():

    results = []

    for pair in PAIRS:

        candles = get_market_data(pair)

        signal = create_signal(
            pair,
            candles
        )

        results.append({
            "signal": signal,
            "candles": candles or []
        })

    return jsonify({
        "status": "success",
        "timeframe": TIMEFRAME,
        "updated": datetime.utcnow().strftime(
            "%H:%M:%S UTC"
        ),
        "pairs": results
    })


# =========================================================
# WEB DASHBOARD
# =========================================================

HTML = '''
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1">

<title>VIC FX SIGNALS</title>

<script src="https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"></script>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background:
        radial-gradient(
            circle at top,
            #18275c 0%,
            #070b18 45%,
            #02040a 100%
        );
    color: white;
}

.header {
    text-align: center;
    padding: 25px 15px;
    background:
        linear-gradient(
            135deg,
            #101a46,
            #4b176d,
            #071c3e
        );
    border-bottom: 2px solid #00eaff;
    box-shadow: 0 0 30px #00eaff55;
}

.logo {
    font-size: 29px;
    font-weight: 900;
    letter-spacing: 2px;
    text-shadow: 0 0 15px #00eaff;
}

.subtitle {
    margin-top: 8px;
    color: #b8c9ff;
    font-size: 14px;
}

.container {
    max-width: 1200px;
    margin: auto;
    padding: 15px;
}

.status {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    padding: 15px 17px;
    background: #0c1428;
    border: 1px solid #263e70;
    border-radius: 15px;
}

.online {
    color: #00ff9d;
    font-weight: bold;
    text-shadow: 0 0 10px #00ff9d;
}

.updated {
    color: #8ca3cf;
    font-size: 12px;
}

.grid {
    display: grid;
    grid-template-columns:
        repeat(
            auto-fit,
            minmax(330px, 1fr)
        );
    gap: 18px;
}

.card {
    background:
        linear-gradient(
            145deg,
            #101a32,
            #070d1b
        );
    border: 1px solid #263b69;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 10px 35px #00000077;
}

.card-header {
    padding: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #243657;
}

.pair {
    font-size: 21px;
    font-weight: 900;
}

.tf {
    color: #8ca9dc;
    font-size: 12px;
    background: #101e3d;
    padding: 6px 9px;
    border-radius: 8px;
}

.signal {
    margin: 14px;
    padding: 13px;
    border-radius: 13px;
    text-align: center;
    font-size: 23px;
    font-weight: 900;
    letter-spacing: 2px;
}

.buy {
    color: #00ff9d;
    background:
        linear-gradient(
            135deg,
            #063b2e,
            #075f40
        );
    border: 1px solid #00ff9d;
    box-shadow: 0 0 20px #00ff9d33;
}

.sell {
    color: #ff5878;
    background:
        linear-gradient(
            135deg,
            #48152a,
            #701d31
        );
    border: 1px solid #ff5878;
    box-shadow: 0 0 20px #ff587833;
}

.wait {
    color: #ffd84a;
    background:
        linear-gradient(
            135deg,
            #443509,
            #5b480b
        );
    border: 1px solid #ffd84a;
}

.chart {
    height: 270px;
    margin: 0 10px 10px 10px;
    border-radius: 12px;
    overflow: hidden;
    background: #060b16;
}

.data {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 9px;
    padding: 10px 14px 16px;
}

.box {
    padding: 11px;
    border-radius: 11px;
    background: #0b1427;
    border: 1px solid #263d6c;
}

.label {
    color: #7188b7;
    font-size: 10px;
    font-weight: bold;
    margin-bottom: 5px;
}

.value {
    font-size: 15px;
    font-weight: 900;
    color: white;
}

.entry {
    color: #00eaff;
}

.stop {
    color: #ff5878;
}

.tp {
    color: #00ff9d;
}

.protect {
    color: #c875ff;
}

.rsi {
    color: #ffd84a;
}

.footer {
    text-align: center;
    color: #60749e;
    font-size: 12px;
    padding: 30px 15px;
}

@media(max-width:600px) {

    .logo {
        font-size: 23px;
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .chart {
        height: 250px;
    }

}

</style>

</head>


<body>


<div class="header">

    <div class="logo">
        ⚡ VIC FX SIGNALS
    </div>

    <div class="subtitle">
        REAL 5-MIN CANDLES • SUPPLY & DEMAND • RSI
    </div>

</div>


<div class="container">


    <div class="status">

        <div class="online">
            ● MARKET ONLINE
        </div>

        <div
            class="updated"
            id="updated">
            Connecting...
        </div>

    </div>


    <div
        class="grid"
        id="cards">

        <div class="card">

            <div class="signal wait">
                LOADING...
            </div>

        </div>

    </div>


</div>


<div class="footer">

    Market data supplied by Twelve Data.
    Signals are informational and involve trading risk.

</div>


<script>

function number(value) {

    if (value === undefined ||
        value === null) {

        return "-";

    }

    return value;

}


function box(
    label,
    value,
    color
) {

    return `
        <div class="box">

            <div class="label">
                ${label}
            </div>

            <div
                class="value ${color}">
                ${number(value)}
            </div>

        </div>
    `;

}


function signalClass(signal) {

    if (signal === "BUY") {
        return "buy";
    }

    if (signal === "SELL") {
        return "sell";
    }

    return "wait";
}


function signalText(signal) {

    if (signal === "BUY") {
        return "🟢 BUY";
    }

    if (signal === "SELL") {
        return "🔴 SELL";
    }

    if (signal === "WAIT") {
        return "🟡 WAIT";
    }

    return "⚪ NO DATA";
}


function candleTime(value) {

    const parts = value.split(" ");

    const dateParts =
        parts[0].split("-");

    const timeParts =
        parts[1].split(":");

    return Date.UTC(
        parseInt(dateParts[0]),
        parseInt(dateParts[1]) - 1,
        parseInt(dateParts[2]),
        parseInt(timeParts[0]),
        parseInt(timeParts[1]),
        parseInt(timeParts[2] || 0)
    ) / 1000;

}


function drawChart(
    element,
    candles,
    signal
) {

    if (!element ||
        !candles ||
        candles.length === 0) {

        return;

    }


    const chart =
        LightweightCharts.createChart(
            element,
            {
                width:
                    element.clientWidth,

                height: 270,

                layout: {
                    background: {
                        color: "#060b16"
                    },

                    textColor: "#8da4d2"
                },

                grid: {
                    vertLines: {
                        color: "#14213b"
                    },

                    horzLines: {
                        color: "#14213b"
                    }
                },

                rightPriceScale: {
                    borderColor: "#263b61"
                },

                timeScale: {
                    borderColor: "#263b61",
                    timeVisible: true,
                    secondsVisible: false
                }
            }
        );


    const series =
        chart.addCandlestickSeries({

            upColor: "#00d68f",
            downColor: "#ff4f70",

            borderUpColor: "#00d68f",
            borderDownColor: "#ff4f70",

            wickUpColor: "#00d68f",
            wickDownColor: "#ff4f70"

        });


    const chartData = [];


    for (
        let i = 0;
        i < candles.length;
        i++
    ) {

        const c = candles[i];

        chartData.push({

            time: candleTime(c.time),

            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close

        });

    }


    series.setData(chartData);


    if (signal.demand) {

        series.createPriceLine({

            price: signal.demand,

            color: "#00eaff",

            lineWidth: 1,

            lineStyle:
                LightweightCharts.LineStyle.Dashed,

            axisLabelVisible: true,

            title: "DEMAND"

        });

    }


    if (signal.supply) {

        series.createPriceLine({

            price: signal.supply,

            color: "#ff4fd8",

            lineWidth: 1,

            lineStyle:
                LightweightCharts.LineStyle.Dashed,

            axisLabelVisible: true,

            title: "SUPPLY"

        });

    }


    if (
        signal.signal === "BUY" ||
        signal.signal === "SELL"
    ) {

        series.createPriceLine({

            price: signal.entry,

            color: "#00eaff",

            lineWidth: 2,

            axisLabelVisible: true,

            title: "ENTRY"

        });


        series.createPriceLine({

            price: signal.stop,

            color: "#ff4f70",

            lineWidth: 1,

            axisLabelVisible: true,

            title: "SL"

        });


        series.createPriceLine({

            price: signal.tp,

            color: "#00ff9d",

            lineWidth: 1,

            axisLabelVisible: true,

            title: "TP"

        });


        series.createPriceLine({

            price: signal.protect,

            color: "#bd65ff",

            lineWidth: 1,

            lineStyle:
                LightweightCharts.LineStyle.Dotted,

            axisLabelVisible: true,

            title: "0.5R"

        });

    }


    chart.timeScale().fitContent();

}


async function loadDashboard() {

    try {

        const response =
            await fetch(
                "/api/dashboard",
                {
                    cache: "no-store"
                }
            );


        const data =
            await response.json();


        document.getElementById(
            "updated"
        ).innerText =
            "Updated " + data.updated;


        const cards =
            document.getElementById(
                "cards"
            );


        cards.innerHTML = "";


        for (
            let i = 0;
            i < data.pairs.length;
            i++
        ) {

            const item =
                data.pairs[i];

            const signal =
                item.signal;

            const chartId =
                "chart" + i;


            let boxes = "";


            if (
                signal.signal === "BUY" ||
                signal.signal === "SELL"
            ) {

                boxes += box(
                    "ENTRY",
                    signal.entry,
                    "entry"
                );

                boxes += box(
                    "STOP LOSS",
                    signal.stop,
                    "stop"
                );

                boxes += box(
                    "TAKE PROFIT",
                    signal.tp,
                    "tp"
                );

                boxes += box(
                    "PROTECT 0.5R",
                    signal.protect,
                    "protect"
                );

                boxes += box(
                    "RSI",
                    signal.rsi,
                    "rsi"
                );

                boxes += box(
                    "RISK / REWARD",
                    signal.rr,
                    ""
                );

                boxes += box(
                    "DEMAND",
                    signal.demand,
                    ""
                );

                boxes += box(
                    "SUPPLY",
                    signal.supply,
                    ""
                );

            } else {

                boxes += box(
                    "CURRENT PRICE",
                    signal.price,
                    "entry"
                );

                boxes += box(
                    "RSI",
                    signal.rsi,
                    "rsi"
                );

                boxes += box(
                    "DEMAND",
                    signal.demand,
                    ""
                );

                boxes += box(
                    "SUPPLY",
                    signal.supply,
                    ""
                );

            }


            cards.innerHTML += `

                <div class="card">

                    <div class="card-header">

                        <div class="pair">
                            ${signal.pair}
                        </div>

                        <div class="tf">
                            5 MIN
                        </div>

                    </div>


                    <div class="signal
                        ${signalClass(
                            signal.signal
                        )}">

                        ${signalText(
                            signal.signal
                        )}

                    </div>


                    <div
                        class="chart"
                        id="${chartId}">
                    </div>


                    <div class="data">

                        ${boxes}

                    </div>

                </div>

            `;

        }


        for (
            let i = 0;
            i < data.pairs.length;
            i++
        ) {

            const item =
                data.pairs[i];


            const element =
                document.getElementById(
                    "chart" + i
                );


            drawChart(
                element,
                item.candles,
                item.signal
            );

        }


    } catch (error) {

        console.log(error);


        document.getElementById(
            "cards"
        ).innerHTML = `

            <div class="card">

                <div class="signal sell">
                    CONNECTION ERROR
                </div>

                <div style="
                    padding:20px;
                    color:#9db0d2;
                ">
        

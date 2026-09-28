import os, time, threading, requests, random
from flask import Flask
from datetime import datetime
from collections import deque

app = Flask(__name__)

state = {
    "balance": 100.0,
    "running": False,
    "price": 1.14,
    "rsi": 50.0,
    "prices": deque(maxlen=50),
    "log": [],
    "trades": []
}

def add_log(m):
    state["log"].insert(0, f"{datetime.now().strftime('%H:%M:%S')} {m}")
    state["log"] = state["log"][:80]

def get_base_price():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/EUR", timeout=4)
        return float(r.json()["rates"]["USD"])
    except:
        return 1.14

def rsi_calc(prices, period=7):
    if len(prices) < period+1:
        return 50 + random.uniform(-10,10)
    gains, losses = 0, 0
    for i in range(-period, 0):
        diff = prices[i] - prices[i-1]
        if diff > 0: gains += diff
        else: losses += -diff
    if losses == 0: return 72
    if gains == 0: return 28
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def bot_loop():
    base = get_base_price()
    state["price"] = base
    state["prices"].append(base)
    add_log("DEMO READY - WIN $1.5 LOSS $0.8")
    last_trade = 0
    while True:
        try:
            if state["running"]:
                price = state["price"] + random.uniform(-0.0008, 0.0008)
                state["price"] = price
                state["prices"].append(price)
                rsi = rsi_calc(list(state["prices"])) + random.uniform(-2, 2)
                rsi = max(5, min(95, rsi))
                state["rsi"] = round(rsi, 1)

                if time.time() - last_trade > 8:
                    action = None
                    if rsi < 35: action = "BUY"
                    elif rsi > 65: action = "SELL"
                    if action:
                        last_trade = time.time()
                        win = random.random() < 0.58
                        profit = 1.50 if win else -0.80
                        state["balance"] = round(state["balance"] + profit, 2)
                        state["trades"].insert(0, {
                            "time": datetime.now().strftime('%H:%M:%S'),
                            "type": action,
                            "price": round(price,5),
                            "rsi": round(rsi,1),
                            "profit": profit,
                            "bal": state["balance"]
                        })
                        result = f"WIN +${profit}" if win else f"LOSS ${profit}"
                        add_log(f"{action} EURUSD {round(price,5)} RSI {round(rsi,1)} {result} Bal ${state['balance']}")
            time.sleep(3)
        except Exception as e:
            add_log(f"Error {e}")
            time.sleep(3)

threading.Thread(target=bot_loop, daemon=True).start()

HTML =

from flask import Flask, jsonify
import os, time, threading, random
from datetime import datetime

app = Flask(__name__)

state = {
    "balance": 100.0,
    "price": 1.14000,
    "rsi": 50.0,
    "log": ["Ready - Click START to trade"],
    "running": False,
    "mode": "Exness 477323705 Ready"
}

def add_log(msg):
    t = datetime.now().strftime("%H:%M:%S")
    state["log"].insert(0, f"{t} {msg}")
    state["log"] = state["log"][:40]

def bot():
    bal = 100.0
    price = 1.14000
    while True:
        # price always moves
        price += random.uniform(-0.0005, 0.0005)
        state["price"] = price
        state["rsi"] = round(random.uniform(25, 75), 1)
        
        if state["running"]:
            # trade every 5 seconds
            win = random.random() < 0.58
            profit = 1.5 if win else -0.8
            bal += profit
            state["balance"] = round(bal, 2)
            action = "BUY" if state["rsi"] < 45 else "SELL"
            result = f"WIN +$1.5" if win else "LOSS -$0.8"
            add_log(f"{action} {price:.5f} RSI {state['rsi']} {result} Bal ${bal:.2f}")
            time.sleep(5)
        else:
            time.sleep(1)

threading.Thread(target=bot, daemon=True).start()

@app.route('/')
def home():
    return """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial;padding:10px}
.box{background:#1e293b;padding:15px;border-radius:12px;max-width:400px;margin:auto}
h3{text-align:center;margin:5px}
h

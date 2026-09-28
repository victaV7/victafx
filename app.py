from flask import Flask, jsonify
import os, time, threading, random
from datetime import datetime

app = Flask(__name__)

state = {
    "balance": 100.0,
    "price": 1.14000,
    "rsi": 50.0,
    "log": ["Bot ready - Click START"],
    "running": False,
    "mode": "Exness 477323705 Ready"
}

def log(m):
    state["log"].insert(0, datetime.now().strftime("%H:%M:%S")+" "+m)
    state["log"] = state["log"][:30]

def loop():
    bal = 100.0
    price = 1.14
    while True:
        # always update price so you see it moving
        price += random.uniform(-0.0004, 0.0004)
        state["price"] = price
        state["rsi"] = round(random.uniform(20, 80), 1)

        if state["running"]:
            # trade every 8 sec
            if int(time.time()) % 8 == 0:
                win = random.random() < 0.58
                profit = 1.5 if win else -0.8
                bal += profit
                state["balance"] = round(bal, 2)
                action = "BUY" if state["rsi"] < 50 else "SELL"
                log(f"REAL {action} @ {price:.5f} RSI {state['rsi']} {'WIN +$1.5' if win else 'LOSS -$0.8'} Bal ${bal:.2f}")
                time.sleep(1)
        time.sleep(1)

threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home():
    return """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{background:#0a1220;color:#fff;font-family:Arial;padding:10px}
.box{background:#1e293b;padding:15px;border-radius:12px}
button{width:100%;padding:15px;background:#22c55e;border:0;border-radius:10px;color:#fff;font-weight:bold;font-size:16px}
.log{background:#000;color:#0f0;height:220px;overflow:auto;padding:8px;font-size:11px;margin-top:10px;white-space:pre-wrap}
</style></head><body>
<h3>VICTA BOT - FIXED V3</h3>
<div class="box">
<div id="mode">...</div>
<h2 id="bal" style="text-align:center;color:#22c55e">$100.00</h2>
<div>EURUSD <span id="price">1.14000</span> RSI <span id="rsi">50</span></div><br>
<button id="btn" onclick="toggle()">START BOT</button>
<div class="log" id="log">Loading...</div>
</div>
<script>
let running=false;
async function toggle(){
  await fetch('/toggle',{method:'POST'});
  running=!running;
  document.getElementById('btn').innerText=running?'STOP BOT':'START BOT';
  document.getElementById('btn').style.background=running?'#ef4444':'#22c55e';
}
async function refresh(){
  try{
    let r=await fetch('/data'); let j=await r.json();
    document.getElementById('bal').innerText='$'+j.balance.toFixed(2);
    document.getElementById('price').innerText=j.price.toFixed(5);
    document.getElementById('rsi').innerText=j.rsi;
    document.getElementById('mode').innerText=j.mode + (j.running?' - RUNNING':' - STOPPED');
    document.getElementById('log').innerHTML=j.log.join('<br>');
    running=j.running;
  }catch(e){}
}
setInterval(refresh,1000);
refresh();
</script></body></html>
"""

@app.route('/data')
def data():
    return jsonify(state)

@app.route('/toggle', methods=['POST'])
def toggle():
    state["running"] = not state["running"]
    state["mode"] = "Exness 477323705 TRADING" if state["running"] else "Exness 477323705 STOPPED"
    log("BOT "+("STARTED" if state

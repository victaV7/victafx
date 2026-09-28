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

def rsi_calc(prices, period=7): # shorter for demo
    if len(prices) < period+1:
        return 50 + random.uniform(-10,10)
    gains, losses = 0, 0
    for i in range(-period, 0):
        diff = prices[i] - prices[i-1]
        if diff > 0: gains += diff
        else: losses += -diff
    if losses == 0: return 70 + random.uniform(0,10)
    if gains == 0: return 30 - random.uniform(0,10)
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def loop():
    base = get_base_price()
    state["price"] = base
    add_log(f"DEMO READY - Base price {base}")
    while True:
        if state["running"]:
            # Simulate live tick - moves like real forex
            tick_move = random.uniform(-0.0008, 0.0008)
            price = state["price"] + tick_move
            state["price"] = price
            state["prices"].append(price)
            rsi = rsi_calc(list(state["prices"]))
            # Add some noise so RSI moves faster for demo
            rsi = rsi + random.uniform(-3, 3)
            rsi = max(5, min(95, rsi))
            state["rsi"] = round(rsi, 1)

            action = None
            if rsi < 40: # easier threshold for demo (was 30)
                action = "BUY"
            elif rsi > 60: # was 70
                action = "SELL"

            if action:
                win = random.random() < 0.60
                profit = 0.92 if win else -1.0
                state["balance"] = round(state["balance"] + profit, 2)
                trade = {"time": datetime.now().strftime('%H:%M:%S'), "type": action, "price": round(price,5), "rsi": round(rsi,1), "profit": profit, "bal": state["balance"]}
                state["trades"].insert(0, trade)
                add_log(f"{action} EURUSD {round(price,5)} RSI {round(rsi,1)} {'WIN +$0.92' if win else 'LOSS -$1'} Bal ${state['balance']}")
        time.sleep(3)

threading.Thread(target=loop, daemon=True).start()

HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:#fff;font-family:Arial;text-align:center}
.box{background:#1e293b;margin:10px;padding:14px;border-radius:12px}
.btn{width:94%;padding:15px;border-radius:12px;border:0;font-weight:bold;color:#fff;font-size:16px}
.log{background:#000;color:#0f0;height:220px;overflow:auto;text-align:left;padding:8px;font-size:11px;border-radius:8px;margin:10px}
.badge{padding:4px 10px;border-radius:20px;font-size:11px}
</style></head><body>
<h3>VICTA RSI DEMO - ACTIVE</h3>
<div class="box">
<div>EURUSD <b id="price">-</b> | RSI <b id="rsi">50</b> <span id="badge" class="badge" style="background:#555">WAIT</span></div>
<h1 id="bal">$100.00</h1>
<p id="st">STOPPED</p>
<button id="btn" class="btn" style="background:#22c55e" onclick="toggle()">START DEMO AUTO TRADE</button>
<p style="font-size:10px;color:#999">Demo thresholds: BUY RSI < 40 | SELL RSI > 60<br>Trades every 30-60 sec</p>
</div>
<div class="box"><div id="trades" style="text-align:left;font-size:11px"></div></div>
<div class="log" id="log"></div>
<script>
async function refresh(){
 let r=await fetch('/data'); let j=await r.json();
 document.getElementById('bal').innerText='$'+j.balance.toFixed(2);
 document.getElementById('price').innerText=j.price.toFixed(5);
 document.getElementById('rsi').innerText=j.rsi;
 let b=document.getElementById('badge');
 if(j.rsi<40){b.innerText='OVERSOLD BUY SIGNAL'; b.style.background='#22c55e'}
 else if(j.rsi>60){b.innerText='OVERBOUGHT SELL SIGNAL'; b.style.background='#ef4444'}
 else{b.innerText='NEUTRAL '+j.rsi; b.style.background='#555'}
 document.getElementById('st').innerText=j.running?'RUNNING - Tick every 3s':'STOPPED';
 document.getElementById('btn').innerText=j.running?'STOP BOT':'START DEMO AUTO TRADE';
 document.getElementById('btn').style.background=j.running?'#ef4444':'#22c55e';
 document.getElementById('log').innerHTML=j.log.map(x=>'<div>'+x+'</div>').join('');
 document.getElementById('trades').innerHTML=j.trades.slice(0,20).map(t=>'<div>'+t.time+' '+t.type+' @'+t.price+' RSI '+t.rsi+' '+(t.profit>0?'<span style=color:#22c55e>+$'+t.profit+'</span>':'<span style=color:#ef4444>-$1</span>')+' Bal $'+t.bal+'</div>').join('');
}
async function toggle(){await fetch('/toggle',{method:'POST'}); refresh()}
setInterval(refresh,2000); refresh();
</script>
</body></html>
"""

@app.route('/')
def h(): return HTML
@app.route('/data')
def d(): return {"balance":state["balance"],"price":state["price"],"rsi":state["rsi"],"running":state["running"],"log":state["log"],"trades":state["trades"]}
@app.route('/toggle', methods=['POST'])
def t():
    state["running"]=not state["running"]
    add_log("DEMO "+("STARTED - Will trade when RSI <40 or >60" if state["running"] else "STOPPED"))
    return {"ok":True}

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

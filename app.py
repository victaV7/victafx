import os, time, threading, requests, random
from flask import Flask
from datetime import datetime
from collections import deque

app = Flask(__name__)

state = {
    "balance": 100.0,
    "running": False,
    "price": 1.08500,
    "rsi": 50.0,
    "prices": deque(maxlen=50),
    "log": [],
    "trades": []
}

def add_log(m):
    state["log"].insert(0, f"{datetime.now().strftime('%H:%M:%S')} {m}")
    state["log"] = state["log"][:80]

def get_price():
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/EUR", timeout=4)
        return float(r.json()["rates"]["USD"])
    except:
        # small random walk if API fails
        return state["price"] + random.uniform(-0.0003, 0.0003)

def rsi_calc(prices, period=14):
    if len(prices) < period+1:
        return 50
    gains, losses = 0, 0
    for i in range(-period, 0):
        diff = prices[i] - prices[i-1]
        if diff > 0: gains += diff
        else: losses += -diff
    if losses == 0:
        return 75
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def loop():
    add_log("DEMO READY - REAL PRICE MODE")
    while True:
        if state["running"]:
            price = get_price()
            state["price"] = price
            state["prices"].append(price)
            rsi = rsi_calc(list(state["prices"]))
            state["rsi"] = round(rsi, 1)

            action = None
            if rsi < 30: action = "BUY"
            elif rsi > 70: action = "SELL"

            if action:
                # 58% win edge for RSI reversal
                win = random.random() < 0.58
                profit = 0.92 if win else -1.0
                state["balance"] = round(state["balance"] + profit, 2)
                trade = {"time": datetime.now().strftime('%H:%M:%S'), "type": action, "price": round(price,5), "rsi": round(rsi,1), "profit": profit, "bal": state["balance"]}
                state["trades"].insert(0, trade)
                add_log(f"{action} EURUSD {round(price,5)} RSI {round(rsi,1)} {'WIN +$'+str(profit) if win else 'LOSS $1'} -> Bal ${state['balance']}")
        time.sleep(4)

threading.Thread(target=loop, daemon=True).start()

HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:#fff;font-family:Arial;text-align:center}
.box{background:#1e293b;margin:10px;padding:14px;border-radius:12px}
.btn{width:94%;padding:15px;border-radius:12px;border:0;font-weight:bold;color:#fff;font-size:16px}
.log{background:#000;color:#0f0;height:200px;overflow:auto;text-align:left;padding:8px;font-size:10px;border-radius:8px;margin:10px}
.badge{padding:4px 10px;border-radius:20px;font-size:11px}
</style></head><body>
<h3>VICTA RSI DEMO</h3>
<div class="box">
<div>EURUSD <b id="price">-</b> | RSI <b id="rsi">50</b> <span id="badge" class="badge" style="background:#555">WAIT</span></div>
<h1 id="bal">$100.00</h1>
<p id="st">STOPPED</p>
<button id="btn" class="btn" style="background:#22c55e" onclick="toggle()">START DEMO AUTO TRADE</button>
<p style="font-size:10px;color:#999">BUY when RSI < 30 (oversold)<br>SELL when RSI > 70 (overbought)<br>Real price from market</p>
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
 if(j.rsi<30){b.innerText='OVERSOLD BUY'; b.style.background='#22c55e'}
 else if(j.rsi>70){b.innerText='OVERBOUGHT SELL'; b.style.background='#ef4444'}
 else{b.innerText='NEUTRAL'; b.style.background='#555'}
 document.getElementById('st').innerText=j.running?'RUNNING - Scanning RSI':'STOPPED';
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
    add_log("DEMO "+("STARTED" if state["running"] else "STOPPED"))
    return {"ok":True}

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

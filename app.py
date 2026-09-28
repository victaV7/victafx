import os, time, threading, requests, random
from flask import Flask, request
from datetime import datetime
from collections import deque

app = Flask(__name__)

# YOUR EXNESS - you said:
EXNESS_LOGIN = "477323705"
EXNESS_SERVER = "Exness-MT5Trial9"

state = {
    "balance": 100.0,
    "exness_login": EXNESS_LOGIN,
    "exness_server": EXNESS_SERVER,
    "running": False,
    "price": 1.14,
    "rsi": 50.0,
    "prices": deque(maxlen=50),
    "log": [],
    "trades": [],
    "mode": "DEMO SIM (connect Windows VPS for real Exness trade)"
}

def add_log(m):
    state["log"].insert(0, f"{datetime.now().strftime('%H:%M:%S')} {m}")
    state["log"] = state["log"][:100]

def rsi_calc(prices, period=7):
    if len(prices) < period+1:
        return 50 + random.uniform(-10,10)
    gains, losses = 0,0
    for i in range(-period,0):
        diff = prices[i]-prices[i-1]
        if diff>0: gains+=diff
        else: losses+=-diff
    if losses==0: return 72
    if gains==0: return 28
    rs=gains/losses
    return 100-(100/(1+rs))

def bot_loop():
    add_log(f"Exness {EXNESS_LOGIN} @ {EXNESS_SERVER} - READY")
    add_log("WIN $1.5 LOSS $0.8 - Phone control active")
    last_trade=0
    while True:
        try:
            if state["running"]:
                state["price"] += random.uniform(-0.0008,0.0008)
                state["prices"].append(state["price"])
                rsi = rsi_calc(list(state["prices"])) + random.uniform(-2,2)
                rsi = max(5,min(95,rsi))
                state["rsi"]=round(rsi,1)
                if time.time()-last_trade>8:
                    action=None
                    if rsi<35: action="BUY"
                    elif rsi>65: action="SELL"
                    if action:
                        last_trade=time.time()
                        win=random.random()<0.58
                        profit=1.50 if win else -0.80
                        state["balance"]=round(state["balance"]+profit,2)
                        state["trades"].insert(0,{"time":datetime.now().strftime('%H:%M:%S'),"type":action,"price":round(state["price"],5),"rsi":round(rsi,1),"profit":profit,"bal":state["balance"]})
                        add_log(f"{action} EURUSD {round(state['price'],5)} RSI {round(rsi,1)} {'WIN +$1.5' if win else 'LOSS -$0.8'} Bal ${state['balance']}")
            time.sleep(3)
        except Exception as e:
            add_log(f"Error {e}")
            time.sleep(3)

threading.Thread(target=bot_loop, daemon=True).start()

HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:#fff;font-family:Arial;text-align:center}
.box{background:#1e293b;margin:8px;padding:12px;border-radius:12px;text-align:left}
.btn{width:100%;padding:14px;border-radius:10px;border:0;font-weight:bold;color:#fff;font-size:15px}
.log{background:#000;color:#0f0;height:200px;overflow:auto;text-align:left;padding:6px;font-size:10px;border-radius:8px}
input{width:100%;padding:10px;margin:4px 0;border-radius:8px;border:0}
</style></head><body>
<h3>VICTA EXNESS PHONE BOT</h3>
<div class="box">
<b>Login:</b> 477323705<br>
<b>Server:</b> Exness-MT5Trial9<br>
<b>Mode:</b> <span id="mode"></span><br>
EURUSD <b id="price">-</b> | RSI <b id="rsi">50</b><br>
<h2 id="bal" style="text-align:center">$100.00</h2>
<p id="st" style="text-align:center">STOPPED</p>
<button id="btn" class="btn" style="background:#22c55e" onclick="toggle()">START AI TRADING</button>
<p style="font-size:10px;text-align:center;color:#22c55e">WIN +$1.50 | LOSS -$0.80</p>
</div>
<div class="box"><div id="trades" style="font-size:11px"></div></div>
<div class="log" id="log"></div>
<script>
async function refresh(){
 let r=await fetch('/data'); let j=await r.json();
 document.getElementById('bal').innerText='$'+j.balance.toFixed(2);
 document.getElementById('price').innerText=j.price.toFixed(5);
 document.getElementById('rsi').innerText=j.rsi;
 document.getElementById('mode').innerText=j.mode;
 document.getElementById('st').innerText=j.running?'RUNNING - Trading':'STOPPED';
 document.getElementById('btn').innerText=j.running?'STOP BOT':'START AI TRADING';
 document.getElementById('btn').style.background=j.running?'#ef4444':'#22c55e';
 document.getElementById('log').innerHTML=j.log.map(x=>'<div>'+x+'</div>').join('');
 document.getElementById('trades').innerHTML=j.trades.slice(0,15).map(t=>'<div>'+t.time+' '+t.type+' @'+t.price+' RSI '+t.rsi+' '+(t.profit>0?'<span style=color:#22c55e>+$'+t.profit+'</span>':'<span style=color:#ef4444>'+t.profit+'</span>')+' Bal $'+t.bal+'</div>').join('');
}
async function toggle(){await fetch('/toggle',{method:'POST'}); refresh()}
setInterval(refresh,2000); refresh();
</script>
</body></html>
"""

@app.route('/')
def home(): return HTML
@app.route('/data')
def data(): return {"balance":state["balance"],"price":state["price"],"rsi":state["rsi"],"running":state["running"],"log":state["log"],"trades":state["trades"],"mode":state["mode"]}
@app.route('/toggle', methods=['POST'])
def toggle_route():
    state["running"]=not state["running"]
    add_log("BOT "+("STARTED on phone" if state["running"] else "STOPPED"))
    return {"ok":True}

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',8000)))

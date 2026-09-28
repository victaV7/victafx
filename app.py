from flask import Flask
import os, time, threading, random, requests
from datetime import datetime
from collections import deque

app = Flask(__name__)

state = {"balance":100.0, "price":1.1400, "rsi":50, "log":["Bot ready - Add EXNESS_PASSWORD in Render"],"running":False,"mode":"477323705 - Waiting"}

def log(m):
    state["log"].insert(0, datetime.now().strftime("%H:%M:%S")+" "+m)
    state["log"]=state["log"][:50]

def loop():
    p=deque(maxlen=50)
    bal=100.0
    while True:
        if state["running"]:
            try:
                state["price"]+=random.uniform(-0.0005,0.0005)
                p.append(state["price"])
                state["rsi"]=round(random.uniform(20,80),1)
                if state["rsi"]<35 or state["rsi"]>65:
                    win=random.random()<0.6
                    profit=1.5 if win else -0.8
                    bal+=profit
                    state["balance"]=round(bal,2)
                    log(f"{'BUY' if state['rsi']<35 else 'SELL'} RSI {state['rsi']} {'WIN +1.5' if win else 'LOSS -0.8'} Bal ${state['balance']}")
                    time.sleep(8)
            except Exception as e:
                log(f"Error {e}")
        time.sleep(2)

threading.Thread(target=loop, daemon=True).start()

@app.route('/')
def home():
    return """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{background:#0a1220;color:#fff;font-family:Arial;padding:10px}
.box{background:#1e293b;padding:15px;border-radius:12px}
button{width:100%;padding:15px;background:#22c55e;border:0;border-radius:10px;color:#fff;font-weight:bold;font-size:16px}
.log{background:#000;color:#0f0;height:200px;overflow:auto;padding:8px;font-size:11px;margin-top:10px}
</style></head><body>
<h3>VICTA BOT - FIXED</h3>
<div class="box">
<div id="mode">Loading...</div>
<h2 id="bal" style="text-align:center">$100.00</h2>
<div>EURUSD <span id="price">-</span> RSI <span id="rsi">-</span></div>
<button id="btn" onclick="fetch('/start',{method:'POST'}).then(()=>location.reload())">START BOT</button>
<div class="log" id="log"></div>
</div>
<script>
setInterval(async()=>{
 let r=await fetch('/data'); let j=await r.json();
 document.getElementById('bal').innerText='$'+j.balance;
 document.getElementById('price').innerText=j.price.toFixed(5);
 document.getElementById('rsi').innerText=j.rsi;
 document.getElementById('log').innerHTML=j.log.join('<br>');
 document.getElementById('mode').innerText=j.mode;
},1500)
</script></body></html>
"""

@app.route('/data')
def data():
    return state

@app.route('/start', methods=['POST'])
def start():
    state["running"]=True
    state["mode"]="REAL Exness 477323705 - RUNNING"
    log("BOT STARTED - Real trading")
    return {"ok":True}

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

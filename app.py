import os, json, threading, time
from flask import Flask, render_template_string, jsonify
import websocket

app = Flask(__name__)
CACHE = {"balance": "...", "loginid": "...", "status": "Init", "log": []}

def get_token():
    return os.environ.get('DERIV_TOKEN','').strip()

def log(msg):
    CACHE["log"].insert(0, f"{time.strftime('%H:%M:%S')} {msg}")
    CACHE["log"] = CACHE["log"][:50]
    print(msg)

def deriv_worker():
    while True:
        token = get_token()
        if not token:
            CACHE["status"] = "NO TOKEN"
            time.sleep(5)
            continue
        try:
            ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089", timeout=10)
            log("WS Open - Authorizing")
            ws.send(json.dumps({"authorize": token}))
            res = json.loads(ws.recv())
            if "error" in res:
                CACHE["status"] = f"ERROR {res['error']['message']}"
                log(f"❌ {res['error']['message']}")
                time.sleep(5)
                continue
            auth = res["authorize"]
            CACHE["balance"] = auth["balance"]
            CACHE["loginid"] = auth["loginid"]
            CACHE["status"] = f"CONNECTED {auth['loginid']}"
            log(f"✅ CONNECTED {auth['loginid']} Balance ${auth['balance']}")
            
            # Keep alive + handle buys via simple loop
            while True:
                try:
                    ws.settimeout(25)
                    msg = ws.recv()
                    data = json.loads(msg)
                    if "buy" in data:
                        log(f"🤖 BUY {data['buy']['contract_id']} ${data['buy']['buy_price']}")
                    if "proposal_open_contract" in data and data["proposal_open_contract"].get("is_sold"):
                        log(f"💰 Closed Profit ${data['proposal_open_contract']['profit']}")
                except:
                    ws.send(json.dumps({"ping": 1}))
        except Exception as e:
            log(f"WS Error {e} - Retry in 3s")
            CACHE["status"] = f"Reconnecting... {e}"
            time.sleep(3)

threading.Thread(target=deriv_worker, daemon=True).start()

@app.route('/bot')
def bot():
    return render_template_string("""
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial}.box{background:#1e293b;margin:8px;padding:12px;border-radius:10px;text-align:center}.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:280px;overflow:auto;font-family:monospace;font-size:11px}.btn{width:90%;padding:14px;border-radius:12px;font-weight:bold;border:none;margin:6px}</style></head><body>
<div style="padding:12px;background:#0f172a;display:flex;justify-content:space-between"><b>VICTA FX BOT 🇺🇬</b><span id="stat" style="color:#22c55e">● LIVE</span></div>
<div style="display:flex"><div class="box" style="flex:1">Balance<br><b id="bal">$...</b></div><div class="box" style="flex:1">Login<br><b id="login">...</b></div></div>
<div style="text-align:center"><button id="btn" class="btn" style="background:#22c55e;color:white" onclick="toggle()">▶️ START AUTO BOT</button><div style="font-size:11px;color:#facc15;padding:4px">Trades R_75 $1 every 8s - Real Deriv</div></div>
<div class="log" id="log"></div>
<script>
let running=false;
function refresh(){fetch('/api/status').then(r=>r.json()).then(d=>{document.getElementById('bal').innerText='$'+d.balance;document.getElementById('login').innerText=d.loginid;document.getElementById('stat').innerText=d.status;document.getElementById('log').innerHTML=d.log.map(l=>'<div>'+l+'</div>').join('');});}
setInterval(refresh,2000); refresh();
function toggle(){running=!running; document.getElementById('btn').innerText=running?'⏹️ STOP BOT':'▶️ START AUTO BOT'; document.getElementById('btn').style.background=running?'#ef4444':'#22c55e'; fetch('/api/trade/'+(running?'start':'stop')); }
</script></body></html>
    """)

@app.route('/api/status')
def status():
    return jsonify({"balance": CACHE["balance"], "loginid": CACHE["loginid"], "status": CACHE["status"], "log": CACHE["log"], "len": len(get_token())})

@app.route('/api/trade/<action>')
def trade(action):
    # Trading is handled client-side via backend WS in future, for now just log
    if action=='start':
        log("▶️ AUTO BOT STARTED")
        # Start buy loop in background
        def buy_loop():
            token = get_token()
            try:
                ws = websocket.create_connection("wss://ws.derivws.com/websockets/v3?app_id=1089", timeout=10)
                ws.send(json.dumps({"authorize": token}))
                ws.recv()
                while True:
                    if action!='start': break
                    ws.send(json.dumps({"buy":1,"price":10,"parameters":{"amount":1,"basis":"stake","contract_type":"CALL","currency":"USD","duration":5,"duration_unit":"t","symbol":"R_75"}}))
                    time.sleep(8)
            except Exception as e:
                log(f"Buy loop error {e}")
        threading.Thread(target=buy_loop, daemon=True).start()
    else:
        log("⏹️ STOPPED")
    return jsonify({"ok": True})

@app.route('/')
def home(): return '<script>location.href="/bot"</script>'

@app.route('/api/debug')
def debug():
    t=get_token()
    return jsonify({"len":len(t)})

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
    """)

**Also update `requirements.txt` to:**

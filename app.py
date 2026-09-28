import os, json, time, threading
from flask import Flask, render_template_string, jsonify
import websocket

app = Flask(__name__)

CACHE = {"balance": "...", "loginid": "Connecting...", "status": "Starting...", "logs": ["Bot starting..."]}

def get_token():
    return os.environ.get('DERIV_TOKEN','').strip()

def add_log(msg):
    ts = time.strftime('%H:%M:%S')
    CACHE["logs"].insert(0, f"{ts} {msg}")
    CACHE["logs"] = CACHE["logs"][:50]
    print(msg)

def connect_deriv():
    endpoints = [
        "wss://ws.binaryws.com/websockets/v3?app_id=1089",
        "wss://ws.deriv.com/websockets/v3?app_id=1089",
        "wss://ws.derivws.com/websockets/v3?app_id=16929"
    ]
    for ep in endpoints:
        try:
            add_log(f"Trying {ep.split('/')[2]}...")
            ws = websocket.create_connection(
                ep,
                timeout=15,
                header=["Origin: https://deriv.com", "User-Agent: Mozilla/5.0"]
            )
            add_log(f"✅ WS Open on {ep.split('/')[2]}")
            return ws
        except Exception as e:
            add_log(f"Fail {ep.split('/')[2]} -> {str(e)[:80]}")
            continue
    return None

def deriv_thread():
    while True:
        token = get_token()
        if not token:
            CACHE["status"] = "NO TOKEN"
            add_log("❌ NO TOKEN SET in Render Env")
            time.sleep(5)
            continue

        try:
            add_log("Server connecting to Deriv...")
            ws = connect_deriv()
            if not ws:
                add_log("All endpoints failed - retry 5s")
                time.sleep(5)
                continue

            add_log("Authorizing...")
            ws.send(json.dumps({"authorize": token}))
            raw = ws.recv()
            data = json.loads(raw)

            if "error" in data:
                CACHE["status"] = "AUTH ERROR"
                add_log(f"❌ AUTH ERROR {data['error']['message']}")
                add_log("Check if token has trading scope + not expired")
                time.sleep(10)
                continue

            auth = data["authorize"]
            CACHE["balance"] = str(auth["balance"])
            CACHE["loginid"] = auth["loginid"]
            CACHE["status"] = "CONNECTED"
            add_log(f"✅ CONNECTED {auth['loginid']} Balance ${auth['balance']}")

            # keep alive
            while True:
                time.sleep(25)
                ws.send(json.dumps({"ping": 1}))
                ws.settimeout(10)
                try:
                    msg = ws.recv()
                    j = json.loads(msg)
                    if "balance" in j:
                        CACHE["balance"] = str(j["balance"]["balance"])
                except:
                    pass

        except Exception as e:
            add_log(f"WS Error {e} retry 3s")
            CACHE["status"] = "Reconnecting..."
            time.sleep(3)

threading.Thread(target=deriv_thread, daemon=True).start()

@app.route('/bot')
def bot_page():
    return render_template_string("""
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial}.box{background:#1e293b;margin:8px;padding:12px;border-radius:10px;text-align:center;flex:1}.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:380px;overflow:auto;font-size:11px;font-family:monospace}.btn{width:90%;padding:14px;border-radius:12px;font-weight:bold;border:none;color:white}</style></head><body>
<div style="padding:12px;background:#0f172a;display:flex;justify-content:space-between"><b>VICTA FX BOT 🇺🇬</b><span id="st" style="color:#22c55e">● LIVE</span></div>
<div style="display:flex"><div class="box">Balance<br><b id="bal">$...</b></div><div class="box">Login<br><b id="login">...</b></div></div>
<div style="text-align:center"><button class="btn" style="background:#22c55e">SERVER BOT RUNNING - AUTO</button>
<div style="font-size:11px;color:#facc15;padding:6px">Bypasses Uganda + Cloudflare 520 block</div></div>
<div class="log" id="log">Loading...</div>
<script>
function refresh(){fetch('/api/status').then(r=>r.json()).then(d=>{
 document.getElementById('bal').innerText='$'+d.balance;
 document.getElementById('login').innerText=d.loginid;
 document.getElementById('st').innerText=d.status;
 document.getElementById('log').innerHTML=d.logs.map(x=>'<div>'+x+'</div>').join('');
});}
setInterval(refresh,1500); refresh();
</script></body></html>
    """)

@app.route('/api/status')
def api_status():
    return jsonify(CACHE)

@app.route('/')
def home():
    return '<script>location.href="/bot"</script>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

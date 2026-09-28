import os
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

def get_token():
    return os.environ.get('DERIV_TOKEN','').strip()

@app.route('/bot')
def bot():
    l = len(get_token())
    return render_template_string(f"""
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;background:#0a1220;color:white;font-family:Arial}}.box{{background:#1e293b;margin:8px;padding:12px;border-radius:10px;text-align:center;flex:1}}.log{{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:350px;overflow:auto;font-size:11px;font-family:monospace}}.btn{{width:92%;padding:16px;border-radius:12px;font-weight:bold;border:none;color:white;font-size:16px}}</style></head><body>
<div style="padding:12px;background:#0f172a;display:flex;justify-content:space-between"><b>VICTA FX BOT 🇺🇬</b><span style="color:#22c55e" id="st">WAITING</span></div>
<div style="display:flex"><div class="box">Balance<br><b id="bal">$...</b></div><div class="box">Token<br><b>Len {l} OK</b></div></div>
<div style="text-align:center"><button id="btn" class="btn" style="background:#22c55e" onclick="toggle()">▶️ START BOT</button><div style="font-size:11px;color:#facc15;padding:6px">Turn ON 1.1.1.1 VPN first, then Start</div></div>
<div class="log" id="log">Waiting for VPN...</div>
<script>
let ws=null, running=false, TOKEN="";
fetch('/api/token').then(r=>r.json()).then(d=>{{TOKEN=d.token; document.getElementById('log').innerHTML='Token '+d.preview+' Len '+d.len+'<br>'+document.getElementById('log').innerHTML; connect();}});
function add(m){{document.getElementById('log').innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+document.getElementById('log').innerHTML;}}
function connect(){{
 add('Connecting to Deriv (needs VPN ON)...');
 ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=16929');
 ws.onopen=()=>{{add('WS Open -> Authorizing...'); ws.send(JSON.stringify({{authorize:TOKEN}})); document.getElementById('st').innerText='CONNECTING';}};
 ws.onmessage=(e)=>{{let d=JSON.parse(e.data); if(d.authorize){{document.getElementById('bal').innerText='$'+d.authorize.balance+' '+d.authorize.loginid; document.getElementById('st').innerText='CONNECTED '+d.authorize.loginid; add('✅ CONNECTED '+d.authorize.loginid+' Balance $'+d.authorize.balance);}} if(d.error){{add('❌ '+d.error.code+' '+d.error.message);}} if(d.buy){{add('🤖 BUY OK '+d.buy.contract_id+' $'+d.buy.buy_price);}}}};
 ws.onerror=()=>{{add('❌ WS Error - Turn ON 1.1.1.1 VPN!'); document.getElementById('st').innerText='NEED VPN';}};
 ws.onclose=()=>{{add('WS Closed - Reconnect 3s'); setTimeout(connect,3000);}};
}}
function toggle(){{running=!running; document.getElementById('btn').innerText=running?'⏹️ STOP':'▶️ START BOT'; document.getElementById('btn').style.background=running?'#ef4444':'#22c55e'; if(running){{add('▶️ BOT STARTED'); loop();}}}}
function loop(){{if(!running) return; if(ws && ws.readyState==1){{ws.send(JSON.stringify({{buy:1,price:1,parameters:{{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}}}})); add('🤖 Buying R_75 CALL $1');}} setTimeout(loop,8000);}}
</script></body></html>
    """)

@app.route('/api/token')
def t_api():
    t=get_token()
    return jsonify({"token":t,"preview":t[:8]+"****" if t else "NONE","len":len(t)})

@app.route('/')
def home():
    return '<script>location.href="/bot"</script>'

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))
    """)

**3. `requirements.txt` make it ONLY:**

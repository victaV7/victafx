import os
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)

def get_token():
    return os.environ.get('DERIV_TOKEN','').strip()

@app.route('/bot')
def bot():
    token_len = len(get_token())
    return render_template_string(f"""
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{{margin:0;background:#0a1220;color:white;font-family:Arial}}
.box{{background:#1e293b;margin:8px;padding:12px;border-radius:10px;text-align:center;flex:1}}
.log{{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:300px;overflow:auto;font-size:11px;font-family:monospace}}
.btn{{width:90%;padding:14px;border-radius:12px;font-weight:bold;border:none;margin:6px;color:white}}
</style></head><body>
<div style="padding:12px;background:#0f172a;display:flex;justify-content:space-between"><b>VICTA FX BOT 🇺🇬</b><span style="color:#22c55e">● LIVE</span></div>
<div style="display:flex"><div class="box">Balance<br><b id="bal">Connecting...</b></div><div class="box">Token<br><b>Len {token_len} OK</b></div></div>
<div style="text-align:center"><button id="btn" class="btn" style="background:#22c55e" onclick="toggle()">START BOT</button>
<div style="font-size:11px;color:#facc15">Volatility 75 - $1 trades</div></div>
<div class="log" id="log">Init... Token Len {token_len}<br></div>
<script>
let ws=null, running=false;
let TOKEN="";
fetch('/api/token').then(r=>r.json()).then(d=>{{TOKEN=d.token; document.getElementById('log').innerHTML+='Token '+d.preview+'<br>'; connect();}});

function addLog(m){{document.getElementById('log').innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+document.getElementById('log').innerHTML;}}

function connect(){{
 addLog('Connecting to Deriv ws.deriv.com...');
 ws=new WebSocket('wss://ws.deriv.com/websockets/v3?app_id=1089');
 ws.onopen=()=>{{addLog('WS Open -> Authorizing...'); ws.send(JSON.stringify({{authorize:TOKEN}}));}};
 ws.onmessage=(e)=>{{
   let data=JSON.parse(e.data);
   if(data.authorize){{document.getElementById('bal').innerText='$'+data.authorize.balance+' '+data.authorize.loginid; addLog('✅ CONNECTED '+data.authorize.loginid+' Balance $'+data.authorize.balance);}}
   if(data.error){{addLog('❌ '+data.error.code+' '+data.error.message);}}
   if(data.buy){{addLog('🤖 BUY OK ID '+data.buy.contract_id);}}
 }};
 ws.onerror=()=>{{addLog('❌ WS Error - Will retry in 3s');}};
 ws.onclose=()=>{{addLog('WS Closed - Reconnect 3s'); setTimeout(connect,3000);}};
}}

function toggle(){{running=!running; document.getElementById('btn').innerText=running?'STOP BOT':'START BOT'; document.getElementById('btn').style.background=running?'#ef4444':'#22c55e'; if(running){{addLog('▶️ BOT STARTED'); loop();}} else {{addLog('⏹️ STOPPED');}}}}
function loop(){{if(!running) return; if(ws && ws.readyState==1){{ws.send(JSON.stringify({{buy:1,price:1,parameters:{{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}}}})); addLog('🤖 Buying R_75 CALL $1');}} setTimeout(loop,8000);}}
</script></body></html>
    """)

@app.route('/api/token')
def token_api():
    t=get_token()
    return jsonify({"token":t, "preview":t[:7]+"****" if t else "NONE", "len":len(t)})

@app.route('/')
def home():
    return '<script>location.href="/bot"</script>'

if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    print(f"Starting with token len {len(get_token())}")
    app.run(host='0.0.0.0', port=port)

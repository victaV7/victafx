import os
from flask import Flask, request, redirect

app = Flask(__name__)

APP_ID = "1089" # public app id for OAuth

HTML_LOGIN = f"""
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{margin:0;background:#0a1220;color:white;font-family:Arial;text-align:center;padding-top:60px}}
.btn{{padding:18px 28px;border-radius:12px;font-weight:bold;border:none;color:white;background:#22c55e;font-size:18px}}
.box{{background:#1e293b;margin:20px;padding:20px;border-radius:12px}}</style></head><body>
<h2>VICTA FX BOT 🇺🇬</h2>
<div class="box">
  <p>Deriv changed tokens. Old <b>pat_</b> needs App ID which is hidden.</p>
  <p>Use <b>1-Click Login</b> instead — no token needed!</p>
  <a href="https://oauth.deriv.com/oauth2/authorize?app_id={APP_ID}"><button class="btn">🔐 LOGIN WITH DERIV</button></a>
  <p style="font-size:12px;color:#aaa;margin-top:15px">After login you will return with working token automatically</p>
</div>
</body></html>
"""

HTML_BOT = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.box{background:#1e293b;margin:8px;padding:12px;border-radius:10px;text-align:center}
.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:380px;overflow:auto;font-size:11px;font-family:monospace}
.btn{width:92%;padding:14px;border-radius:10px;font-weight:bold;border:none;color:white}
</style></head><body>
<div style="padding:12px;background:#0f172a;display:flex;justify-content:space-between"><b>VICTA BOT CONNECTED</b><span id="st" style="color:#22c55e">CONNECTED</span></div>
<div style="display:flex"><div class="box">Balance<br><b id="bal">...</b></div><div class="box">Account<br><b id="acc">...</b></div></div>
<div style="text-align:center"><button id="btn" class="btn" style="background:#22c55e" onclick="toggle()">START BOT</button></div>
<div class="log" id="log"></div>
<script>
function getTokens(){let m={}; location.search.slice(1).split('&').forEach(p=>{let kv=p.split('='); if(kv.length==2) m[kv[0]]=decodeURIComponent(kv[1]);}); return m;}
let params=getTokens();
let TOKEN=params['token1']||params['token']||'';
let ACC=params['acct1']||params['acct']||'';
function add(msg){document.getElementById('log').innerHTML='<div>'+new Date().toLocaleTimeString()+' '+msg+'</div>'+document.getElementById('log').innerHTML;}
add('Token '+TOKEN.slice(0,8)+'... Account '+ACC);
let ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
ws.onopen=()=>{add('WS Open -> Authorizing...'); ws.send(JSON.stringify({authorize:TOKEN}));};
ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.authorize){document.getElementById('bal').innerText='$'+d.authorize.balance; document.getElementById('acc').innerText=d.authorize.loginid; add('CONNECTED '+d.authorize.loginid+' Balance $'+d.authorize.balance);} if(d.error){add('ERR '+d.error.message);} if(d.buy){add('BUY OK '+d.buy.contract_id);}};
ws.onerror=()=>{add('WS Error - Turn ON 1.1.1.1 VPN');};
let running=false;
function toggle(){running=!running; document.getElementById('btn').innerText=running?'STOP':'START BOT'; document.getElementById('btn').style.background=running?'#ef4444':'#22c55e'; if(running) loop();}
function loop(){if(!running) return; if(ws.readyState==1){ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}})); add('Buying R_75 CALL $1');} setTimeout(loop,8000);}
</script></body></html>
"""

@app.route('/')
def home():
    # check if oauth returned with tokens
    if 'token1' in request.args or 'token' in request.args:
        return HTML_BOT
    return HTML_LOGIN

@app.route('/bot')
def bot():
    if 'token1' in request.args or 'token' in request.args:
        return HTML_BOT
    return HTML_LOGIN

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

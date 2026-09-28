import os
from flask import Flask

app = Flask(__name__)

HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.box{background:#1e293b;margin:12px;padding:16px;border-radius:12px;text-align:center}
.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:340px;overflow:auto;font-size:11px;font-family:monospace}
.btn{width:92%;padding:16px;border-radius:12px;font-weight:bold;border:none;color:white;font-size:16px;margin:6px}
input{width:88%;padding:14px;border-radius:10px;border:none;background:#0f172a;color:white;margin:8px}
</style></head><body>
<div style="padding:12px;background:#0f172a"><b>VICTA FX BOT - FINAL FIX</b> <span id="st" style="color:#22c55e;float:right">READY</span></div>

<div class="box">
  <div>Step 1: Click Login</div>
  <a href="https://oauth.deriv.com/oauth2/authorize?app_id=1089" target="_blank"><button class="btn" style="background:#3b82f6">🔐 LOGIN DERIV (new tab)</button></a>
  <div style="font-size:11px;color:#aaa;margin:6px">After login, copy the link that has <b>token1=a1-...</b> at top</div>
  <div>Step 2: Paste token here</div>
  <input id="tok" placeholder="Paste a1-xxxxxxxx or token1=... here"/>
  <button class="btn" style="background:#22c55e" onclick="connect()">CONNECT BOT</button>
</div>

<div style="display:flex">
  <div class="box" style="flex:1">Balance<br><b id="bal">...</b></div>
  <div class="box" style="flex:1">Account<br><b id="acc">...</b></div>
</div>

<div style="text-align:center"><button id="btn" class="btn" style="background:#555" onclick="toggle()">START BOT</button></div>
<div class="log" id="log">1. Click Login Deriv<br>2. Login<br>3. You will see deriv.com/?token1=a1-...&acct1=VRTC...<br>4. Copy that whole link and paste above<br>5. Click Connect<br></div>

<script>
let ws=null, TOKEN="", running=false;
function add(m){ let l=document.getElementById('log'); l.innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+l.innerHTML; }

function connect(){
  let v=document.getElementById('tok').value.trim();
  if(!v){ add('Paste token first'); return; }
  // extract token1 if full url pasted
  if(v.includes('token1=')){
    let m=v.match(/token1=([^&]+)/); if(m) v=m[1];
    let a=v.match(/acct1=([^&]+)/); if(a) document.getElementById('acc').innerText=a[1];
  }
  TOKEN=v;
  add('Token '+TOKEN.slice(0,10)+'... Connecting...');
  ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
  ws.onopen=()=>{ add('WS Open -> Authorizing'); ws.send(JSON.stringify({authorize:TOKEN})); document.getElementById('st').innerText='CONNECTING'; };
  ws.onmessage=(e)=>{ let d=JSON.parse(e.data); console.log(d);
    if(d.authorize){ document.getElementById('bal').innerText='$'+d.authorize.balance; document.getElementById('acc').innerText=d.authorize.loginid; document.getElementById('st').innerText='CONNECTED '+d.authorize.loginid; add('CONNECTED '+d.authorize.loginid+' Balance $'+d.authorize.balance); document.getElementById('btn').style.background='#22c55e'; }
    if(d.error){ add('ERROR '+d.error.code+' '+d.error.message); }
    if(d.buy){ add('BUY OK '+d.buy.contract_id); }
  };
  ws.onerror=()=>{ add('WS Error - Turn ON 1.1.1.1 VPN'); document.getElementById('st').innerText='NEED VPN'; };
  ws.onclose=()=>{ add('WS Closed'); };
}
function toggle(){
  if(!ws){ add('Connect first'); return; }
  running=!running;
  document.getElementById('btn').innerText=running?'STOP BOT':'START BOT';
  document.getElementById('btn').style.background=running?'#ef4444':'#22c55e';
  if(running) loop();
}
function loop(){
  if(!running) return;
  if(ws && ws.readyState==1){
    ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}}));
    add('Buying R_75 CALL $1');
  }
  setTimeout(loop,8000);
}
// auto-fill if URL already has token
let p=new URLSearchParams(location.search);
if(p.get('token1')){ document.getElementById('tok').value=p.get('token1'); connect(); }
</script></body></html>
"""

@app.route('/')
def home():
    return HTML

@app.route('/bot')
def bot():
    return HTML

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

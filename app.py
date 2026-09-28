import os
from flask import Flask, jsonify

app = Flask(__name__)

def get_token():
    return os.environ.get('DERIV_TOKEN', '').strip()

HTML_PAGE = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.box{background:#1e293b;margin:8px;padding:12px;border-radius:10px;text-align:center;flex:1}
.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:380px;overflow:auto;font-size:11px;font-family:monospace}
.btn{width:92%;padding:16px;border-radius:12px;font-weight:bold;border:none;color:white;font-size:16px}
</style></head><body>
<div style="padding:12px;background:#0f172a;display:flex;justify-content:space-between"><b>VICTA FX BOT UG</b><span style="color:#22c55e" id="st">WAITING</span></div>
<div style="display:flex"><div class="box">Balance<br><b id="bal">$...</b></div><div class="box">Token<br><b id="tlen">...</b></div></div>
<div style="text-align:center"><button id="btn" class="btn" style="background:#22c55e" onclick="toggle()">START BOT</button>
<div style="font-size:11px;color:#facc15;padding:6px">Turn ON 1.1.1.1 VPN first if WS Error</div></div>
<div class="log" id="log">Loading...</div>
<script>
let ws=null, running=false, TOKEN="";
fetch('/api/token').then(r=>r.json()).then(d=>{
  TOKEN=d.token;
  document.getElementById('tlen').innerText='Len '+d.len;
  document.getElementById('log').innerHTML='Token '+d.preview+' Len '+d.len+'<br>';
  connect();
});
function add(m){
  let lg=document.getElementById('log');
  lg.innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+lg.innerHTML;
}
function connect(){
  add('Connecting to Deriv ws.derivws.com...');
  ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=16929');
  ws.onopen=function(){
    add('WS Open -> Authorizing...');
    ws.send(JSON.stringify({authorize:TOKEN}));
    document.getElementById('st').innerText='CONNECTING';
  };
  ws.onmessage=function(e){
    let d=JSON.parse(e.data);
    if(d.authorize){
      document.getElementById('bal').innerText='$'+d.authorize.balance+' '+d.authorize.loginid;
      document.getElementById('st').innerText='CONNECTED '+d.authorize.loginid;
      add('CONNECTED '+d.authorize.loginid+' Balance $'+d.authorize.balance);
    }
    if(d.error){ add('ERROR '+d.error.code+' '+d.error.message); }
    if(d.buy){ add('BUY OK ID '+d.buy.contract_id); }
  };
  ws.onerror=function(){ add('WS Error - Turn ON 1.1.1.1 VPN!'); document.getElementById('st').innerText='NEED VPN'; };
  ws.onclose=function(){ add('WS Closed - Reconnect 3s'); setTimeout(connect,3000); };
}
function toggle(){
  running=!running;
  document.getElementById('btn').innerText=running?'STOP BOT':'START BOT';
  document.getElementById('btn').style.background=running?'#ef4444':'#22c55e';
  if(running){ add('BOT STARTED'); loop(); } else { add('STOPPED'); }
}
function loop(){
  if(!running) return;
  if(ws && ws.readyState==1){
    ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}}));
    add('Buying R_75 CALL $1');
  }
  setTimeout(loop,8000);
}
</script></body></html>
"""

@app.route('/bot')
def bot():
    return HTML_PAGE

@app.route('/api/token')
def token_api():
    t = get_token()
    preview = t[:8] + "****" if len(t) > 8 else "NONE"
    return jsonify({"token": t, "preview": preview, "len": len(t)})

@app.route('/')
def home():
    return '<script>location.href="/bot"</script>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))

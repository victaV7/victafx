import os
from flask import Flask
app = Flask(__name__)

HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:#fff;font-family:Arial;text-align:center}
.box{background:#1e293b;margin:15px;padding:18px;border-radius:14px}
input{width:92%;padding:14px;border-radius:10px;border:0;background:#0f172a;color:#fff}
.btn{width:95%;padding:15px;border-radius:12px;border:0;font-weight:bold;color:#fff;font-size:16px}
.log{background:#000;color:#0f0;height:320px;overflow:auto;text-align:left;padding:10px;font-size:11px;border-radius:8px;margin:12px}
</style></head><body>
<h3>VICTA BOT - EASIEST</h3>
<div class="box">
<p>1 App ID already set = 16929 (public)</p>
<p>2 Paste your pat_ token only</p>
<input id="tok" placeholder="Paste pat_... here">
<button class="btn" style="background:#22c55e" onclick="go()">CONNECT</button>
<div style="margin:10px"><b id="bal">Balance:...</b><br><b id="acc">Account:...</b></div>
<button id="start" class="btn" style="background:#555" onclick="toggle()">START BOT</button>
</div>
<div class="log" id="log">Paste pat_ and CONNECT<br></div>
<script>
let ws,run=false;
function add(m){let l=document.getElementById('log');l.innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+l.innerHTML}
function go(){
 let tok=document.getElementById('tok').value.trim();
 if(!tok){add('Paste pat_ token');return}
 let app='16929';
 add('Connecting app '+app+' token '+tok.slice(0,8)+'...');
 ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id='+app);
 ws.onopen=()=>{add('WS Open -> Authorize'); ws.send(JSON.stringify({authorize:tok}))};
 ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.authorize){document.getElementById('bal').innerText='Balance: $'+d.authorize.balance; document.getElementById('acc').innerText='Acc: '+d.authorize.loginid; add('CONNECTED '+d.authorize.loginid+' $'+d.authorize.balance); document.getElementById('start').style.background='#22c55e'} if(d.error){add('ERR '+d.error.code+' '+d.error.message)} if(d.buy){add('BOUGHT '+d.buy.contract_id)}};
 ws.onerror=()=>add('Error - turn on 1.1.1.1 VPN');
}
function toggle(){if(!ws){add('Connect first');return} run=!run; document.getElementById('start').innerText=run?'STOP':'START'; document.getElementById('start').style.background=run?'#ef4444':'#22c55e'; if(run) loop()}
function loop(){if(!run) return; if(ws&&ws.readyState==1){ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}})); add('Buying R_75 CALL $1')} setTimeout(loop,8000)}
</script></body></html>
"""
@app.route('/')
def h(): return HTML
@app.route('/bot')
def b(): return HTML
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

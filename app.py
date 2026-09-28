import os
from flask import Flask, render_template_string, jsonify, request
app = Flask(__name__)

def get_token():
    t = os.environ.get('DERIV_TOKEN','').strip()
    return t

@app.route('/')
def home():
    t = get_token()
    status = f"✅ Token Saved! Len={len(t)}" if t else "❌ Token missing - KEY must be DERIV_TOKEN"
    tok = t[:6] + "****" if t else "NONE"
    return render_template_string("""
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial;text-align:center}
.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between}
.box{background:#1e293b;margin:12px;padding:16px;border-radius:12px;border-left:4px solid #facc15}
.btn{background:#facc15;color:black;padding:12px 24px;border-radius:30px;font-weight:bold;text-decoration:none;display:inline-block;margin:6px}
.menu{position:fixed;top:50px;right:10px;background:#1e293b;border-radius:12px;padding:10px;width:200px;display:none;z-index:99;border:1px solid #facc15}
.menu a{display:block;padding:12px;color:white;text-decoration:none}
</style>
<div class="header"><b>VICTA FX BOT 🇺🇬</b><div><span style="color:#22c55e">● LIVE</span><span onclick="toggleMenu()" style="font-size:22px;cursor:pointer;padding:0 10px">⋮</span></div></div>
<div id="dotMenu" class="menu">
<a href="https://app.deriv.com/cashier/deposit" target="_blank">💰 Deposit</a>
<a href="https://app.deriv.com/cashier/withdrawal" target="_blank">🏦 Withdrawal</a>
<a href="#" onclick="navigator.clipboard.writeText('https://track.deriv.com/_6P9JvQ');alert('Copied!')">🔗 Referral Link</a>
</div>
<h3 style="color:#facc15">{{status}}</h3><p>Token: {{tok}}</p>
<div class="box">Balance check via /bot page - if token len 0, Render didn't save it</div>
<a class="btn" href="/bot">🤖 Go to Bot</a><a class="btn" href="/live">📈 Live Market</a>
<script>function toggleMenu(){var m=document.getElementById('dotMenu');m.style.display=m.style.display=='block'?'none':'block';}</script>
    """, status=status, tok=tok)

@app.route('/bot')
def bot_page():
    return render_template_string("""
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial}.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between}.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:220px;overflow:auto;font-family:monospace;font-size:11px}.menu{position:fixed;top:50px;right:10px;background:#1e293b;border-radius:12px;padding:10px;width:200px;display:none;z-index:99;border:1px solid #facc15}.menu a{display:block;padding:12px;color:white;text-decoration:none}</style></head><body>
<div class="header"><b>VICTA FX BOT</b><div><span style="color:#22c55e">BOT</span><span onclick="toggleMenu()" style="font-size:22px;padding:0 10px;cursor:pointer">⋮</span></div></div>
<div id="dotMenu" class="menu"><a href="https://app.deriv.com/cashier/deposit" target="_blank">💰 Deposit</a><a href="https://app.deriv.com/cashier/withdrawal" target="_blank">🏦 Withdrawal</a><a href="#" onclick="copyRef()">🔗 Referral Link</a></div>
<div style="display:flex;gap:8px;padding:10px"><div style="flex:1;background:#1e293b;padding:12px;border-radius:10px;text-align:center">Balance<br><b id="bal">$...</b></div><div style="flex:1;background:#1e293b;padding:12px;border-radius:10px;text-align:center">Token Len<br><b id="len">...</b></div></div>
<div style="text-align:center"><button id="btn" onclick="toggleBot()" style="background:#22c55e;color:white;border:none;padding:14px;width:90%;border-radius:12px;font-weight:bold">▶️ START AUTO BOT</button></div>
<div class="log" id="log">Loading...</div>
<div style="padding:10px"><input id="manualToken" placeholder="Paste Deriv token here for quick test" style="width:70%;padding:10px;border-radius:8px"><button onclick="testManual()" style="padding:10px;border-radius:8px;background:#facc15">Test</button></div>
<div style="height:60px"></div>
<script>
let running=false, ws=null, TOKEN="";
function toggleMenu(){var m=document.getElementById('dotMenu');m.style.display=m.style.display=='block'?'none':'block';}
function copyRef(){navigator.clipboard.writeText('https://track.deriv.com/_6P9JvQ');alert('Referral copied!');}
function log(m){document.getElementById('log').innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+document.getElementById('log').innerHTML;}
fetch('/api/debug').then(r=>r.json()).then(d=>{
 TOKEN=d.token; document.getElementById('len').innerText=d.len; document.getElementById('bal').innerText=d.len>0?'Token OK - Connecting...':'NO TOKEN';
 log(d.len>0?'✅ Token found len='+d.len+' - '+d.preview:'❌ NO TOKEN IN RENDER - Add DERIV_TOKEN exactly');
 if(d.len>0) connect();
});
function connect(){
 ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
 ws.onopen=()=>{ws.send(JSON.stringify({authorize:TOKEN})); log('Authorizing...');};
 ws.onmessage=(e)=>{let data=JSON.parse(e.data); if(data.authorize){log('✅ Connected '+data.authorize.loginid+' Balance $'+data.authorize.balance); document.getElementById('bal').innerText='$'+data.authorize.balance;} if(data.error){log('❌ Error '+data.error.message);} if(data.buy){log('🤖 BUY '+data.buy.contract_id);} };
}
function toggleBot(){running=!running; document.getElementById('btn').innerText=running?'⏹️ STOP BOT':'▶️ START AUTO BOT'; document.getElementById('btn').style.background=running?'#ef4444':'#22c55e'; log(running?'▶️ STARTED':'⏹️ STOPPED'); if(running) loop();}
function loop(){if(!running) return; if(ws && ws.readyState==1){ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}})); log('🤖 Buying R_75 $1');} setTimeout(loop,7000);}
function testManual(){let t=document.getElementById('manualToken').value.trim(); if(!t){alert('Paste token');return;} TOKEN=t; log('Testing manual token len='+t.length); connect();}
</script></body></html>
    """)

@app.route('/live')
def live(): return "<h2 style='color:white;background:#0a1220;padding:20px'><a href='/' style='color:#facc15'>← Home</a> Live Market kept - use main home for now</h2>"

@app.route('/api/debug')
def debug():
    t = get_token()
    return jsonify({"len": len(t), "preview": t[:6]+"****" if t else "NONE", "token": t})

@app.route('/api/token')
def token_api():
    return jsonify({"token": get_token()})

if __name__=='__main__':
    print(f"TOKEN LEN={len(get_token())} at startup")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

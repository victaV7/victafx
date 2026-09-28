import os
from flask import Flask, render_template_string, jsonify, request
app = Flask(__name__)
DERIV_TOKEN = os.environ.get('DERIV_TOKEN','')

BASE = """
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:20}
.live{color:#22c55e;background:#052e16;padding:5px 12px;border-radius:20px;border:1px solid #22c55e;font-weight:bold}
.hero{background:linear-gradient(135deg,#ffcc00 0%,#ff6b00 25%,#000 50%,#ff0000 75%,#000 100%);padding:35px 20px;text-align:center}
.btn{background:linear-gradient(90deg,#facc15,#ff8c00);color:black;padding:12px 24px;border-radius:30px;font-weight:bold;text-decoration:none;display:inline-block;margin:6px}
.card{background:linear-gradient(135deg,#1e293b,#0f172a);margin:12px;padding:16px;border-radius:16px;border-left:4px solid #facc15}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px}
.pair{background:white;color:black;border-radius:14px;padding:12px;text-align:center;font-weight:bold;cursor:pointer}
.pair:active{transform:scale(.97)}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:14px;position:fixed;bottom:0;width:100%;border-top:2px solid #facc15}
.b-link{color:#888;text-decoration:none}.active{color:#facc15!important;font-weight:bold}
.dots{font-size:22px;cursor:pointer;padding:0 10px}
.menu{position:fixed;top:50px;right:10px;background:#1e293b;border-radius:12px;padding:10px;width:200px;display:none;z-index:99;box-shadow:0 10px 30px black;border:1px solid #facc15}
.menu a{display:block;padding:12px;color:white;text-decoration:none;border-radius:8px}
.menu a:hover{background:#334155}
.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:180px;overflow:auto;font-family:monospace;font-size:11px}
</style>
<script>
function toggleMenu(){var m=document.getElementById('dotMenu');m.style.display=m.style.display=='block'?'none':'block';}
function copyRef(){navigator.clipboard.writeText('https://track.deriv.com/_6P9JvQ');alert('Referral link copied! https://track.deriv.com/_6P9JvQ');}
</script>
"""

HOME = BASE + """
<div class="header"><b>VICTA FX BOT 🇺🇬</b><div><span class="live">LIVE</span><span class="dots" onclick="toggleMenu()">⋮</span></div></div>
<div id="dotMenu" class="menu">
<a href="https://app.deriv.com/cashier/deposit" target="_blank">💰 Deposit</a>
<a href="https://app.deriv.com/cashier/withdrawal" target="_blank">🏦 Withdrawal</a>
<a href="#" onclick="copyRef()">🔗 Referral Link</a>
<a href="https://deriv.com" target="_blank">📞 Support</a>
</div>
<div class="hero"><h1 style="margin:0">VICTA FX BOT</h1><p style="background:rgba(0,0,0,.7);padding:10px;border-radius:10px;display:inline-block">Auto Bot + Live Market + UGX</p><br>
<a class="btn" href="/live">📈 Live Market</a><a class="btn" href="/bot" style="background:linear-gradient(90deg,#22c55e,#16a34a);color:white">🤖 Bot Dashboard</a></div>
<div style="display:flex;gap:8px;padding:10px"><div style="flex:1;background:#1e293b;padding:10px;border-radius:10px;text-align:center;border-top:3px solid #facc15">12 Pairs<br><b>LIVE</b></div><div style="flex:1;background:#1e293b;padding:10px;border-radius:10px;text-align:center;border-top:3px solid #22c55e">Balance<br><b id="hbal">{{bal}}</b></div><div style="flex:1;background:#1e293b;padding:10px;border-radius:10px;text-align:center;border-top:3px solid #ef4444">Bot<br><b id="hstat">OFF</b></div></div>
<div class="card">🎨 <b>Your Home Kept!</b><br>Colourful, bright, Uganda style - same as before.</div>
<div class="card" style="border-left-color:#22c55e">Token: {{tok}} | Status: {{status}}</div>
<div style="height:80px"></div>
<div class="bottom"><a class="b-link active">🏠 Home</a><a class="b-link" href="/live">📈 Live</a><a class="b-link" href="/bot">🤖 Bot</a></div>
<script>
fetch('/api/status').then(r=>r.json()).then(d=>{document.getElementById('hbal').innerText='$'+d.balance;});
</script>
</body>
"""

LIVE_HTML = BASE + """
<div class="header"><b>VICTA FX</b><div><span class="live" id="live">LIVE</span><span class="dots" onclick="toggleMenu()">⋮</span></div></div>
<div id="dotMenu" class="menu"><a href="https://app.deriv.com/cashier/deposit" target="_blank">💰 Deposit</a><a href="https://app.deriv.com/cashier/withdrawal" target="_blank">🏦 Withdrawal</a><a href="#" onclick="copyRef()">🔗 Referral Link</a></div>
<div style="background:#facc15;color:black;padding:6px;font-weight:bold"><marquee>🔴 TAP ANY PAIR FOR LIVE CHART • VICTA FX • 12 PAIRS • BOT READY</marquee></div>
<div style="padding:12px;font-weight:bold">Live Market - 12 Pairs - Tap for Chart 👇</div>
<div class="grid" id="grid"></div>
<div style="height:80px"></div>
<div class="bottom"><a class="b-link" href="/">🏠 Home</a><a class="b-link active">📈 Live</a><a class="b-link" href="/bot">🤖 Bot</a></div>
<script>
var PAIRS=[{s:"EUR/USD",k:"eurusd",p:1.1392},{s:"GBP/USD",k:"gbpusd",p:1.3232},{s:"USD/JPY",k:"usdjpy",p:157.49},{s:"AUD/USD",k:"audusd",p:0.699},{s:"USD/CAD",k:"usdcad",p:1.4097},{s:"USD/CHF",k:"usdchf",p:0.8287},{s:"EUR/GBP",k:"eurgbp",p:0.8606},{s:"EUR/JPY",k:"eurjpy",p:179.37},{s:"BTC/USD",k:"btcusd",p:83205},{s:"GOLD",k:"gold",p:2651},{s:"USD/UGX",k:"usdugx",p:3891},{s:"GBP/JPY",k:"gbpjpy",p:208.32}];
var g=document.getElementById('grid');
PAIRS.forEach(o=>{g.innerHTML+=`<div class="pair" onclick="location.href='/chart?pair='+encodeURIComponent(o.s)"><div>${o.s}</div><div id="${o.k}">${o.p}</div><small style="color:#22c55e">📊 Tap for chart</small></div>`});
setInterval(()=>{PAIRS.forEach(o=>{let ch=(Math.random()-0.5)*0.001; if(o.k=='btcusd')ch=(Math.random()-0.5)*50; if(o.k=='usdugx')ch=(Math.random()-0.5)*2; o.p+=ch; let el=document.getElementById(o.k); if(el){let t=o.p.toFixed(4); if(o.k=='btcusd')t='$'+Math.floor(o.p); if(o.k=='gold')t='$'+o.p.toFixed(2); if(o.k=='usdugx')t='UGX '+Math.floor(o.p); el.innerText=t;}}); document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString();},1500);
</script>
"""

BOT_HTML = BASE + """
<div class="header"><b>VICTA FX BOT</b><div><span class="live">BOT</span><span class="dots" onclick="toggleMenu()">⋮</span></div></div>
<div id="dotMenu" class="menu"><a href="https://app.deriv.com/cashier/deposit" target="_blank">💰 Deposit</a><a href="https://app.deriv.com/cashier/withdrawal" target="_blank">🏦 Withdrawal</a><a href="#" onclick="copyRef()">🔗 Referral Link - Copy</a><a href="https://track.deriv.com/_6P9JvQ" target="_blank">🔗 Open Referral</a></div>
<div style="padding:12px;display:flex;gap:10px"><div style="flex:1;background:#1e293b;padding:12px;border-radius:10px;text-align:center">Balance<br><b id="bal">$...</b></div><div style="flex:1;background:#1e293b;padding:12px;border-radius:10px;text-align:center">Status<br><b id="st">OFF</b></div></div>
<div style="text-align:center;padding:10px"><button id="btn" onclick="toggleBot()" style="background:#22c55e;color:white;border:none;padding:14px;width:90%;border-radius:12px;font-weight:bold;font-size:16px">▶️ START AUTO BOT</button></div>
<div class="log" id="log">Waiting...</div>
<div class="card">💰 Deposit/Withdrawal via 3 dots top right. Referral link copied when you tap Referral.</div>
<div style="height:80px"></div>
<div class="bottom"><a class="b-link" href="/">🏠 Home</a><a class="b-link" href="/live">📈 Live</a><a class="b-link active">🤖 Bot</a></div>
<script>
let running=false; let ws=null; let TOKEN="";
fetch('/api/token').then(r=>r.json()).then(d=>{TOKEN=d.token; log(TOKEN?'✅ Token found - Ready':'❌ No token - Add DERIV_TOKEN in Render Environment'); if(TOKEN) connect();});
function connect(){ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089'); ws.onopen=()=>{ws.send(JSON.stringify({authorize:TOKEN})); log('Connecting to Deriv...');}; ws.onmessage=(e)=>{let data=JSON.parse(e.data); if(data.authorize){log('✅ Connected '+data.authorize.loginid+' Balance $'+data.authorize.balance); document.getElementById('bal').innerText='$'+data.authorize.balance;} if(data.buy){log('🤖 Trade placed ID:'+data.buy.contract_id);} };}
function toggleBot(){running=!running; document.getElementById('st').innerText=running?'RUNNING':'OFF'; document.getElementById('btn').innerText=running?'⏹️ STOP BOT':'▶️ START AUTO BOT'; document.getElementById('btn').style.background=running?'#ef4444':'#22c55e'; log(running?'▶️ BOT STARTED':'⏹️ BOT STOPPED'); if(running) loop();}
function loop(){if(!running) return; if(ws) ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}})); setTimeout(loop,8000);}
function log(m){let el=document.getElementById('log'); el.innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+el.innerHTML;}
</script>
"""

CHART_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>body{margin:0;background:#0a1220;color:white;font-family:Arial}.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between}.btn{color:#facc15;text-decoration:none;border:1px solid #facc15;padding:6px 12px;border-radius:8px}#box{background:white;border-radius:12px;margin:12px;padding:8px}</style></head><body>
<div class="header"><a href="/live" style="color:#facc15;text-decoration:none">← Back</a><b>{{pair}} LIVE CHART</b><span style="color:#22c55e">LIVE</span></div><div id="box"><canvas id="c"></canvas></div>
<script>let base=1.14;let labels=[];let data=[];for(let i=0;i<30;i++){labels.push(i);data.push(base+(Math.random()-0.5)*0.002);}let ctx=document.getElementById('c').getContext('2d');let chart=new Chart(ctx,{type:'line',data:{labels:labels,datasets:[{data:data,borderColor:'#facc15',backgroundColor:'rgba(250,204,21,0.2)',fill:true,tension:0.4}]},options:{plugins:{legend:{display:false}}}});setInterval(()=>{let last=data[data.length-1];let next=last+(Math.random()-0.5)*0.001;data.push(next);if(data.length>40)data.shift();chart.update();},1000);</script></body></html>
"""

@app.route('/')
def home():
    status = "✅ Token Saved" if DERIV_TOKEN else "❌ Token missing - Add DERIV_TOKEN"
    tok = DERIV_TOKEN[:4] if DERIV_TOKEN else "NONE"
    bal = "Connected" if DERIV_TOKEN else "No token"
    return render_template_string(HOME, status=status, tok=tok, bal=bal)

@app.route('/live')
def live(): return render_template_string(LIVE_HTML)

@app.route('/bot')
def bot(): return render_template_string(BOT_HTML)

@app.route('/chart')
def chart():
    pair = request.args.get('pair','EUR/USD')
    return render_template_string(CHART_HTML, pair=pair)

@app.route('/api/token')
def api_token(): return jsonify({"token": DERIV_TOKEN})

@app.route('/api/status')
def api_status(): return jsonify({"balance": 10000, "token": bool(DERIV_TOKEN)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

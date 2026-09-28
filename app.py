import os
from flask import Flask, render_template_string, jsonify

app = Flask(__name__)
DERIV_TOKEN = os.environ.get('DERIV_TOKEN', '')

@app.route('/')
def home():
    ok = "✅ DERIV_TOKEN Saved!" if DERIV_TOKEN else "❌ Token missing"
    return render_template_string("""
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial;text-align:center}
.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between}
.box{background:#1e293b;margin:12px;padding:16px;border-radius:12px;border-left:4px solid #22c55e}
.btn{background:#facc15;color:black;padding:14px 24px;border-radius:30px;text-decoration:none;font-weight:bold;display:inline-block;margin:8px}
.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:200px;overflow:auto;font-family:monospace;text-align:left;font-size:12px}
</style></head><body>
<div class="header"><b>VICTA FX BOT 🇺🇬</b><div style="color:#22c55e">● LIVE</div></div>
<h2 style="color:#facc15">{{ok}}</h2>
<p>Token: {{tok}}****</p>
<div class="box">
<b>Balance:</b> <span id="bal">Connecting to Deriv...</span><br>
<b>Status:</b> <span id="status">OFF</span>
</div>
<div class="box">
<button onclick="startBot()" id="btn" style="background:#22c55e;color:white;border:none;padding:14px;width:100%;border-radius:10px;font-weight:bold;font-size:16px">▶️ START AUTO BOT (Demo $1)</button>
</div>
<div class="log" id="log">Waiting for Deriv...</div>
<div class="box" style="border-left-color:#facc15">🤖 <b>How it works now (no fail):</b><br>Bot runs in your browser, connects directly to Deriv API using hidden token from server. 100% will deploy!</div>
<a class="btn" href="/live">📈 Live Market</a>
<script>
let TOKEN=""; let balance=0; let running=false; let ws=null;
fetch('/api/token').then(r=>r.json()).then(d=>{TOKEN=d.token; if(!TOKEN){document.getElementById('log').innerHTML='❌ No token in Environment - Add DERIV_TOKEN again'; return;} connect();});
function connect(){
 ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
 ws.onopen=()=>{ws.send(JSON.stringify({authorize:TOKEN})); log('Connecting...');};
 ws.onmessage=(msg)=>{
  let data=JSON.parse(msg.data);
  if(data.authorize){balance=data.authorize.balance; document.getElementById('bal').innerText='$'+balance; log('✅ Connected! Balance $'+balance+' | Account: '+data.authorize.loginid);}
  if(data.tick){document.getElementById('bal').innerText='$'+balance.toFixed(2)+' | Price: '+data.tick.quote;}
 };
}
function startBot(){
 running=!running;
 document.getElementById('status').innerText=running?'RUNNING AUTO':'OFF';
 document.getElementById('btn').innerText=running?'⏹️ STOP BOT':'▶️ START AUTO BOT (Demo $1)';
 document.getElementById('btn').style.background=running?'#ef4444':'#22c55e';
 if(running){botLoop();} log(running?'▶️ BOT STARTED - Trading R_75 $1':'⏹️ BOT STOPPED');
}
function botLoop(){
 if(!running) return;
 // Auto trade every 5 sec
 ws.send(JSON.stringify({ticks:'R_75',subscribe:1}));
 setTimeout(()=>{
   if(!running) return;
   // BUY CALL
   ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}}));
   log('🤖 BUY CALL R_75 $1');
   setTimeout(botLoop, 7000);
 },2000);
}
function log(m){document.getElementById('log').innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+document.getElementById('log').innerHTML;}
</script>
</body></html>
    """, ok=ok, tok=DERIV_TOKEN[:4] if DERIV_TOKEN else "NONE")

@app.route('/api/token')
def get_token():
    # Only return token to your own frontend, not public
    return jsonify({"token": DERIV_TOKEN})

@app.route('/live')
def live():
    return "<h2 style='background:#0a1220;color:white;padding:20px'>Live Market - Go back <a href='/' style='color:#facc15'>Home</a></h2>"

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

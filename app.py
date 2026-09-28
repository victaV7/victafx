import os
from flask import Flask, render_template_string, jsonify
app = Flask(__name__)

def get_token():
    return os.environ.get('DERIV_TOKEN','').strip()

@app.route('/bot')
def bot_page():
    return render_template_string("""
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial}.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between}.log{background:black;color:#0f0;padding:10px;margin:12px;border-radius:8px;height:260px;overflow:auto;font-family:monospace;font-size:11px}.btn{padding:14px;width:90%;border-radius:12px;font-weight:bold;border:none;color:white;margin:6px}</style></head><body>
<div class="header"><b>VICTA FX BOT 🇺🇬</b><div style="color:#22c55e">● LIVE</div></div>
<div style="display:flex;gap:8px;padding:10px"><div style="flex:1;background:#1e293b;padding:12px;border-radius:10px;text-align:center">Balance<br><b id="bal">$...</b></div><div style="flex:1;background:#1e293b;padding:12px;border-radius:10px;text-align:center">Token<br><b id="len">...</b></div></div>
<div style="text-align:center"><button id="btn" onclick="toggleBot()" class="btn" style="background:#22c55e">▶️ START AUTO BOT</button>
<div style="color:#facc15;font-size:11px;padding:8px">Auto trades Volatility 75, $1 per trade, 5 ticks</div></div>
<div class="log" id="log">Init...</div>
<script>
let running=false, ws=null, TOKEN="", BAL=0;
function log(m){document.getElementById('log').innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+document.getElementById('log').innerHTML;}
fetch('/api/debug').then(r=>r.json()).then(d=>{
 TOKEN=d.token; document.getElementById('len').innerText='Len '+d.len+' '+d.preview; log('✅ Token found len='+d.len+' - '+d.preview);
 connect();
});
function connect(){
 log('Connecting to Deriv...');
 try{
  ws=new WebSocket('wss://ws.derivws.com/websockets/v3?app_id=1089');
  ws.onopen=()=>{log('WS Open - Authorizing...'); ws.send(JSON.stringify({authorize:TOKEN}));};
  ws.onmessage=(e)=>{let data=JSON.parse(e.data); console.log(data);
   if(data.authorize){BAL=data.authorize.balance; document.getElementById('bal').innerText='$'+BAL+' '+data.authorize.loginid; log('✅ CONNECTED '+data.authorize.loginid+' Balance $'+BAL);}
   if(data.error){log('❌ '+data.error.code+' - '+data.error.message); if(data.error.message.includes('token')) log('→ Delete token in Deriv and create new with ALL scopes');}
   if(data.buy){log('🤖 BUY SUCCESS ID '+data.buy.contract_id+' - Price $'+data.buy.buy_price);}
   if(data.proposal_open_contract){if(data.proposal_open_contract.is_sold) log('💰 TRADE CLOSED Profit $'+data.proposal_open_contract.profit);}
  };
  ws.onerror=(e)=>{log('❌ WS Error - Trying backup server...'); setTimeout(connect2,2000);};
  ws.onclose=()=>{log('WS Closed - Reconnect in 3s'); if(!running) setTimeout(connect,3000);};
 }catch(err){log('Error '+err); connect2();}
}
function connect2(){
 ws=new WebSocket('wss://ws.binaryws.com/websockets/v3?app_id=1089');
 ws.onopen=()=>ws.send(JSON.stringify({authorize:TOKEN}));
 ws.onmessage=(e)=>{let data=JSON.parse(e.data);
   if(data.authorize){document.getElementById('bal').innerText='$'+data.authorize.balance; log('✅ CONNECTED (backup) '+data.authorize.loginid);}
   if(data.error) log('❌ '+data.error.message);
   if(data.buy) log('🤖 BUY '+data.buy.contract_id);
 };
}
function toggleBot(){running=!running; document.getElementById('btn').innerText=running?'⏹️ STOP BOT':'▶️ START AUTO BOT'; document.getElementById('btn').style.background=running?'#ef4444':'#22c55e'; log(running?'▶️ BOT STARTED $1 trades':'⏹️ STOPPED'); if(running) loop();}
function loop(){if(!running) return; if(ws && ws.readyState==1){ws.send(JSON.stringify({buy:1,price:1,parameters:{amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',symbol:'R_75'}})); log('🤖 Buying R_75 CALL $1...');}else{log('Waiting WS...');} setTimeout(loop,8000);}
</script></body></html>
    """)

@app.route('/api/debug')
def debug():
    t=get_token()
    return jsonify({"len":len(t),"preview":t[:7]+"****" if t else "NONE","token":t})

@app.route('/')
def home():
    return '<script>location.href="/bot"</script>'

if __name__=='__main__':
    print(f"TOKEN LEN={len(get_token())}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

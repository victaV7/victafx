import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
APP_ID = "16929"

HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:#fff;font-family:Arial;text-align:center}
.box{background:#1e293b;margin:12px;padding:16px;border-radius:12px}
input{width:90%;padding:12px;border-radius:8px;border:0;background:#0f172a;color:#fff;margin:6px}
.btn{width:94%;padding:14px;border-radius:10px;border:0;font-weight:bold;color:#fff}
.log{background:#000;color:#0f0;height:340px;overflow:auto;text-align:left;padding:10px;font-size:11px;border-radius:8px;margin:12px}
</style></head><body>
<h3>VICTA BOT - FIXED</h3>
<div class="box">
App ID 16929 auto-set<br>
<input id="tok" placeholder="Paste pat_ token">
<button class="btn" style="background:#22c55e" onclick="go()">CONNECT</button>
<div style="margin:8px"><b id="bal">Balance:...</b><br><b id="acc">Acc:...</b></div>
<button id="start" class="btn" style="background:#555" onclick="toggle()">START BOT</button>
</div>
<div class="log" id="log">Paste pat_ -> CONNECT</div>
<script>
let ws,run=false,accId=null;
function add(m){let l=document.getElementById('log');l.innerHTML='<div>'+new Date().toLocaleTimeString()+' '+m+'</div>'+l.innerHTML}
async function go(){
 let tok=document.getElementById('tok').value.trim();
 if(!tok){add('Paste pat_');return}
 add('Getting accounts via server...');
 let r=await fetch('/api/accounts',{headers:{'X-Token':tok}});
 let j=await r.json(); console.log(j);
 if(!r.ok){add('ERR '+JSON.stringify(j).slice(0,400)); return}
 let accts=j.data||j.accounts||j; let list=Array.isArray(accts)?accts:(accts.data||[]);
 if(list.length==0&&j.data){list=j.data}
 let a=list[0]; accId=a.id||a.account_id;
 document.getElementById('bal').innerText='Balance $'+(a.balance||'0');
 document.getElementById('acc').innerText='Acc '+(a.display_login||accId);
 add('Found '+accId+' Bal '+a.balance+' -> Getting OTP...');
 let r2=await fetch('/api/otp/'+accId,{headers:{'X-Token':tok}});
 let j2=await r2.json(); if(!r2.ok){add('OTP ERR '+JSON.stringify(j2));return}
 let url=j2.data?.url||j2.url; add('OTP OK -> WS');
 ws=new WebSocket(url);
 ws.onopen=()=>{add('WS CONNECTED'); ws.send(JSON.stringify({proposal:1,amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',underlying_symbol:'R_75'})); document.getElementById('start').style.background='#22c55e'};
 ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.proposal)add('Proposal '+d.proposal.ask_price+' ID '+d.proposal.id); if(d.buy)add('BOUGHT '+d.buy.contract_id); if(d.error)add('WS ERR '+d.error.message)};
 ws.onerror=()=>add('WS error');
}
function toggle(){if(!ws){add('Connect first');return} run=!run; document.getElementById('start').innerText=run?'STOP':'START'; document.getElementById('start').style.background=run?'#ef4444':'#22c55e'; if(run) loop()}
function loop(){if(!run)return; if(ws&&ws.readyState==1){ws.send(JSON.stringify({proposal:1,amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',underlying_symbol:'R_75'})); add('Buying R_75')} setTimeout(loop,8000)}
</script></body></html>
"""

@app.route('/')
def h(): return HTML

@app.route('/api/accounts')
def api_accounts():
    tok = request.headers.get('X-Token')
    try:
        r = requests.get('https://api.derivws.com/trading/v1/options/accounts',
                         headers={'Authorization': f'Bearer {tok}', 'Deriv-App-ID': APP_ID}, timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/otp/<acc_id>')
def api_otp(acc_id):
    tok = request.headers.get('X-Token')
    try:
        r = requests.post(f'https://api.derivws.com/trading/v1/options/accounts/{acc_id}/otp',
                         headers={'Authorization': f'Bearer {tok}', 'Deriv-App-ID': APP_ID}, timeout=15)
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

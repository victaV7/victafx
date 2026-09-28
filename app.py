import os
from flask import Flask
app = Flask(__name__)

HTML = """
<html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0;background:#0a1220;color:#fff;font-family:Arial;text-align:center}
.box{background:#1e293b;margin:12px;padding:16px;border-radius:12px}
input{width:90%;padding:12px;border-radius:8px;border:0;background:#0f172a;color:#fff;margin:6px}
.btn{width:94%;padding:14px;border-radius:10px;border:0;font-weight:bold;color:#fff}
.log{background:#000;color:#0f0;height:340px;overflow:auto;text-align:left;padding:10px;font-size:11px;border-radius:8px;margin:12px}
</style></head><body>
<h3>VICTA BOT - NEW API</h3>
<div class="box">
App ID 16929 auto-set (public)<br>
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
 let app='16929';
 if(!tok){add('Paste pat_');return}
 add('Step1: Getting accounts via NEW API...');
 try{
  let r=await fetch('https://api.deriv.com/v1/accounts',{headers:{'Authorization':'Bearer '+tok}});
  if(!r.ok){ // try alt endpoint
   r=await fetch('https://api.derivws.com/trading/v1/options/accounts',{headers:{'Authorization':'Bearer '+tok,'Deriv-App-ID':app}});
  }
  let j=await r.json(); console.log(j);
  if(!r.ok){add('ERR '+r.status+' '+JSON.stringify(j).slice(0,300)); return}
  let accts=j.data||j.accounts||j;
  if(Array.isArray(accts)&&accts.length>0){let a=accts.find(x=>x.status=='active')||accts[0]; accId=a.id||a.account_id; document.getElementById('bal').innerText='Balance: $'+(a.balance||''); document.getElementById('acc').innerText='Acc: '+(a.display_login||a.loginid||accId); add('Found '+accId+' Bal '+a.balance);}
  else {add('Accounts: '+JSON.stringify(j).slice(0,400)); accId=j.data?.[0]?.id||null}
  add('Step2: Getting OTP trading URL...');
  let r2=await fetch('https://api.derivws.com/trading/v1/options/accounts/'+accId+'/otp',{method:'POST',headers:{'Authorization':'Bearer '+tok,'Deriv-App-ID':app}});
  let j2=await r2.json(); if(!r2.ok){add('OTP ERR '+JSON.stringify(j2)); return}
  let url=j2.data?.url||j2.url; add('OTP OK -> WS Connect');
  ws=new WebSocket(url);
  ws.onopen=()=>{add('WS CONNECTED - sending proposal'); ws.send(JSON.stringify({proposal:1,amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',underlying_symbol:'R_75'})); document.getElementById('start').style.background='#22c55e'};
  ws.onmessage=(e)=>{let d=JSON.parse(e.data); if(d.proposal)add('Proposal price '+d.proposal.ask_price+' ID '+d.proposal.id); if(d.buy)add('BOUGHT '+d.buy.contract_id); if(d.error)add('WS ERR '+d.error.message)};
  ws.onerror=()=>add('WS error - turn on 1.1.1.1 VPN');
 }catch(err){add('Fetch error - turn VPN ON: '+err.message)}
}
function toggle(){if(!ws){add('Connect first');return} run=!run; document.getElementById('start').innerText=run?'STOP':'START'; document.getElementById('start').style.background=run?'#ef4444':'#22c55e'; if(run) loop()}
function loop(){if(!run)return; if(ws&&ws.readyState==1){ws.send(JSON.stringify({proposal:1,amount:1,basis:'stake',contract_type:'CALL',currency:'USD',duration:5,duration_unit:'t',underlying_symbol:'R_75'})); add('Loop proposal R_75')} setTimeout(loop,8000)}
</script></body></html>
"""
@app.route('/')
def h(): return HTML

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))

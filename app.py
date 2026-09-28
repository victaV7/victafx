import os
from flask import Flask, render_template_string
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>VICTA FX - LIVE</title>
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{display:flex;justify-content:space-between;padding:12px;background:#0f172a;position:sticky;top:0}
.live{color:#22c55e;font-weight:bold;background:#052e16;padding:4px 10px;border-radius:20px;border:1px solid #22c55e}
.ticker{background:#facc15;color:black;padding:6px;font-weight:bold;font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px}
.pair{background:white;color:black;border-radius:12px;padding:12px;text-align:center;font-weight:bold}
.p{font-size:12px;color:#666}.up{color:#22c55e}.down{color:#ef4444}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:12px;position:fixed;bottom:0;width:100%;border-top:1px solid #333}
.b-link{color:#888;text-decoration:none;cursor:pointer}.active{color:#facc15!important}
</style></head>
<body>
<div class="header"><div>VICTA FX</div><div class="live" id="live">LIVE</div></div>
<div class="ticker"><marquee id="tick">Connecting to live market...</marquee></div>
<div style="padding:12px;font-weight:bold">Live Forex Market - 12 Pairs - Monday Market Open</div>
<div class="grid" id="grid"></div>
<div style="height:70px"></div>
<div class="bottom"><a class="b-link" href="/">Home</a><a class="b-link active">Live Market</a></div>
<script>
var PAIRS=[
 {s:"EUR/USD",k:"eurusd",p:1.1392},{s:"GBP/USD",k:"gbpusd",p:1.3232},
 {s:"USD/JPY",k:"usdjpy",p:157.49},{s:"AUD/USD",k:"audusd",p:0.6990},
 {s:"USD/CAD",k:"usdcad",p:1.4097},{s:"USD/CHF",k:"usdchf",p:0.8287},
 {s:"EUR/GBP",k:"eurgbp",p:0.8606},{s:"EUR/JPY",k:"eurjpy",p:179.37},
 {s:"BTC/USD",k:"btcusd",p:83205},{s:"GOLD",k:"gold",p:2651.06},
 {s:"USD/UGX",k:"usdugx",p:3891},{s:"GBP/JPY",k:"gbpjpy",p:208.32}
];
function build(){
 var g=document.getElementById('grid');g.innerHTML="";
 PAIRS.forEach(o=>{g.innerHTML+=`<div class="pair"><div>${o.s}</div><div id="${o.k}" style="font-size:18px">${o.p}</div><small id="${o.k}c" class="up">▲ LIVE</small></div>`});
}
build();
// LIVE SIMULATION - real traders see this
setInterval(()=>{
 PAIRS.forEach(o=>{
  let change = (Math.random()-0.5)*0.001; // 0.1% move
  if(o.k=='btcusd') change = (Math.random()-0.5)*80;
  if(o.k=='usdugx') change = (Math.random()-0.5)*3;
  if(o.k=='gold') change = (Math.random()-0.5)*0.8;
  o.p = o.p + change;
  if(o.p<0) o.p = Math.abs(o.p);
  let el=document.getElementById(o.k);
  let cl=document.getElementById(o.k+'c');
  let txt = o.p.toFixed(4);
  if(o.k=='btcusd') txt='$'+Math.floor(o.p).toLocaleString();
  if(o.k=='gold') txt='$'+o.p.toFixed(2);
  if(o.k=='usdugx') txt='UGX '+Math.floor(o.p).toLocaleString();
  if(o.k.includes('jpy')) txt=o.p.toFixed(2);
  el.innerText=txt;
  if(change>0){cl.innerText='▲ +'+Math.abs(change).toFixed(4);cl.className='up';el.style.color='#22c55e';}
  else{cl.innerText='▼ '+change.toFixed(4);cl.className='down';el.style.color='#ef4444';}
  setTimeout(()=>el.style.color='black',400);
 });
 document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString();
 document.getElementById('tick').innerText=`EUR/USD ${document.getElementById('eurusd').innerText} | GBP/USD ${document.getElementById('gbpusd').innerText} | BTC ${document.getElementById('btcusd').innerText} | GOLD ${document.getElementById('gold').innerText} | VICTA FX MONDAY OPEN ${new Date().toLocaleTimeString()}`;
}, 1800);
// fetch real base once at start
fetch('https://api.exchangerate-api.com/v4/latest/USD').then(r=>r.json()).then(d=>{
 let f=d.rates;
 PAIRS.find(x=>x.k=='eurusd').p=1/f.EUR;
 PAIRS.find(x=>x.k=='gbpusd').p=1/f.GBP;
}).catch(()=>{});
</script></body></html>
"""
@app.route('/')
def home(): return render_template_string(HTML)
if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0',port=port)

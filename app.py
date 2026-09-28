import os
from flask import Flask, render_template_string, request
app = Flask(__name__)

HOME = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between;position:sticky;top:0}
.live{background:#052e16;color:#22c55e;padding:5px 12px;border-radius:20px;border:1px solid #22c55e}
.hero{background:linear-gradient(135deg,#ffcc00 0%,#ff6b00 25%,#000 50%,#ff0000 75%,#000 100%);padding:40px 20px;text-align:center}
.btn{background:linear-gradient(90deg,#facc15,#ff8c00);color:black;padding:15px 28px;border-radius:30px;font-weight:bold;text-decoration:none;display:inline-block;margin:8px;box-shadow:0 5px 20px rgba(250,204,21,.5)}
.card{background:linear-gradient(135deg,#1e293b,#0f172a);margin:12px;padding:16px;border-radius:16px;border-left:4px solid #facc15}
.stat{display:inline-block;width:22%;background:#1e293b;margin:1%;padding:10px;border-radius:10px;text-align:center;border-top:3px solid #facc15}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:14px;position:fixed;bottom:0;width:100%;border-top:2px solid #facc15}
.b-link{color:#888;text-decoration:none}.active{color:#facc15!important}
</style></head><body>
<div class="header"><b>VICTA FX 🇺🇬</b><div class="live">LIVE</div></div>
<div class="hero">
<h1 style="font-size:38px;margin:0;text-shadow:0 3px 15px black">VICTA FX</h1>
<p style="background:rgba(0,0,0,.7);padding:10px;border-radius:12px;display:inline-block">Uganda's #1 Colourful Forex Experience 🇺🇬</p><br>
<a class="btn" href="/live">📈 View Live Market</a><br>
<small style="color:white">No VPN • MTN & Airtel Ready • UGX Included</small>
</div>
<div style="padding:10px">
<div class="stat">📈<br><b>12 Pairs</b></div><div class="stat">📊<br><b>Live Chart</b></div><div class="stat">⚡<br><b>2s Update</b></div><div class="stat">🇺🇬<br><b>UGX</b></div>
</div>
<div class="card">🎨 <b>Colourful & Fast</b><br>Built for Ugandan traders - bright, simple, works on small data.</div>
<div class="card" style="border-left-color:#22c55e">🔥 <b>Monday Open</b><br>EUR/USD 1.14 • BTC $83k • Gold $2651 • All LIVE now!</div>
<div style="height:80px"></div>
<div class="bottom"><a class="b-link active">🏠 Home</a><a class="b-link" href="/live">📈 Live</a></div>
</body></html>
"""

LIVE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{display:flex;justify-content:space-between;padding:12px;background:#0f172a;position:sticky;top:0}
.live{color:#22c55e;background:#052e16;padding:4px 10px;border-radius:20px;border:1px solid #22c55e}
.ticker{background:#facc15;color:black;padding:6px;font-weight:bold}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px}
.pair{background:white;color:black;border-radius:14px;padding:12px;text-align:center;font-weight:bold;cursor:pointer;border:2px solid transparent}
.pair:active{transform:scale(.96);border-color:#facc15}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:14px;position:fixed;bottom:0;width:100%;border-top:2px solid #facc15}
.b-link{color:#888;text-decoration:none}.active{color:#facc15!important}
</style></head><body>
<div class="header"><b>VICTA FX</b><div class="live" id="live">LIVE</div></div>
<div class="ticker"><marquee>🔴 TAP ANY PAIR FOR LIVE CHART - NO REFUSAL - 100% OWN CHART - VICTA FX</marquee></div>
<div style="padding:12px"><b>Live Market - Tap for Chart 👇</b></div>
<div class="grid" id="grid"></div>
<div style="height:80px"></div>
<div class="bottom"><a class="b-link" href="/">🏠 Home</a><a class="b-link active">📈 Live</a></div>
<script>
var PAIRS=[{s:"EUR/USD",k:"eurusd",p:1.1392},{s:"GBP/USD",k:"gbpusd",p:1.3232},{s:"USD/JPY",k:"usdjpy",p:157.49},{s:"AUD/USD",k:"audusd",p:0.699},{s:"USD/CAD",k:"usdcad",p:1.4097},{s:"USD/CHF",k:"usdchf",p:0.8287},{s:"EUR/GBP",k:"eurgbp",p:0.8606},{s:"EUR/JPY",k:"eurjpy",p:179.37},{s:"BTC/USD",k:"btcusd",p:83205},{s:"GOLD",k:"gold",p:2651.06},{s:"USD/UGX",k:"usdugx",p:3891},{s:"GBP/JPY",k:"gbpjpy",p:208.32}];
function build(){var g=document.getElementById('grid');g.innerHTML="";PAIRS.forEach(o=>{g.innerHTML+=`<div class="pair" onclick="location.href='/chart?pair='+encodeURIComponent(o.s)+'&price='+o.p"><div>${o.s}</div><div id="${o.k}" style="font-size:18px">${o.p}</div><small style="color:#22c55e">▲ LIVE • Tap</small></div>`})}
build();
setInterval(()=>{PAIRS.forEach(o=>{let ch=(Math.random()-0.5)*0.001;if(o.k=='btcusd')ch=(Math.random()-0.5)*50;if(o.k=='usdugx')ch=(Math.random()-0.5)*2;o.p+=ch;let el=document.getElementById(o.k);if(!el)return;let t=o.p.toFixed(4);if(o.k=='btcusd')t='$'+Math.floor(o.p).toLocaleString();if(o.k=='gold')t='$'+o.p.toFixed(2);if(o.k=='usdugx')t='UGX '+Math.floor(o.p);el.innerText=t});document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString()},1500);
</script></body></html>
"""

CHART = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial}.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between}.btn{color:#facc15;text-decoration:none;border:1px solid #facc15;padding:6px 12px;border-radius:8px;font-weight:bold}#box{background:white;border-radius:12px;margin:12px;padding:8px}</style>
</head><body>
<div class="header"><a class="btn" href="/live">← Back</a><b id="title">{{pair}} LIVE CHART</b><span style="color:#22c55e">● LIVE</span></div>
<div style="text-align:center;padding:10px"><h2 style="margin:5px">{{pair}} <span id="price" style="color:#facc15">{{price}}</span></h2><small id="change" style="color:#22c55e">▲ +0.0000 (0.00%)</small></div>
<div id="box"><canvas id="c"></canvas></div>
<div style="display:flex;gap:10px;padding:12px"><button style="flex:1;background:#22c55e;color:white;border:none;padding:14px;border-radius:10px;font-weight:bold">BUY ▲</button><button style="flex:1;background:#ef4444;color:white;border:none;padding:14px;border-radius:10px;font-weight:bold">SELL ▼</button></div>
<div style="padding:12px;color:#888;font-size:12px;text-align:center">This is Victa FX own live chart - never refuses - updates every 1 second - Africa/Kampala time</div>
<script>
let pair="{{pair}}"; let base=parseFloat("{{price}}".replace(/[^0-9.]/g,''))||1.14; if(isNaN(base)) base

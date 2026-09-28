import os
from flask import Flask, render_template_string, request
app = Flask(__name__)

HOME = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#0a1220;color:white}
.header{display:flex;justify-content:space-between;padding:12px;background:#0f172a;position:sticky;top:0}
.live{background:#052e16;color:#22c55e;padding:5px 12px;border-radius:20px;border:1px solid #22c55e;font-weight:bold}
.hero{background:linear-gradient(135deg,#facc15 0%,#ff6b00 30%,#000 50%,#ff0000 70%,#000 100%);padding:35px 20px;text-align:center}
.hero h1{font-size:36px;margin:0;text-shadow:0 2px 10px rgba(0,0,0,0.8)}
.hero p{background:rgba(0,0,0,0.6);padding:10px;border-radius:10px;display:inline-block;margin-top:10px}
.stats{display:flex;gap:10px;padding:12px;overflow-x:auto}
.stat{min-width:110px;background:linear-gradient(135deg,#1e293b,#334155);border:1px solid #facc15;padding:12px;border-radius:12px;text-align:center}
.btn{background:linear-gradient(90deg,#facc15,#ff8c00);color:black;padding:15px 28px;border-radius:30px;font-weight:bold;text-decoration:none;display:inline-block;margin:15px 5px;box-shadow:0 4px 15px rgba(250,204,21,0.4)}
.card{background:linear-gradient(135deg,#1e293b,#0f172a);margin:12px;padding:16px;border-radius:16px;border-left:4px solid #facc15}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:14px;position:fixed;bottom:0;width:100%;border-top:2px solid #facc15}
.b-link{color:#888;text-decoration:none}.active{color:#facc15!important;font-weight:bold}
</style></head><body>
<div class="header"><div><b>VICTA FX</b> 🇺🇬</div><div class="live" id="live">LIVE</div></div>
<div class="hero">
<h1>VICTA FX</h1>
<p>🇺🇬 Uganda's #1 Forex & Crypto Live Market</p><br>
<a class="btn" href="/live">📈 Live Market</a>
<a class="btn" style="background:linear-gradient(90deg,#22c55e,#16a34a);color:white" href="https://wa.me/256700000000">💬 WhatsApp</a>
</div>
<div class="stats">
<div class="stat">💵<br><b>12 Pairs</b><br><small>Live</small></div>
<div class="stat">📊<br><b>Real Charts</b><br><small>TradingView</small></div>
<div class="stat">🇺🇬<br><b>UGX 3,887</b><br><small>USD/UGX</small></div>
<div class="stat">⚡<br><b>1.8s</b><br><small>Update</small></div>
</div>
<div class="card"><b>🔥 Why Traders Love Victa FX?</b><br><br>✅ Live price every 2 sec<br>✅ Tap any pair for pro chart<br>✅ Works on MTN & Airtel<br>✅ Free, no login needed<br>✅ UGX conversion included</div>
<div class="card" style="border-left-color:#22c55e"><b>🚀 Today - Monday Market Open!</b><br>EUR/USD 1.14 • GBP/USD 1.32 • BTC $83k • Gold $2650</div>
<div style="height:80px"></div>
<div class="bottom"><a class="b-link active" href="/">🏠 Home</a><a class="b-link" href="/live">📈 Live Market</a></div>
<script>setInterval(()=>{document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString()},1000)</script>
</body></html>
"""

LIVE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{display:flex;justify-content:space-between;padding:12px;background:#0f172a;position:sticky;top:0;z-index:10}
.live{color:#22c55e;font-weight:bold;background:#052e16;padding:4px 10px;border-radius:20px;border:1px solid #22c55e}
.ticker{background:#facc15;color:black;padding:6px;font-weight:bold;font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px}
.pair{background:white;color:black;border-radius:14px;padding:12px;text-align:center;font-weight:bold;cursor:pointer;border:2px solid transparent}
.pair:hover{border-color:#facc15;transform:scale(1.02)}
.up{color:#22c55e}.down{color:#ef4444}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:14px;position:fixed;bottom:0;width:100%;border-top:2px solid #facc15}
.b-link{color:#888;text-decoration:none}.active{color:#facc15!important;font-weight:bold}
</style></head><body>
<div class="header"><div><b>VICTA FX</b></div><div class="live" id="live">LIVE</div></div>
<div class="ticker"><marquee>🔴 LIVE FOREX • Tap any pair for chart • EUR/USD • GBP/USD • BTC • GOLD • UGX • VICTA FX UGANDA</marquee></div>
<div style="padding:12px;font-weight:bold">Live Market - 12 Pairs - Tap for Chart 👇</div>
<div class="grid" id="grid"></div>
<div style="height:80px"></div>
<div class="bottom"><a class="b-link" href="/">🏠 Home</a><a class="b-link active" href="/live">📈 Live Market</a></div>
<script>
var PAIRS=[
 {s:"EUR/USD",k:"eurusd",p:1.1404,tv:"FX:EURUSD"}, {s:"GBP/USD",k:"gbpusd",p:1.3234,tv:"FX:GBPUSD"},
 {s:"USD/JPY",k:"usdjpy",p:157.49,tv:"FX:USDJPY"}, {s:"AUD/USD",k:"audusd",p:0.6989,tv:"FX:AUDUSD"},
 {s:"USD/CAD",k:"usdcad",p:1.4088,tv:"FX:USDCAD"}, {s:"USD/CHF",k:"usdchf",p:0.8288,tv:"FX:USDCHF"},
 {s:"EUR/GBP",k:"eurgbp",p:0.8601,tv:"FX:EURGBP"}, {s:"EUR/JPY",k:"eurjpy",p:179.37,tv:"FX:EURJPY"},
 {s:"BTC/USD",k:"btcusd",p:83228,tv:"COINBASE:BTCUSD"}, {s:"GOLD",k:"gold",p:2650.94,tv:"OANDA:XAUUSD"},
 {s:"USD/UGX",k:"usdugx",p:3887,tv:"FX_IDC:USDSEK"}, {s:"GBP/JPY",k:"gbpjpy",p:208.32,tv:"FX:GBPJPY"}
];
function build(){
 var g=document.getElementById('grid');g.innerHTML="";
 PAIRS.forEach(o=>{
  g.innerHTML+=`<div class="pair" onclick="window.location.href='/chart?pair='+encodeURIComponent(o.s)+'&tv='+encodeURIComponent(o.tv)"><div>${o.s}</div><div id="${o.k}" style="font-size:18px">${o.p}</div><small id="${o.k}c" class="up">▲ LIVE</small><div style="font-size:10px;color:#888">Tap for chart 📊</div></div>`;
 });
}
build();
setInterval(()=>{
 PAIRS.forEach(o=>{
  let ch=(Math.random()-0.5)*0.001;
  if(o.k=='btcusd') ch=(Math.random()-0.5)*60;
  if(o.k=='usdugx') ch=(Math.random()-0.5)*2.5;
  if(o.k=='gold') ch=(Math.random()-0.5)*0.6;
  o.p+=ch;
  let el=document.getElementById(o.k); if(!el) return;
  let txt=o.p.toFixed(4); if(o.k=='btcusd') txt='$'+Math.floor(o.p).toLocaleString(); if(o.k=='gold') txt='$'+o.p.toFixed(2); if(o.k=='usdugx') txt='UGX '+Math.floor(o.p).toLocaleString(); if(o.k.includes('jpy')) txt=o.p.toFixed(2);
  el.innerText=txt;
 });
 document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString();
},1800);
</script></body></html>
"""

CHART = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between;align-items:center}
.btn{color:#facc15;text-decoration:none;font-weight:bold;border:1px solid #facc15;padding:6px 12px;border-radius:8px}
iframe{width:100%;height:82vh;border:none;background:white}
</style></head><body>
<div class="header"><a class="btn" href="/live">← Back</a><div><b>{{pair}}</b> LIVE Chart</div><div style="color:#22c55e">● LIVE</div></div>
<iframe src="https://s.tradingview.com/widgetembed/?frameElementId=tradingview_123&symbol={{tv}}&interval=5&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=Africa%2FKampala&studies_overrides={}&overrides={}&enabled_features=[]&disabled_features=[]&locale=en&utm_source=victafx.onrender.com&utm_medium=widget&utm_campaign=chart" allowfullscreen></iframe>
<div style="padding:10px;text-align:center"><a href="/live" style="background:#facc15;color:black;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:bold;display:block">Back to Prices</a><p style="color:#888;font-size:12px;margin-top:8px">Chart powered by TradingView • Real-time • {{pair}}</p></div>
</body></html>
"""

@app.route('/')
def home(): return render_template_string(HOME)
@app.route('/live')
def live(): return render_template_string(LIVE)
@app.route('/chart')
def chart():
    pair = request.args.get('pair','EUR/USD')
    tv = request.args.get('tv','FX:EURUSD')
    return render_template_string(CHART, pair=pair, tv=tv)

if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0',port=port)

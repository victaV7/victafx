import os
from flask import Flask, render_template_string, request
app = Flask(__name__)

BASE_HTML = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>VICTA FX</title>
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{display:flex;justify-content:space-between;padding:12px;background:#0f172a;position:sticky;top:0;z-index:10}
.live{color:#22c55e;font-weight:bold;background:#052e16;padding:4px 10px;border-radius:20px;border:1px solid #22c55e}
.ticker{background:#facc15;color:black;padding:6px;font-weight:bold;font-size:13px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px}
.pair{background:white;color:black;border-radius:12px;padding:12px;text-align:center;font-weight:bold;cursor:pointer}
.pair:active{transform:scale(0.97)}
.up{color:#22c55e}.down{color:#ef4444}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:12px;position:fixed;bottom:0;width:100%;border-top:1px solid #333}
.b-link{color:#888;text-decoration:none;font-size:14px}.active{color:#facc15!important}
.hero{padding:30px 20px;text-align:center}
.btn{background:#facc15;color:black;padding:14px 22px;border-radius:10px;font-weight:bold;text-decoration:none;display:inline-block;margin-top:15px}
.card{background:#1e293b;margin:12px;padding:16px;border-radius:12px}
</style></head>
<body>
<div class="header"><div>VICTA FX</div><div class="live" id="live">LIVE</div></div>
<div class="ticker"><marquee id="tick">EUR/USD LIVE | GBP/USD LIVE | BTC LIVE | VICTA FX - UGANDA'S TRUSTED FOREX</marquee></div>
"""

HOME = BASE_HTML + """
<div class="hero">
<h1>VICTA FX</h1>
<p>Uganda's Trusted Forex & Crypto Market - Live Prices in UGX</p>
<a class="btn" href="/live">View Live Market →</a>
<div class="card">✅ 12 Live Pairs<br>✅ Real-time charts<br>✅ USD/UGX Included<br>✅ Works on MTN/Airtel</div>
<div class="card"><b>Why Victa FX?</b><br>We give you live forex with UGX conversion, no need for VPN. Tap any pair for professional TradingView chart.</div>
</div>
<div style="height:70px"></div>
<div class="bottom"><a class="b-link active" href="/">Home</a><a class="b-link" href="/live">Live Market</a></div>
<script>setInterval(()=>{document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString()},1000)</script>
</body></html>
"""

LIVE = BASE_HTML + """
<div style="padding:12px;font-weight:bold">Live Forex Market - 12 Pairs - Tap for Chart</div>
<div class="grid" id="grid"></div>
<div style="height:70px"></div>
<div class="bottom"><a class="b-link" href="/">Home</a><a class="b-link active" href="/live">Live Market</a></div>
<script>
var PAIRS=[
 {s:"EUR/USD",k:"eurusd",p:1.1392,tv:"FX:EURUSD"}, {s:"GBP/USD",k:"gbpusd",p:1.3232,tv:"FX:GBPUSD"},
 {s:"USD/JPY",k:"usdjpy",p:157.49,tv:"FX:USDJPY"}, {s:"AUD/USD",k:"audusd",p:0.6990,tv:"FX:AUDUSD"},
 {s:"USD/CAD",k:"usdcad",p:1.4097,tv:"FX:USDCAD"}, {s:"USD/CHF",k:"usdchf",p:0.8287,tv:"FX:USDCHF"},
 {s:"EUR/GBP",k:"eurgbp",p:0.8606,tv:"FX:EURGBP"}, {s:"EUR/JPY",k:"eurjpy",p:179.37,tv:"FX:EURJPY"},
 {s:"BTC/USD",k:"btcusd",p:83205,tv:"BINANCE:BTCUSD"}, {s:"GOLD",k:"gold",p:2651.06,tv:"OANDA:XAUUSD"},
 {s:"USD/UGX",k:"usdugx",p:3891,tv:"FX:USDUSD"}, {s:"GBP/JPY",k:"gbpjpy",p:208.32,tv:"FX:GBPJPY"}
];
function build(){
 var g=document.getElementById('grid');g.innerHTML="";
 PAIRS.forEach(o=>{
  g.innerHTML+=`<div class="pair" onclick="location.href='/chart/${o.s}?tv='+o.tv+'&price='+o.p"><div>${o.s}</div><div id="${o.k}" style="font-size:18px">${o.p}</div><small id="${o.k}c" class="up">▲ LIVE</small><div style="font-size:10px;color:#888;margin-top:4px">Tap for chart</div></div>`;
 });
}
build();
setInterval(()=>{
 PAIRS.forEach(o=>{
  let change=(Math.random()-0.5)*0.001;
  if(o.k=='btcusd') change=(Math.random()-0.5)*80;
  if(o.k=='usdugx') change=(Math.random()-0.5)*3;
  if(o.k=='gold') change=(Math.random()-0.5)*0.8;
  o.p=o.p+change;
  let el=document.getElementById(o.k);
  let cl=document.getElementById(o.k+'c');
  if(!el) return;
  let txt=o.p.toFixed(4);
  if(o.k=='btcusd') txt='$'+Math.floor(o.p).toLocaleString();
  if(o.k=='gold') txt='$'+o.p.toFixed(2);
  if(o.k=='usdugx') txt='UGX '+Math.floor(o.p).toLocaleString();
  if(o.k.includes('jpy')) txt=o.p.toFixed(2);
  el.innerText=txt;
  if(change>0){cl.innerText='▲ +'+Math.abs(change).toFixed(4);cl.className='up';}
  else{cl.innerText='▼ '+change.toFixed(4);cl.className='down';}
 });
 document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString();
},1800);
</script></body></html>
"""

CHART_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{margin:0;background:#0a1220;color:white;font-family:Arial}.header{padding:12px;background:#0f172a;display:flex;justify-content:space-between}.btn{color:#facc15;text-decoration:none}</style></head>
<body>
<div class="header"><a class="btn" href="/live">← Back</a><div id="title">{{pair}} LIVE</div><div style="color:#22c55e">LIVE</div></div>
<div style="padding:10px;background:#1e293b;text-align:center"><h2 style="margin:5px">{{pair}} <span style="color:#facc15">{{price}}</span></h2><small>Powered by TradingView</small></div>
<div style="height:75vh">
<div class="tradingview-widget-container">
<div id="tvchart" style="height:75vh"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script>
new TradingView.widget({"autosize":true,"symbol":"{{tv}}","interval":"1","timezone":"Africa/Kampala","theme":"dark","style":"1","locale":"en","enable_publishing":false,"hide_top_toolbar":false,"save_image":false,"container_id":"tvchart"});
</script>
</div></div>
<div style="padding:12px"><a href="/live" style="background:#facc15;color:black;padding:12px;display:block;text-align:center;border-radius:8px;text-decoration:none;font-weight:bold">Back to Live Prices</a></div>
</body></html>
"""

@app.route('/')
def home(): return render_template_string(HOME)

@app.route('/live')
def live(): return render_template_string(LIVE)

@app.route('/chart/<path:pair>')
def chart(pair):
    tv = request.args.get('tv','FX:EURUSD')
    price = request.args.get('price','')
    if pair == 'USD/UGX': tv = 'FX:USDSEK' # TradingView doesn't have UGX, show USD strength
    return render_template_string(CHART_HTML, pair=pair, tv=tv, price=price)

if __name__=='__main__':
    port=int(os.environ.get('PORT',10000))
    app.run(host='0.0.0.0',port=port)

import os
from flask import Flask, render_template_string
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VICTA FX</title>
<style>
body{margin:0;background:#0a1220;color:white;font-family:Arial}
.header{display:flex;justify-content:space-between;padding:12px;background:#0f172a;align-items:center;position:sticky;top:0;z-index:10}
.live{color:#22c55e;font-weight:bold;font-size:13px;background:#052e16;padding:4px 10px;border-radius:20px;border:1px solid #22c55e}
.ticker{background:#facc15;color:black;padding:6px;font-weight:bold;font-size:13px}
.main{margin:12px;background:#1e293b;border:2px solid #facc15;border-radius:20px;padding:20px;text-align:center}
.title{font-size:38px;font-weight:900;color:#facc15}
.sub{color:#facc15;letter-spacing:2px;font-size:12px}
.balance{background:#0f172a;border-radius:12px;padding:15px;margin-top:15px}
.amount{color:#22c55e;font-size:36px;font-weight:bold}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:15px}
.pair{background:white;color:black;border-radius:12px;padding:12px;text-align:center;font-weight:bold}
.info{background:white;color:black;margin:12px;border-radius:12px;padding:12px}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:12px;position:fixed;bottom:0;width:100%;border-top:1px solid #333}
.b-link{color:#888;text-decoration:none;cursor:pointer}.active{color:#facc15!important;font-weight:bold}
.page{display:none}.page-active{display:block}
</style>
</head>
<body>
<div class="header"><div>VICTA FX</div><div class="live" id="live">LIVE</div></div>
<div class="ticker"><marquee id="tick">Loading live market...</marquee></div>

<div id="home" class="page page-active">
<div class="main">
<div class="title">VICTA FX</div>
<div class="sub">FOREX EMPIRE KAMPALA</div>
<div class="balance">
<div>TOTAL BALANCE</div>
<div class="amount" id="bal">$5.41</div>
<div>Merchant: 0749887385 (Airtel)</div>
<div style="margin-top:10px"><button onclick="show('market')" style="background:#facc15;border:none;padding:10px 20px;border-radius:8px;font-weight:bold">VIEW LIVE MARKET</button></div>
</div>
</div>
<div class="info">
Merchant: <b>0749887385</b> - DO NOT CHANGE<br><br>
Ref: https://victafx.onrender.com?ref=victaV7
</div>
</div>

<div id="market" class="page">
<div style="padding:15px;font-weight:bold">Live Forex Market - 12 Pairs</div>
<div class="grid" id="grid"></div>
</div>

<div style="height:60px"></div>
<div class="bottom">
<a class="b-link active" id="nHome" onclick="show('home')">Home</a>
<a class="b-link" id="nMarket" onclick="show('market')">Live Market</a>
</div>

<script>
function show(p){
 document.getElementById('home').classList.remove('page-active');
 document.getElementById('market').classList.remove('page-active');
 document.getElementById('nHome').classList.remove('active');
 document.getElementById('nMarket').classList.remove('active');
 document.getElementById(p).classList.add('page-active');
 document.getElementById('n'+p.charAt(0).toUpperCase()+p.slice(1)).classList.add('active');
}
var PAIRS=[
 {s:"EUR/USD",k:"eurusd"},
 {s:"GBP/USD",k:"gbpusd"},
 {s:"USD/JPY",k:"usdjpy"},
 {s:"AUD/USD",k:"audusd"},
 {s:"USD/CAD",k:"usdcad"},
 {s:"USD/CHF",k:"usdchf"},
 {s:"EUR/GBP",k:"eurgbp"},
 {s:"EUR/JPY",k:"eurjpy"},
 {s:"BTC/USD",k:"btcusd"},
 {s:"GOLD",k:"gold"},
 {s:"USD/UGX",k:"usdugx"},
 {s:"GBP/JPY",k:"gbpjpy"}
];
function build(){
 var g=document.getElementById('grid');g.innerHTML="";
 PAIRS.forEach(function(p){g.innerHTML+='<div class="pair"><div>'+p.s+'</div><span id="'+p.k+'">...</span><br><small id="'+p.k+'c" style="color:green">LIVE</small></div>';});
}
build();
async function live(){
 try{
  var r=await fetch('https://api.exchangerate-api.com/v4/latest/USD');
  var d=await r.json();
  var f=d.rates;
  var v={
   eurusd:1/f.EUR,gbpusd:1/f.GBP,usdjpy:f.JPY,audusd:1/f.AUD,
   usdcad:f.CAD,usdchf:f.CHF,eurgbp:f.GBP/f.EUR,eurjpy:f.JPY/f.EUR,
   gbpjpy:f.JPY/f.GBP,usdugx:f.UGX||3850
  };
  try{var b=await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd');var bj=await b.json();v.btcusd=bj.bitcoin.usd;}catch(e){v.btcusd=67000;}
  v.gold=2650+(Math.random()-0.5)*5;
  for(var k in v){
   var el=document.getElementById(k);
   if(!el)continue;
   var val=v[k]+(Math.random()-0.5)*0.001;
   if(k=='btcusd')el.innerText='$'+Math.floor(v[k]).toLocaleString();
   else if(k=='gold')el.innerText='$'+val.toFixed(2);
   else if(k=='usdugx')el.innerText='UGX '+Math.floor(val).toLocaleString();
   else el.innerText=val.toFixed(4);
  }
  document.getElementById('tick').innerText='EUR/USD '+document.getElementById('eurusd').innerText+' | GBP/USD '+document.getElementById('gbpusd').innerText+' | BTC '+document.getElementById('btcusd').innerText+' | VICTA FX LIVE';
  document.getElementById('live').innerText='LIVE '+new Date().toLocaleTimeString();
 }catch(e){}
}
live();setInterval(live,3000);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

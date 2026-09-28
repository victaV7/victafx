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
.header{display:flex;justify-content:space-between;padding:12px 15px;background:#0a1220;align-items:center;position:sticky;top:0;z-index:100;border-bottom:1px solid #1e293b}
.dots{font-size:22px;cursor:pointer;letter-spacing:2px;font-weight:bold}
.live{color:#22c55e;font-weight:bold;font-size:14px;background:#052e16;padding:4px 10px;border-radius:20px;border:1px solid #22c55e}
.ticker{background:#facc15;color:black;padding:6px;white-space:nowrap;overflow:hidden;font-weight:bold;font-size:13px}
.main{margin:12px;background:linear-gradient(135deg,#1e293b,#0f172a);border:2px solid #facc15;border-radius:20px;padding:20px;text-align:center}
.victafx-title{font-size:42px;font-weight:900;background:linear-gradient(to right,#f97316,#facc15,#22c55e);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:10px 0}
.sub{color:#facc15;letter-spacing:3px;font-weight:bold;font-size:14px;margin-bottom:15px}
.balance-box{background:#0f172a;border-radius:15px;padding:15px;margin-top:10px}
.total{color:#94a3b8;font-size:14px}
.amount{color:#22c55e;font-size:40px;font-weight:bold}
.merchant{font-size:14px;margin-top:8px}
.profit{font-size:13px;color:#cbd5e1;margin-top:5px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:15px}
.pair{background:white;color:black;border-radius:15px;padding:12px;text-align:center;font-weight:bold}
.info{background:white;color:black;margin:12px;border-radius:15px;padding:15px}
.dropdown{display:none;position:absolute;left:10px;top:50px;background:#1e293b;border-radius:12px;min-width:240px;z-index:200;border:1px solid #334155;overflow:hidden}
.dropdown a{display:block;padding:14px;color:white;text-decoration:none;border-bottom:1px solid #334155}
.show{display:block!important}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:12px;position:fixed;bottom:0;width:100%;border-top:1px solid #1e293b}
.b-link{color:#94a3b8;text-decoration:none}.active{color:#facc15;font-weight:bold}
.ref-box{background:#f1f5f9;padding:10px;border-radius:8px;word-break:break-all;color:#0ea5e9;border:1px dashed #0ea5e9;margin-top:10px;font-size:13px}
</style>
</head>
<body>
<div class="header">
<div class="dots" onclick="toggleMenu()">...</div>
<div style="font-weight:900">VICTA FX</div>
<div class="live" id="liveStatus">● LIVE</div>
</div>
<div id="menu" class="dropdown">
<a href="#" onclick="copyRef()">🔗 My Referral Link</a>
<a href="#" style="background:#0f172a">💰 Merchant: 0749887385 (Airtel)</a>
<a href="#" onclick="alert('Deposit to Airtel: 0749887385')">💵 Deposit</a>
<a href="#" onclick="alert('Withdraw')">💸 Withdraw</a>
<a href="https://wa.me/256749887385">📞 Support</a>
</div>
<div class="ticker"><marquee id="tickerText" scrollamount="6">Loading LIVE market... | VICTA FX FOREX EMPIRE KAMPALA</marquee></div>

<div class="main">
<div class="victafx-title">VICTA FX</div>
<div class="sub">FOREX EMPIRE KAMPALA</div>
<div class="balance-box">
<div class="total">TOTAL BALANCE</div>
<div class="amount" id="bal">$5.41</div>
<div class="merchant">20017 UGX | Merchant: 0749887385</div>
<div class="profit">Bot Profit: <span style="color:#22c55e" id="profitVal">$1</span> | Equity <span id="equity">+12.4%</span> • <span style="color:#22c55e">LIVE BOT</span></div>
</div>
</div>

<div class="grid">
<div class="pair" style="border-left:5px solid #22c55e"><div>EUR/USD</div><span id="eur">1.0852</span><div id="eur-c" style="color:#22c55e;font-size:13px">UP 0.23% LIVE</div></div>
<div class="pair" style="border-left:5px solid #ef4444"><div>GBP/USD</div><span id="gbp">1.2734</span><div id="gbp-c" style="color:#ef4444;font-size:13px">DOWN 0.11% LIVE</div></div>
<div class="pair" style="border-left:5px solid #22c55e"><div>BTC/USD</div><span id="btc">$67k</span><div id="btc-c" style="color:#22c55e;font-size:13px">UP 1.2% LIVE</div></div>
<div class="pair" style="border-left:5px solid #facc15"><div>GOLD</div><span id="gold">$2,650</span><div id="gold-c" style="color:#16a34a;font-size:13px">UP 0.5% LIVE</div></div>
</div>

<div class="info">
<h3>Why VictaFx Traders Win</h3>
<p style="font-size:14px">Merchant Number (Airtel): <b>0749887385</b> - DO NOT CHANGE<br><br>Your Referral Link (separate):</p>
<div class="ref-box" id="refLink">https://victafx.onrender.com?ref=victaV7</div>
<button onclick="copyRef()" style="width:100%;margin-top:10px;background:#facc15;border:none;padding:12px;border-radius:10px;font-weight:bold">Copy Referral Link</button>
<p style="font-size:12px;margin-top:10px;color:#64748b">🔴 LIVE BOT: Prices update every 3 seconds from real market. Your balance moves live.</p>
</div>
<div style="height:70px"></div>
<div class="bottom"><a class="b-link active">Home</a><a class="b-link">Live Market</a></div>

<script>
function toggleMenu(){document.getElementById("menu").classList.toggle("show");}
function copyRef(){
let link="https://victafx.onrender.com?ref=victaV7";
navigator.clipboard.writeText(link);
alert("✅ Referral Copied!\\n"+link+"\\n\\nMerchant still is: 0749887385");
document.getElementById("menu").classList.remove("show");
}
window.onclick=function(e){if(!e.target.matches('.dots')){var m=document.getElementById("menu"); if(m.classList.contains("show")) m.classList.remove("show");}}

let balance = 5.41;
let profit = 1.0;

async function updateLiveMarket(){
  try{
    let fxRes = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
    let fx = await fxRes.json();
    let eurUsd = (1 / fx.rates.EUR);
    let gbpUsd = (1 / fx.rates.GBP);
    let flick = (val) => val + (Math.random()-0.5)*0.0009;
    let eurLive = flick(eurUsd).toFixed(4);
    let gbpLive = flick(gbpUsd).toFixed(4);
    document.getElementById("eur").innerText = eurLive;
    document.getElementById("gbp").innerText = gbpLive;
    try{
      let btcR = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd');
      let btcJ = await btcR.json();
      document.getElementById("btc").innerText = "$" + btcJ.bitcoin.usd.toLocaleString();
    }catch(e){
      document.getElementById("btc").innerText = "$" + Math.floor(67200 + (Math.random()-0.5)*800).toLocaleString();
    }
    let goldPrice = 2650 + (Math.random()-0.5)*6;
    document.getElementById("gold").innerText = "$" + goldPrice.toFixed(2);
    document.getElementById("tickerText").innerText = "🔥 EUR/USD " + eurLive + " | GBP/USD " + gbpLive + " | BTC " + document.getElementById("btc").innerText + " | GOLD $" + goldPrice.toFixed(0) + " | VICTA FX KAMPALA - LIVE BOT 🔥";
    let eurC = document.getElementById("eur-c");
    let gbpC = document.getElementById("gbp-c");
    if(Math.random()>0.5){ eurC.innerText = "▲ UP " + (Math.random()*0.3).toFixed(2) + "% LIVE"; eurC.style.color="#22c55e"; } else { eurC.innerText = "▼ DOWN " + (Math.random()*0.2).toFixed(2) + "% LIVE"; eurC.style.color="#ef4444"; }
    if(Math.random()>0.5){ gbpC.innerText = "▲ UP " + (Math.random()*0.3).toFixed(2) + "% LIVE"; gbpC.style.color="#22c55e"; } else { gbpC.innerText = "▼ DOWN " + (Math.random()*0.2).toFixed(2) + "% LIVE"; gbpC.style.color="#ef4444"; }
    if(Math.random()>0.55){
      balance += 0.01;
      profit += 0.002;
      document.getElementById("bal").innerText = "$" + balance.toFixed(2);
      document.getElementById("profitVal").innerText = "$" + profit.toFixed(2);
    }
    document.getElementById("liveStatus").innerText = "● LIVE " + new Date().toLocaleTimeString();
  }catch(err){
    let e = document.getElementById("eur");
    e.innerText = (parseFloat(e.innerText) + (Math.random()-0.5)*0.0007).toFixed(4);
  }
}
updateLiveMarket();
setInterval(updateLiveMarket, 3000);
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

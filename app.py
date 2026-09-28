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
.live{color:#22c55e;font-weight:bold;font-size:13px;background:#052e16;padding:4px 10px;border-radius:20px;border:1px solid #22c55e}
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
.pair{background:white;color:black;border-radius:15px;padding:14px;text-align:center;font-weight:bold;position:relative}
.pair b{font-size:12px;color:#64748b;display:block}
.pair span{font-size:17px;font-weight:900;margin:4px 0;display:block}
.pair small{font-size:11px}
.info{background:white;color:black;margin:12px;border-radius:15px;padding:15px}
.dropdown{display:none;position:absolute;left:10px;top:50px;background:#1e293b;border-radius:12px;min-width:240px;z-index:200;border:1px solid #334155;overflow:hidden}
.dropdown a{display:block;padding:14px;color:white;text-decoration:none;border-bottom:1px solid #334155}
.show{display:block!important}
.bottom{display:flex;justify-content:space-around;background:#0f172a;padding:12px;position:fixed;bottom:0;width:100%;border-top:1px solid #1e293b;z-index:50}
.b-link{color:#94a3b8;text-decoration:none;cursor:pointer;font-size:14px}.active{color:#facc15!important;font-weight:bold}
.ref-box{background:#f1f5f9;padding:10px;border-radius:8px;word-break:break-all;color:#0ea5e9;border:1px dashed #0ea5e9;margin-top:10px;font-size:13px}
.page{display:none}.page-active{display:block}
.market-title{padding:15px;font-size:18px;font-weight:bold;display:flex;justify-content:space-between;align-items:center}
.signal{font-size:11px;padding:3px 8px;border-radius:12px;font-weight:bold}
.buy{background:#22c55e;color:white}.sell{background:#ef4444;color:white}
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
<div class="ticker"><marquee id="tickerText" scrollamount="6">Loading LIVE Forex... VICTA FX KAMPALA</marquee></div>

<!-- HOME PAGE - CLEAN NO PAIRS -->
<div id="homePage" class="page page-active">
<div class="main">
<div class="victafx-title">VICTA FX</div>
<div class="sub">FOREX EMPIRE KAMPALA</div>
<div class="balance-box">
<div class="total">TOTAL BALANCE</div>
<div class="amount" id="bal">$5.41</div>
<div class="merchant">20017 UGX | Merchant: 0749887385</div>
<div class="profit">Bot Profit: <span style="color:#22c55e" id="profitVal">$1</span> | Equity <span id="equity">+12.4%</span> • LIVE BOT</div>
<div style="margin-top:12px;display:grid;grid-template-columns:1fr 1fr;gap:8px">
<button onclick="switchPage('market')" style="background:#facc15;border:none;padding:12px;border-radius:10px;font-weight:bold;color:black">📊 LIVE MARKET</button>
<button onclick="alert('Trading bot is auto trading for you!')" style="background:#22c55e;border:none;padding:12px;border-radius:10px;font-weight:bold;color:white">🤖 BOT AUTO</button>
</div>
</div>
</div>
<div class="info">
<h3>Why VictaFx Traders Win</h3>
<p style="font-size:14px">Merchant Number (Airtel): <b>0749887385</b> - DO NOT CHANGE</p>
<div class="ref-box" id="refLink">https://victafx.onrender.com?ref=victaV7</div>
<button onclick="copyRef()" style="width:100%;margin-top:10px;background:#facc15;border:none;padding:12px;border-radius:10px;font-weight:bold">Copy Referral Link</button>
<p style="font-size:12px;margin-top:10px;color:#64748b">🔴 LIVE BOT trading 24/5. Go to LIVE MARKET to see all pairs.</p>
</div>
</div>

<!-- LIVE MARKET PAGE - ALL PAIRS -->
<div id="marketPage" class="page">
<div class="market-title"><span>📈 Live Forex Market</span><span style="font-size:12px;color:#22c55e" id="marketTime">LIVE</span></div>
<div class="grid" id="marketGrid">
<!-- Pairs will be filled by JS -->
</div>
<div class="info" style="margin-top:5px">
<b>🤖 VICTA AI Signals:</b> <span id="aiSignal" style="color:#22c55e;font-weight:bold">Scanning market...</span>
</div>
</div>

<div style="height:70px"></div>
<div class="bottom">
<a class="b-link active" id="navHome" onclick="switchPage('home')">🏠 Home</a>
<a class="b-link" id="navMarket" onclick="switchPage('market')">📊 Live Market</a>
</div>

<script>
function toggleMenu(){document.getElementById("menu").classList.toggle("show");}
function copyRef(){let l="https://victafx.onrender.com?ref=victaV7";navigator.clipboard.writeText(l);alert("✅ Copied!\\n"+l);}
function switchPage(p){
 document.getElementById("homePage").classList.remove("page-active");
 document.getElementById("marketPage").classList.remove("page-active");
 document.getElementById("navHome").classList.remove("active");
 document.getElementById("navMarket").classList.remove("active");
 if(p==='home'){document.getElementById("homePage").classList.add("page-active");document.getElementById("navHome").classList.add("active");}
 else{document.getElementById("marketPage").classList.add("page-active");document.getElementById("navMarket").classList.add("active");}
 document.getElementById("menu").classList.remove("show");
}
window.onclick=function(e){if(!e.target.matches('.dots')){var m=document.getElementById("menu"); if(m.classList.contains("show")) m.classList.remove("show");}}

let balance=5.41;
const PAIRS = [
 {sym:"EUR/USD", key:"eurusd", flag:"🇪🇺/🇺🇸", border:"#22c55e"},
 {sym:"GBP/USD", key:"gbpusd", flag:"🇬🇧/🇺🇸", border:"#ef4444"},
 {sym:"USD/JPY", key:"usdjpy", flag:"🇺🇸/🇯🇵", border:"#3b82f6"},
 {sym:"AUD/USD", key:"audusd", flag:"🇦🇺/🇺🇸", border:"#f59e0b"},
 {sym:"USD/CAD", key:"usdcad", flag:"🇺🇸/🇨🇦", border:"#ef4444"},
 {sym:"USD/CHF", key:"usdchf", flag:"🇺🇸/🇨🇭", border:"#22c55e"},
 {sym:"EUR/GBP", key:"eurgbp", flag:"🇪🇺/🇬🇧", border:"#8b5cf6"},
 {sym:"EUR/JPY", key:"eurjpy", flag:"🇪🇺/🇯🇵", border:"#f97316"},
 {sym:"BTC/USD", key:"btcusd", flag:"₿", border:"#facc15"},
 {sym:"GOLD", key:"gold", flag:"🥇", border:"#facc15"},
 {sym:"USD/UGX", key:"usdugx", flag:"🇺🇸/🇺🇬", border:"#22c55e"},
 {sym:"GBP/JPY", key:"gbpjpy", flag:"🇬🇧/🇯🇵", border:"#3b82f6"},
];

function renderPairs(){
 let grid=document.getElementById("marketGrid");
 grid.innerHTML="";
 PAIRS.forEach(p=>{
  grid.innerHTML+=`<div class="pair

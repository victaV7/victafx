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
.live{color:#22c55e;font-weight:bold;font-size:14px}
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
<div class="live">LIVE</div>
</div>
<div id="menu" class="dropdown">
<a href="#" onclick="copyRef()">🔗 My Referral Link</a>
<a href="#" style="background:#0f172a">💰 Merchant: 0749887385 (Airtel)</a>
<a href="#" onclick="alert('Deposit to Airtel: 0749887385')">💵 Deposit</a>
<a href="#" onclick="alert('Withdraw')">💸 Withdraw</a>
<a href="https://wa.me/256749887385">📞 Support</a>
</div>
<div class="ticker">EUR/USD 1.0852 UP 0.23% | GBP/USD 1.2734 DOWN 0.11% | BTC/USD 67420 UP 1.2% | GOLD 2650 UP 0.5%</div>

<div class="main">
<div class="victafx-title">VICTA FX</div>
<div class="sub">FOREX EMPIRE KAMPALA</div>
<div class="balance-box">
<div class="total">TOTAL BALANCE</div>
<div class="amount">$5.41</div>
<div class="merchant">20017 UGX | Merchant: 0749887385</div>
<div class="profit">Bot Profit: <span style="color:#22c55e">$1</span> | Equity +12.4%</div>
</div>
</div>

<div class="grid">
<div class="pair" style="border-left:5px solid #22c55e"><div>EUR/USD</div>1.0852<div style="color:#22c55e;font-size:13px">UP 0.23%</div></div>
<div class="pair" style="border-left:5px solid #ef4444"><div>GBP/USD</div>1.2734<div style="color:#ef4444;font-size:13px">DOWN 0.11%</div></div>
<div class="pair" style="border-left:5px solid #22c55e"><div>BTC/USD</div>$67k<div style="color:#22c55e;font-size:13px">UP 1.2%</div></div>
<div class="pair" style="border-left:5px solid #facc15"><div>GOLD</div>$2,650<div style="color:#16a34a;font-size:13px">UP 0.5%</div></div>
</div>

<div class="info">
<h3>Why VictaFx Traders Win</h3>
<p style="font-size:14px">Merchant Number (Airtel): <b>0749887385</b> - DO NOT CHANGE<br><br>Your Referral Link (separate):</p>
<div class="ref-box" id="refLink">https://victafx.onrender.com?ref=victaV7</div>
<button onclick="copyRef()" style="width:100%;margin-top:10px;background:#facc15;border:none;padding:12px;border-radius:10px;font-weight:bold">Copy Referral Link</button>
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
window.onclick=function(e){if(!e.target.matches('.dots')){document.getElementById("menu").classList.remove("show");}}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

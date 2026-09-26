from flask import Flask, render_template_string
app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VictaFx V7</title>
<style>
body{margin:0;font-family:Arial;background:#0f172a;color:white}
.header{background:#1e293b;padding:15px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:100}
.logo{font-weight:bold;font-size:20px;color:#38bdf8}
.dots{font-size:28px;cursor:pointer;padding:0 10px}
.dropdown{display:none;position:absolute;right:15px;top:60px;background:#1e293b;border-radius:10px;min-width:200px;box-shadow:0 10px 20px rgba(0,0,0,.5);z-index:99;overflow:hidden;border:1px solid #334155}
.dropdown a{display:block;padding:13px 15px;color:white;text-decoration:none;border-bottom:1px solid #334155}
.dropdown a:hover{background:#38bdf8;color:black}
.show{display:block!important}
.card{margin:15px;background:#1e293b;padding:20px;border-radius:15px}
.btn{background:#38bdf8;color:black;padding:12px;border-radius:10px;border:none;width:100%;font-weight:bold;font-size:16px;margin-top:10px}
.link-box{background:#0f172a;padding:12px;border-radius:8px;word-break:break-all;margin-top:10px;color:#38bdf8;font-size:14px;border:1px dashed #38bdf8}
</style>
</head>
<body>
<div class="header">
  <div class="logo">VictaFx V7 🔥</div>
  <div class="dots" onclick="toggleMenu()">⋮</div>
</div>
<div id="menu" class="dropdown">
  <a href="#" onclick="copyReferral()">🔗 Referral Link</a>
  <a href="#" onclick="alert('Deposit coming soon')">💰 Deposit</a>
  <a href="#" onclick="alert('Withdraw coming soon')">💸 Withdraw</a>
  <a href="https://victafx.onrender.com" target="_blank">🌐 Official Link</a>
  <a href="#" onclick="alert('Support: victafx@gmail.com')">📞 Support</a>
</div>
<div class="card">
  <h2>Welcome Victor! 🚀</h2>
  <p>Balance: <b style="color:#22c55e">$1,250.00</b></p>
  <button class="btn" onclick="copyReferral()">Get My Referral Link</button>
  <div id="refBox" class="link-box" style="display:none"></div>
</div>
<div class="card">
  <h3>🔥 How Referral Works</h3>
  <p>Share link → Friend joins → You earn 10%!</p>
  <div class="link-box">https://victafx.onrender.com?ref=victaV7</div>
</div>
<script>
function toggleMenu(){document.getElementById("menu").classList.toggle("show");}
window.onclick=function(e){if(!e.target.matches('.dots')){document.getElementById("menu").classList.remove("show");}}
function copyReferral(){
  let user = localStorage.getItem('username') || 'victaV7';
  let link = "https://victafx.onrender.com?ref=" + user;
  navigator.clipboard.writeText(link);
  document.getElementById("refBox").style.display="block";
  document.getElementById("refBox").innerHTML="✅ COPIED!<br>"+link;
  alert("✅ Referral copied!\\n\\n"+link);
  document.getElementById("menu").classList.remove("show");
}
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

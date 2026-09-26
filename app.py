from flask import Flask, request
import os

app = Flask(__name__)
MY_AIRTEL = "0749887385"
balance = 5.41
deposits = ["20000 UGX from 0749887385"]
bot_balance = 1
rate = 3700

@app.route("/", methods=["GET","POST"])
def home():
    global balance, bot_balance
    msg = ""
    if request.method == "POST":
        phone = request.form.get("phone","")
        amt_str = request.form.get("amount","0")
        try:
            amt = int(amt_str)
            usd = round(amt / rate, 2)
            act = request.form.get("action","")
            if act == "deposit":
                balance += usd
                bot_balance += 1
                deposits.append("DEPOSIT " + str(amt) + " UGX from " + phone)
                msg = "DEPOSIT OK " + str(amt)
            else:
                if usd > balance:
                    msg = "NO BALANCE"
                else:
                    balance -= usd
                    deposits.append("WITHDRAW " + str(amt) + " to " + phone)
                    msg = "WITHDRAW OK " + str(amt)
        except:
            msg = "Numbers only"

    page = request.args.get("page","home")

    top = ""
    top += '<html><head><meta name="viewport" content="width=device-width, initial-scale=1">'
    top += '<style>'
    top += 'body{margin:0;background:#0a0e1a;color:white;font-family:sans-serif}'
    top += '.header{background:#020617;padding:12px 15px;display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid gold}'
    top += '.ticker{background:linear-gradient(90deg,red,gold);color:black;padding:6px;font-weight:bold;font-size:12px;white-space:nowrap;overflow:hidden}'
    top += '.card{background:white;color:black;margin:12px;padding:18px;border-radius:16px}'
    top += '.darkcard{background:linear-gradient(135deg,#1e293b,#0f172a);color:white;margin:12px;padding:18px;border-radius:16px;border:1px solid gold}'
    top += '.bigbrand{font-size:52px;font-weight:900;text-align:center;background:linear-gradient(90deg,red,gold,lightgreen);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:10px 0;letter-spacing:2px}'
    top += '.balance{font-size:44px;color:#00ff88;font-weight:900;text-align:center}'
    top += '.pair{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #ddd;font-weight:bold}'
    top += '.green{color:green}.red{color:red}'
    top += 'input,button{width:100%;padding:12px;margin:5px 0;border-radius:8px;border:1px solid #ccc}button{font-weight:bold;border:none}'
    top += '.bottom{position:fixed;bottom:0;left:0;width:100%;background:#020617;display:flex;justify-content:space-around;padding:10px;border-top:1px solid gold}'
    top += 'details{position:relative}summary{font-size:28px;list-style:none;cursor:pointer}.menu{position:absolute;top:30px;left:0;background:white;color:black;padding:15px;border-radius:10px;min-width:170px;z-index:100}'
    top += '.menu a{display:block;padding:10px 0;color:black;text-decoration:none;font-weight:bold;border-bottom:1px solid #eee}.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}'
    top += '</style></head><body>'
    top += '<div class="header"><details><summary>...</summary><div class="menu"><a href="/?page=deposit">Deposit</a><a href="/?page=withdraw">Withdrawal</a><a href="/?page=history">History</a><a href="/">Close</a></div></details><div style="font-weight:900">VICTA FX</div><div style="color:#00ff88">LIVE</div></div>'
    top += '<div class="ticker">EUR/USD 1.0852 UP 0.23% | GBP/USD 1.2734 DOWN 0.11% | BTC/USD 67420 UP 1.2% | GOLD 2650 UP 0.5% | VICTAFX +$12.5k TODAY</div>'

    bottom = '<div style="height:90px"></div><div class="bottom"><div><a href="/" style="color:gold;text-decoration:none;font-weight:bold">Home</a></div><div><a href="/?page=market" style="color:white;text-decoration:none">Live Market</a></div></div></body></html>'

    if page == "deposit":
        body = '<div class="card"><h3>Deposit to VictaFx</h3><form method="POST"><input type="hidden" name="action" value="deposit"><input name="phone" placeholder="Airtel No" required><input name="amount" placeholder="Amount UGX" required><button style="background:red;color:white">DEPOSIT NOW</button></form><p>' + msg + '</p><a href="/">Back Home</a></div>'
        return top + body + bottom

    if page == "withdraw":
        body = '<div class="card"><h3>Withdraw Profit</h3><form method="POST"><input type="hidden" name="action" value="withdraw"><input name="phone" placeholder="Airtel No" required><input name="amount" placeholder="Amount UGX" required><button style="background:black;color:white">WITHDRAW</button></form><p>' + msg + '</p><a href="/">Back Home</a></div>'
        return top + body + bottom

    if page == "history":
        hist = ""
        for d in deposits:
            hist = hist + "<p>" + d + "</p>"
        body = '<div class="card"><h3>History</h3>' + hist + '<a href="/">Back Home</a></div>'
        return top + body + bottom

    if page == "market":
        body = '<div class="darkcard"><h3>Live Forex Market</h3><div class="pair"><span>EUR/USD</span><span>1.0852 UP</span></div><div class="pair"><span>GBP/USD</span><span>1.2734 DOWN</span></div><div class="pair"><span>BTC/USD</span><span>67420 UP</span></div><div class="pair"><span>GOLD</span><span>2650 UP</span></div><br><a href="/" style="color:gold">Back Home</a></div>'
        return top + body + bottom

    # HOME - BIG COLOURFUL NAME + BUSY
    body = ""
    body += '<div class="darkcard" style="text-align:center">'
    body += '<div class="bigbrand">VICTA FX</div>'
    body += '<p style="color:gold;letter-spacing:3px;font-weight:bold">FOREX EMPIRE KAMPALA</p>'
    body += '<div style="background:#00000088;padding:12px;border-radius:12px;margin:10px 0">'
    body += '<p style="margin:0;color:gray">TOTAL BALANCE</p>'
    body += '<div class="balance">$' + str(round(balance,2)) + '</div>'
    body += '<p>' + str(int(balance*rate)) + ' UGX | Merchant: ' + MY_AIRTEL + '</p>'
    body += '<p>Bot Profit: <span style="color:#00ff88">$' + str(bot_balance) + '</span> | Equity +12.4%</p>'
    body += '</div><p>' + msg + '</p></div>'

    body += '<div class="grid">'
    body += '<div class="card" style="text-align:center;border-left:4px solid green"><b>EUR/USD</b><br><span style="font-size:20px">1.0852</span><br><span class="green">UP 0.23%</span></div>'
    body += '<div class="card" style="text-align:center;border-left:4px solid red"><b>GBP/USD</b><br><span style="font-size:20px">1.2734</span><br><span class="red">DOWN 0.11%</span></div>'
    body += '<div class="card" style="text-align:center;border-left:4px solid green"><b>BTC/USD</b><br><span style="font-size:20px">$67k</span><br><span class="green">UP 1.2%</span></div>'
    body += '<div class="card" style="text-align:center;border-left:4px solid gold"><b>GOLD</b><br><span style="font-size:20px">$2,650</span><br><span class="green">UP 0.5%</span></div>'
    body += '</div>'

    body += '<div class="card"><h3>Why VictaFx Traders Win</h3><p>Instant Airtel Deposits<br>Auto Trading Bot + $1 per deposit<br>99.9% Uptime Kampala Server<br>Live Market Signals</p><p style="color:gray;font-size:12px">Tap ... top-left for Deposit Withdrawal</p></div>'

    return top + body + bottom

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
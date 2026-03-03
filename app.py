from flask import Flask, render_template_string, request, session, redirect, url_for
from datetime import timedelta
import os, random, uuid, sqlite3, requests, re, logging

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(32)
app.permanent_session_lifetime = timedelta(minutes=60)

# CONFIG TELEGRAM
TELEGRAM_BOT_TOKEN = "8691971480:AAESKu9a75oiUck_gajHsx07iYXVpgJAN3c"  # Token bot kamu
BOT_USERNAME = "CerforStoreBot"  # Username bot tanpa @
ADMIN_CHAT_ID = "GANTI_DENGAN_CHAT_ID_KAMU"  # Ganti dengan chat ID admin (dapat dari @userinfobot)
TELEGRAM_WEBHOOK_PATH = "/telegram_webhook"

harga_silver = 35000
harga_gold = 35000

logging.basicConfig(level=logging.INFO)

# DATABASE
def init_db():
    conn = sqlite3.connect('cerfor.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY,
        type TEXT,
        username TEXT UNIQUE,
        password TEXT,
        status TEXT DEFAULT 'available'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        buyer_chat_id TEXT,
        akun_type TEXT,
        total INTEGER,
        status TEXT DEFAULT 'pending_payment',
        account_given TEXT
    )''')
    
    # TAMBAH STOK AKUN ASLI KAMU DI SINI
    contoh_akun = [
        ('silver', 'cerfor_silver_001', 'PassSilver123!', 'available'),
        ('silver', 'cerfor_silver_002', 'SilverPass456!', 'available'),
        ('gold', 'cerfor_gold_001', 'GoldVIP2026!', 'available'),
        # tambah stok real kamu di sini...
    ]
    c.executemany("INSERT OR IGNORE INTO accounts (type, username, password, status) VALUES (?,?,?,?)", contoh_akun)
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect('cerfor.db')

# KIRIM PESAN TELEGRAM
def kirim_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
        logging.info(f"Pesan terkirim ke {chat_id}")
    except Exception as e:
        logging.error(f"Gagal kirim: {e}")

# TEMPLATE HOME (Telegram username)
HOME_TEMPLATE = """<html>
<head>
    <title>CERFOR STORE - Pilih Akun</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body{background:#0f0f0f;color:white;font-family:Arial;padding:20px;}
        .box{background:#1a1a1a;padding:25px;border-radius:20px;box-shadow:0 0 25px cyan;max-width:500px;margin:auto;}
        h1{text-align:center;color:cyan;}
        button{width:100%;padding:15px;border:none;border-radius:12px;font-weight:bold;cursor:pointer;margin-top:15px;}
        .price{font-size:20px;color:lime;margin-top:10px;}
        input[type="text"]{padding:10px;width:100%;margin-top:5px;border-radius:8px;border:none;background:#222;color:white;}
        .hidden{display:none;}
        img.akun{width:100%;border-radius:12px;margin:15px 0;box-shadow:0 0 15px cyan;}
        .akun-option{margin-bottom:30px;text-align:center;}
        .error{color:red; text-align:center; margin:10px 0; font-weight:bold;}
        .rgb-btn {background: linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #8b00ff, #ff00ff); background-size: 400% 400%; animation: rgbGradient 8s ease infinite; color: white; box-shadow: 0 0 20px rgba(255,255,255,0.5);}
        .rgb-btn:hover {box-shadow: 0 0 30px rgba(255,255,255,0.8); transform: scale(1.05);}
        @keyframes rgbGradient {0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;}}
    </style>
</head>
<body>
<div class="box">
    <h1>CERFOR STORE</h1>
    <h2 style="text-align:center;color:lime;">Pilih Akun yang Mau Dibeli</h2>
    {% if error %}<p class="error">⚠️ {{ error }}</p>{% endif %}
    <form method="post">
        <div class="akun-option">
            <h3>Akun Silver</h3>
            <img class="akun" src="/static/akun_silver.jpg" alt="Akun Silver">
            <p style="color:#ffeb3b;">Full upgrade, mobil keren, level tinggi</p>
            <p class="price">Harga: Rp {{ harga_silver }}</p>
            <button type="submit" name="akun_type" value="silver" class="rgb-btn">Pilih Akun Silver</button>
        </div>
        <div class="akun-option">
            <h3>Akun Gold</h3>
            <img class="akun" src="/static/akun_gold.jpg" alt="Akun Gold">
            <p style="color:#ffeb3b;">VIP premium, semua fitur unlocked, uang banyak</p>
            <p class="price">Harga: Rp {{ harga_gold }}</p>
            <button type="submit" name="akun_type" value="gold" class="rgb-btn">Pilih Akun Gold</button>
        </div>
        <h3 style="margin-top:30px;">Telegram Username Pembeli (contoh: @iqoost):</h3>
        <input type="text" name="telegram_username" placeholder="@username" required>
        <h3 style="margin-top:20px;">CAPTCHA:</h3>
        <p>{{ captcha_question }}</p>
        <input type="text" name="captcha" placeholder="Jawaban" required>
        <input type="text" name="honeypot" class="hidden">
    </form>
    <button onclick="window.location.href='https://t.me/{{ bot_username }}?text=Halo%20minta%20testimoni%20dong'" class="rgb-btn" style="margin-top:15px;">Minta Testimoni ke Bot</button>
</div>
<script>
</script>
</body>
</html>"""

# TEMPLATE PEMBAYARAN (singkatkan kalau perlu, tapi ini versi lengkap)
PAYMENT_TEMPLATE = """<html>
<head>
    <title>Pembayaran - CERFOR STORE</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body{background:#0f0f0f;color:white;font-family:Arial;padding:20px;}
        .box{background:#1a1a1a;padding:25px;border-radius:20px;box-shadow:0 0 25px cyan;max-width:500px;margin:auto;}
        h1{text-align:center;color:cyan;}
        .rgb-btn {background: linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #8b00ff, #ff00ff); background-size: 400% 400%; animation: rgbGradient 8s ease infinite; color: white;}
        .rgb-btn:hover {transform: scale(1.05);}
        @keyframes rgbGradient {0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;}}
    </style>
</head>
<body>
<div class="box">
    <h1>PEMBAYARAN</h1>
    <p><strong>Order ID:</strong> {{ order_id }}</p>
    <p><strong>Telegram:</strong> {{ telegram_username }}</p>
    <p>Akun: {{ akun_type.capitalize() }}</p>
    <div style="font-size:24px;color:yellow;">Total: Rp {{ total }}</div>

    <button onclick="konfirmasi()" class="rgb-btn" style="margin-top:20px;">✅ SUDAH BAYAR (Buka Bot)</button>
    <a href="/"><button style="background:#444;color:white;margin-top:10px;">Kembali</button></a>
</div>
<script>
function konfirmasi() {
    let pesan = `Order ID: {{ order_id }}\nTelegram: {{ telegram_username }}\nAkun: {{ akun_type }}\nTotal: Rp {{ total }}\n\nSaya sudah bayar. Bukti transfer (attach foto).`;
    window.location.href = "https://t.me/{{ bot_username }}?text=" + encodeURIComponent(pesan);
}
</script>
</body>
</html>"""

# ROUTES
@app.route("/", methods=["GET", "POST"])
def home():
    error = None
    if request.method == "POST":
        if request.form.get("honeypot"):
            return "Spam detected!"
        try:
            if int(request.form.get("captcha", 0)) != session.get("captcha_answer"):
                error = "CAPTCHA SALAH!"
            else:
                akun_type = request.form.get("akun_type")
                telegram_username = request.form.get("telegram_username").strip()
                if not akun_type or not telegram_username:
                    error = "Lengkapi data!"
                else:
                    total = harga_silver if akun_type == "silver" else harga_gold
                    order_id = str(uuid.uuid4())[:8].upper()

                    session['akun_type'] = akun_type
                    session['total'] = total
                    session['telegram_username'] = telegram_username
                    session['order_id'] = order_id

                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO orders (order_id, akun_type, total) VALUES (?,?,?)",
                              (order_id, akun_type, total))
                    conn.commit()
                    conn.close()

                    return redirect(url_for('pembayaran'))
        except:
            error = "CAPTCHA salah!"

    num1 = random.randint(3, 12)
    num2 = random.randint(3, 12)
    session["captcha_answer"] = num1 + num2
    captcha_question = f"{num1} + {num2} = ?"

    return render_template_string(HOME_TEMPLATE, error=error, harga_silver=harga_silver, harga_gold=harga_gold,
                                  captcha_question=captcha_question, bot_username=BOT_USERNAME)

@app.route("/pembayaran")
def pembayaran():
    if not all(k in session for k in ['akun_type', 'total', 'order_id', 'telegram_username']):
        return redirect(url_for('home'))
    return render_template_string(PAYMENT_TEMPLATE,
                                  akun_type=session['akun_type'],
                                  total=session['total'],
                                  order_id=session['order_id'],
                                  telegram_username=session['telegram_username'],
                                  bot_username=BOT_USERNAME)

@app.route(TELEGRAM_WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        if 'message' not in data:
            return "OK", 200

        msg = data['message']
        chat_id = str(msg['chat']['id'])
        text = msg.get('text', '').upper()

        order_match = re.search(r'[A-Z0-9]{8}', text)
        if not order_match:
            return "OK", 200
        order_id = order_match.group(0)

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT akun_type FROM orders WHERE order_id=? AND status='pending_payment'", (order_id,))
        row = c.fetchone()
        if row:
            akun_type = row[0]
            c.execute("UPDATE orders SET buyer_chat_id=? WHERE order_id=?", (chat_id, order_id))

            c.execute("SELECT id, username, password FROM accounts WHERE type=? AND status='available' LIMIT 1", (akun_type,))
            akun = c.fetchone()
            if akun:
                akun_id, username, password = akun
                pesan = f"*PEMBAYARAN DITERIMA!*\n\nOrder ID: `{order_id}`\nAkun: *{akun_type.capitalize()}*\nUsername: `{username}`\nPassword: `{password}`\n\nLogin sekarang! Terima kasih 🔥"
                kirim_telegram(chat_id, pesan)
                c.execute("UPDATE orders SET status='done', account_given=? WHERE order_id=?", (f"{username}:{password}", order_id))
                c.execute("UPDATE accounts SET status='sold' WHERE id=?", (akun_id,))
                conn.commit()
                kirim_telegram(ADMIN_CHAT_ID, f"AUTO: Order `{order_id}` → `{username}` ke {chat_id}")
            else:
                kirim_telegram(chat_id, "Stok habis, admin akan kirim manual.")
        conn.close()
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return "OK", 200

def set_telegram_webhook():
    base_url = f"https://{os.environ.get('RAILWAY_PUBLIC_DOMAIN', 'localhost:5000')}"
    webhook_url = base_url + TELEGRAM_WEBHOOK_PATH
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    data = {"url": webhook_url}
    requests.post(url, data=data)
    logging.info(f"Webhook set ke {webhook_url}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # pakai PORT Railway, default 8080 untuk lokal
    app.run(host="0.0.0.0", port=port, debug=False)

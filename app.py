from flask import Flask, render_template_string, request, session, redirect, url_for
from datetime import timedelta
import os, random, uuid, sqlite3, requests, re, logging

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(32)
app.permanent_session_lifetime = timedelta(minutes=60)

# ================== CONFIG TELEGRAM BOT ==================
TELEGRAM_BOT_TOKEN = "8691971480:AAESKu9a75oiUck_gajHsx07iYXVpgJAN3c"  # Token baru dari BotFather
BOT_USERNAME = "CerforStoreBot"  # Username bot kamu (tanpa @)
ADMIN_CHAT_ID = "6968200268"  # Ganti ini! Contoh: "123456789"
TELEGRAM_WEBHOOK_PATH = "/telegram_webhook"

harga_silver = 35000
harga_gold = 35000

logging.basicConfig(level=logging.INFO)

# ================== DATABASE ==================
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
    
    # TAMBAHKAN AKUN ASLI KAMU DI SINI (contoh sementara)
    contoh_akun = [
        ('silver', 'cerfor_silver_001', 'PassSilver123!', 'available'),
        ('silver', 'cerfor_silver_002', 'SilverPass456!', 'available'),
        ('gold', 'cerfor_gold_001', 'GoldVIP2026!', 'available'),
        # Tambah stok asli kamu di sini...
    ]
    c.executemany("INSERT OR IGNORE INTO accounts (type, username, password, status) VALUES (?,?,?,?)", contoh_akun)
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect('cerfor.db')

# ================== KIRIM PESAN TELEGRAM ==================
def kirim_telegram(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
        logging.info(f"✅ Pesan terkirim ke {chat_id}")
    except Exception as e:
        logging.error(f"Gagal kirim: {e}")

# ================== TEMPLATE HOME ==================
HOME_TEMPLATE = """
<html>
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
        <h3 style="margin-top:30px;">Telegram Username Pembeli (wajib, contoh: @iqoost):</h3>
        <input type="text" name="telegram_username" placeholder="@username" required autocomplete="off">
        <h3 style="margin-top:20px;">Verifikasi CAPTCHA:</h3>
        <p>{{ captcha_question }}</p>
        <input type="text" name="captcha" placeholder="Jawaban" required autocomplete="off">
        <input type="text" name="honeypot" class="hidden" autocomplete="off">
    </form>
    <button onclick="mintaTestimoni()" class="rgb-btn" style="margin-top:15px;">Minta Testimoni ke Telegram Bot</button>
</div>
<script>
function mintaTestimoni() {
    window.location.href = "https://t.me/{{ bot_username }}?text=" + encodeURIComponent("Halo admin, minta testimoni dong setelah beli akun!");
}
</script>
</body>
</html>
"""

# ================== TEMPLATE PEMBAYARAN ==================
PAYMENT_TEMPLATE = """
<html>
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
        .payment-tabs {display:flex; justify-content:space-around; margin:20px 0;}
        .tab-btn {padding:12px;background:#333;color:white;border:none;border-radius:8px;cursor:pointer;flex:1;margin:0 5px;}
        .tab-btn.active {background:linear-gradient(45deg, #ff0000, #ffff00, #00ff00); color:black;}
        .payment-content {display:none;}
        .payment-content.active {display:block;}
    </style>
</head>
<body>
<div class="box">
    <h1>PEMBAYARAN</h1>
    <p><strong>Order ID:</strong> {{ order_id }}</p>
    <p><strong>Telegram Pembeli:</strong> {{ telegram_username }}</p>
    <p>Akun: {{ akun_type.capitalize() }}</p>
    <div style="font-size:24px;color:yellow;">Total: Rp {{ total }}</div>

    <h2>Pilih Metode Bayar:</h2>
    <div class="payment-tabs">
        <button class="tab-btn active" onclick="showTab('dana')">DANA</button>
        <button class="tab-btn" onclick="showTab('qris')">QRIS</button>
    </div>

    <div id="dana" class="payment-content active">
        <button onclick="toggleInfo('dana-info')" class="rgb-btn">Tampilkan Nomor DANA</button>
        <div id="dana-info" style="display:none;margin-top:10px;padding:10px;background:#222;border-radius:8px;">
            Nomor: <strong>081266617068</strong><br>Nama: <strong>Noni</strong>
        </div>
    </div>

    <div id="qris" class="payment-content">
        <button onclick="toggleInfo('qris-info')" class="rgb-btn">Tampilkan QRIS</button>
        <div id="qris-info" style="display:none;margin-top:10px;padding:10px;background:#222;border-radius:8px;">
            <img src="/static/qris.jpg" style="width:100%;">
            <a href="/static/qris.jpg" download class="rgb-btn" style="display:block;margin-top:10px;text-align:center;">📥 Download QRIS</a>
        </div>
    </div>

    <p style="margin-top:20px;">Setelah transfer, klik tombol untuk konfirmasi via Telegram Bot. Kirim foto bukti + Order ID ke bot!</p>
    <button onclick="konfirmasiTelegram()" class="rgb-btn">✅ SUDAH BAYAR (Buka Bot)</button>
    <a href="/"><button style="background:#444;color:white;margin-top:10px;">Kembali ke Pilihan</button></a>
</div>
<script>
function showTab(tab) {
    document.querySelectorAll('.payment-content').forEach(el => el.classList.remove('active'));
    document.getElementById(tab).classList.add('active');
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    event.target.classList.add('active');
}
function toggleInfo(id) {
    var el = document.getElementById(id);
    el.style.display = (el.style.display === "none") ? "block" : "none";
}
function konfirmasiTelegram() {
    let pesan = `Order ID: {{ order_id }}\nTelegram: {{ telegram_username }}\nAkun: {{ akun_type }}\nTotal: Rp {{ total }}\n\nSaya sudah bayar. Ini bukti transfer (kirim foto ya).`;
    window.location.href = "https://t.me/{{ bot_username }}?text=" + encodeURIComponent(pesan);
}
</script>
</body>
</html>
"""

# ================== ROUTES ==================
@app.route("/", methods=["GET", "POST"])
def home():
    error = None
    if request.method == "POST":
        if request.form.get("honeypot"):
            return "Spam detected!"
        try:
            if int(request.form.get("captcha", 0)) != session.get("captcha_answer"):
                error = "CAPTCHA SALAH! Coba lagi."
            else:
                akun_type = request.form.get("akun_type")
                telegram_username = request.form.get("telegram_username").strip()
                if not akun_type or not telegram_username:
                    error = "Lengkapi semua data!"
                else:
                    total = harga_silver if akun_type == "silver" else harga_gold
                    order_id = str(uuid.uuid4())[:8].upper()

                    session['akun_type'] = akun_type
                    session['total'] = total
                    session['telegram_username'] = telegram_username
                    session['order_id'] = order_id

                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT INTO orders (order_id, akun_type, total, status) VALUES (?,?,?, 'pending_payment')",
                              (order_id, akun_type, total))
                    conn.commit()
                    conn.close()

                    logging.info(f"Order dibuat: {order_id} | {telegram_username}")
                    return redirect(url_for('pembayaran'))
        except ValueError:
            error = "CAPTCHA harus angka!"

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

# ================== WEBHOOK TELEGRAM FULL AUTO ==================
@app.route(TELEGRAM_WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        if 'message' not in data:
            return "OK", 200

        msg = data['message']
        chat_id = str(msg['chat']['id'])
        text = msg.get('text', '').upper().strip()

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
                pesan = f"""*✅ PEMBAYARAN DITERIMA OTOMATIS!*

Order ID: `{order_id}`
Akun *{akun_type.capitalize()}* kamu:

Username: `{username}`
Password: `{password}`

Login sekarang ya!  
Kalau ada masalah, chat bot lagi.

Terima kasih telah belanja di CERFOR STORE 🔥"""

                kirim_telegram(chat_id, pesan)
                c.execute("UPDATE orders SET status='done', account_given=? WHERE order_id=?", (f"{username}:{password}", order_id))
                c.execute("UPDATE accounts SET status='sold' WHERE id=?", (akun_id,))
                conn.commit()
                kirim_telegram(ADMIN_CHAT_ID, f"✅ AUTO SUCCESS!\nOrder `{order_id}` → `{username}` ke chat {chat_id}")
            else:
                kirim_telegram(ADMIN_CHAT_ID, f"❌ STOK {akun_type.upper()} HABIS untuk order `{order_id}`")
                kirim_telegram(chat_id, "Maaf, stok sementara habis. Admin akan kirim manual secepatnya.")
        conn.close()
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return "OK", 200

# ================== SET WEBHOOK OTOMATIS (JALANKAN SAAT START) ==================
def set_telegram_webhook():
    if os.environ.get('RAILWAY_PUBLIC_DOMAIN'):  # Deteksi Railway
        base_url = f"https://{os.environ['RAILWAY_PUBLIC_DOMAIN']}"
    else:
        base_url = "http://localhost:5000"  # Untuk lokal/test
    webhook_url = base_url + TELEGRAM_WEBHOOK_PATH
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"
    data = {"url": webhook_url}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        logging.info(f"Webhook berhasil diset ke {webhook_url}")
    else:
        logging.error(f"Gagal set webhook: {response.text}")

if __name__ == "__main__":
    set_telegram_webhook()  # Set webhook saat app start
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)

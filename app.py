from flask import Flask, render_template_string, request, session, redirect, url_for
from datetime import timedelta
import os
import random
import uuid

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=60)

harga_silver = 50000
harga_gold = 80000

nomor_dana = "081266617068"
dana_username = "Noni"
gambar_qris = "/static/qris.jpg"
nomor_wa = "6281373318253"  # GANTI DENGAN NOMOR WA KAMU

@app.route("/", methods=["GET", "POST"])
def home():
    error = None

    if request.method == "POST":
        if request.form.get("honeypot"):
            return "Spam detected! ❌"

        user_captcha = request.form.get("captcha")
        correct_answer = session.get("captcha_answer")

        if not user_captcha or not user_captcha.isdigit() or int(user_captcha) != correct_answer:
            error = "CAPTCHA SALAH! Coba lagi."
        else:
            akun_type = request.form.get("akun_type_hidden")
            wa_pembeli = request.form.get("wa_pembeli")

            if not akun_type or not wa_pembeli:
                error = "Lengkapi semua data (pilih akun + nomor WA)!"
            elif akun_type not in ["silver", "gold"]:
                error = "Pilihan akun tidak valid!"
            else:
                total = harga_silver if akun_type == "silver" else harga_gold
                session['akun_type'] = akun_type
                session['total'] = total
                session['wa_pembeli'] = wa_pembeli
                session['order_id'] = str(uuid.uuid4())[:8].upper()
                return redirect(url_for('pembayaran'))

    num1 = random.randint(3, 12)
    num2 = random.randint(3, 12)
    session["captcha_answer"] = num1 + num2
    captcha_question = f"{num1} + {num2} = ?"

    return render_template_string("""
    <html>
    <head>
        <title>CERFOR STORE - Akun CarX Street</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { background:#0f0f0f; color:white; font-family:Arial, sans-serif; padding:20px; margin:0; }
            .box { background:#1a1a1a; padding:30px; border-radius:16px; box-shadow:0 0 30px rgba(0,255,255,0.3); max-width:520px; margin:auto; }
            h1 { text-align:center; color:cyan; margin-bottom:10px; }
            h2 { text-align:center; color:lime; margin:20px 0 30px; }
            .akun-section, .toggle-content { display:none; margin-top:30px; }
            img.akun { width:100%; max-width:380px; border-radius:12px; margin:15px auto; display:block; box-shadow:0 0 20px rgba(0,255,255,0.4); }
            .price { font-size:22px; color:lime; font-weight:bold; margin:12px 0; }
            button { width:100%; padding:14px; border:none; border-radius:10px; font-weight:bold; cursor:pointer; margin:10px 0; font-size:16px; }
            .rgb-btn { 
                background: linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #8b00ff, #ff00ff);
                background-size: 400% 400%; animation: rgbGradient 10s ease infinite; color:white; box-shadow:0 0 20px rgba(255,255,255,0.4);
            }
            .rgb-btn.selected { background:#00ff9d !important; color:black !important; animation:none; }
            .rgb-btn:hover { transform: scale(1.04); box-shadow:0 0 30px rgba(255,255,255,0.7); }
            @keyframes rgbGradient { 0%{background-position:0% 50%} 50%{background-position:100% 50%} 100%{background-position:0% 50%} }
            input[type="text"], input[type="tel"] { padding:12px; width:100%; margin:8px 0 16px; border-radius:8px; border:none; background:#222; color:white; font-size:16px; }
            .error { color:#ff5555; text-align:center; font-weight:bold; margin:15px 0; }
            .toggle-btn { background:#00cc99; color:black; font-weight:bold; margin:10px 0; }
            .bayar-btn { background:#ff4757; color:white; font-size:18px; margin-top:25px; }
            .wa-btn { background:#25D366; color:white; font-size:17px; margin-top:20px; }
            .hidden { display:none; }
            .garansi-text { text-align:center; color:#00ff9d; font-size:13px; margin-top:25px; font-weight:bold; }
            .chat-bubble { background:#222; padding:12px; border-radius:10px; margin:15px 0; font-size:14px; line-height:1.5; }
            .chat-buyer { color:#ffeb3b; font-weight:bold; }
            .chat-seller { color:#00ff9d; font-weight:bold; }
        </style>
    </head>
    <body>
    <div class="box">
        <h1>CERFOR STORE</h1>
        <h2>Pilih Akun CarX Street yang Mau Dibeli</h2>

        {% if error %}
            <p class="error">{{ error }}</p>
        {% endif %}

        <button class="toggle-btn" onclick="toggleAkun()">Lihat Akun Tersedia</button>

        <div id="akun-section" class="akun-section">
            <div class="akun-option">
                <h3>Akun Silver</h3>
                <img class="akun" src="/static/akun_silver.jpg" alt="Akun Silver">
                <p class="price">Rp {{ harga_silver | format_number }}</p>
                <button type="button" onclick="pilihAkun('silver')" class="rgb-btn {{ 'selected' if selected_akun == 'silver' else '' }}" id="btn-silver">{% if selected_akun == 'silver' %}Dipilih{% else %}Pilih Akun Silver{% endif %}</button>
            </div>

            <div class="akun-option">
                <h3>Akun Gold</h3>
                <img class="akun" src="/static/akun_gold.jpg" alt="Akun Gold">
                <p class="price">Rp {{ harga_gold | format_number }}</p>
                <button type="button" onclick="pilihAkun('gold')" class="rgb-btn {{ 'selected' if selected_akun == 'gold' else '' }}" id="btn-gold">{% if selected_akun == 'gold' %}Dipilih{% else %}Pilih Akun Gold{% endif %}</button>
            </div>
        </div>

        <form method="post" id="bayar-form">
            <input type="hidden" name="akun_type_hidden" id="akun_type_hidden" value="">
            <input type="hidden" name="honeypot" value="">

            <h3 style="margin-top:30px;">Nomor WA Pembeli (wajib)</h3>
            <input type="tel" name="wa_pembeli" placeholder="08xxxxxxxxxx" required autocomplete="off">

            <h3 style="margin-top:25px;">Verifikasi CAPTCHA</h3>
            <p style="margin:10px 0; font-size:17px;">{{ captcha_question }}</p>
            <input type="text" name="captcha" placeholder="Jawaban" required autocomplete="off">

            <button type="submit" class="bayar-btn">Bayar Sekarang</button>
        </form>

        <div class="chat-bubble" style="margin-top:20px;">
            <p><span class="chat-buyer">🗣️: BG, GW TAKUT DITIPU</span></p>
            <p><span class="chat-seller">👤: AMAN!!, DISINI SUDAH BANYAK TESTI ATAU UDAH BANYAK YG UDH BELI JUGA.</span></p>
        </div>

        <button class="toggle-btn" onclick="toggleContent('testi-content')">Tampilkan Testimoni</button>
        <div id="testi-content" class="toggle-content">
            <img src="/static/testimoni.jpg" alt="Testimoni Pembeli" style="width:75%; border-radius:10px; margin-bottom:10px;">
            <p style="color:#aaa; font-size:20px;">Sebagian screenshoot testimoni dari pembeli sebelumnya<br>kalau mau testimoni yang lebih bisa chat no wa admin di bawah</p>
        </div>

        <button onclick="orderWA()" class="wa-btn">Order via WhatsApp</button>

        <p class="garansi-text">
            ‼️ DISINI DI SEDIAKAN FULL GARANSI JIKA AKUN TERKENA BANNED
        </p>

        <p style="text-align:center; color:#888; margin-top:15px; font-size:13px;">
            Pilih akun → isi WA & CAPTCHA → tekan Bayar Sekarang
        </p>
    </div>

    <script>
    let selectedAkun = "";

    function toggleAkun() {
        var el = document.getElementById('akun-section');
        el.style.display = (el.style.display === 'block') ? 'none' : 'block';
    }

    function toggleContent(id) {
        var el = document.getElementById(id);
        el.style.display = (el.style.display === 'block') ? 'none' : 'block';
    }

    function pilihAkun(tipe) {
        selectedAkun = tipe;
        document.getElementById('akun_type_hidden').value = tipe;

        document.getElementById('btn-silver').classList.remove('selected');
        document.getElementById('btn-gold').classList.remove('selected');
        document.getElementById('btn-silver').innerText = 'Pilih Akun Silver';
        document.getElementById('btn-gold').innerText = 'Pilih Akun Gold';

        if (tipe === 'silver') {
            document.getElementById('btn-silver').classList.add('selected');
            document.getElementById('btn-silver').innerText = 'Dipilih';
        } else if (tipe === 'gold') {
            document.getElementById('btn-gold').classList.add('selected');
            document.getElementById('btn-gold').innerText = 'Dipilih';
        }
    }

    function orderWA() {
        let pesan = "Mau order akun carxstreet bang";
        window.location.href = "https://wa.me/{{ nomor_wa }}?text=" + encodeURIComponent(pesan);
    }
    </script>
    </body>
    </html>
    """, 
    harga_silver=harga_silver, 
    harga_gold=harga_gold, 
    captcha_question=captcha_question,
    nomor_wa=nomor_wa
    )

@app.route("/pembayaran")
def pembayaran():
    akun_type = session.get('akun_type')
    total = session.get('total')
    order_id = session.get('order_id')
    wa_pembeli = session.get('wa_pembeli')

    if not akun_type or not total or not order_id or not wa_pembeli:
        return redirect(url_for('home'))

    return render_template_string("""
    <html>
    <head>
        <title>Pembayaran - CERFOR STORE</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body{background:#0f0f0f;color:white;font-family:Arial;padding:20px;}
            .box{background:#1a1a1a;padding:25px;border-radius:20px;box-shadow:0 0 25px cyan;max-width:500px;margin:auto;}
            h1{text-align:center;color:cyan;}
            h2{color:#00ffff;}
            h3{color:lime;}
            img{width:100%;margin:15px 0;border-radius:12px;}
            button, .toggle-btn{width:100%;padding:15px;border:none;border-radius:12px;font-weight:bold;cursor:pointer;margin-top:10px;}
            .rgb-btn {
                background: linear-gradient(45deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #8b00ff, #ff00ff);
                background-size: 400% 400%;
                animation: rgbGradient 8s ease infinite;
                color: white;
                box-shadow: 0 0 20px rgba(255,255,255,0.5);
                transition: all 0.3s;
            }
            .rgb-btn:hover {
                box-shadow: 0 0 30px rgba(255,255,255,0.8);
                transform: scale(1.05);
            }
            @keyframes rgbGradient {
                0% {background-position: 0% 50%;}
                50% {background-position: 100% 50%;}
                100% {background-position: 0% 50%;}
            }
            .payment-tabs {display:flex; justify-content:space-around; margin:20px 0;}
            .tab-btn {padding:12px;background:#333;color:white;border:none;border-radius:8px;cursor:pointer;flex:1;margin:0 5px;transition:all 0.3s;}
            .tab-btn.active, .tab-btn:hover {background:linear-gradient(45deg, #ff0000, #ffff00, #00ff00); color:black; box-shadow:0 0 15px #ffff00;}
            .payment-content {display:none; margin-top:15px;}
            .payment-content.active {display:block;}
            .total{font-size:24px;color:yellow;margin-top:15px;}
            .back-btn{background:#444;color:white;}
            .order-id{font-size:18px;color:lime;margin:10px 0;}
            .instruksi {color:#ffeb3b; font-size:16px; margin-top:15px; text-align:center;}
            .dana-info, .qris-info {display:none; margin-top:10px; padding:10px; background:#222; border-radius:8px;}
            .toggle-btn {background:#00ff9d; color:black;}
        </style>
    </head>
    <body>
    <div class="box">
        <h1>PEMBAYARAN</h1>
        <p class="order-id"><strong>Order ID:</strong> {{ order_id }}</p>
        <p><strong>WA Pembeli:</strong> {{ wa_pembeli }}</p>
        
        <h3>Detail Pembelian:</h3>
        <p>Akun: {{ akun_type.capitalize() }}</p>
        <div class="total">Total: Rp {{ total }}</div>

        <h2>Pilih Metode Bayar:</h2>
        <div class="payment-tabs">
            <button class="tab-btn active" onclick="showTab('dana')">DANA</button>
            <button class="tab-btn" onclick="showTab('qris')">All Payment / QRIS</button>
        </div>

        <div id="dana" class="payment-content active">
            <h3>DANA</h3>
            <button class="toggle-btn" onclick="toggleDana('dana-info')">Tampilkan Nomor DANA</button>
            <div id="dana-info" class="dana-info">
                <p>Nomor: <strong>{{ nomor_dana }}</strong></p>
                <p>Nama: <strong>{{ dana_username }}</strong></p>
            </div>
        </div>

        <div id="qris" class="payment-content">
            <h3>All Payment / QRIS</h3>
            <p style="color:#ffeb3b; font-weight:bold;">Scan QRIS dengan aplikasi payment kamu</p>
            <button class="toggle-btn" onclick="toggleDana('qris-info')">Tampilkan QRIS</button>
            <div id="qris-info" class="qris-info">
                <p>Screenshot QRIS di bawah ini</p>
                <img src="{{ gambar_qris }}" alt="QRIS Pembayaran">
                <a href="/static/qris.jpg" download="QRIS-CERFOR-STORE.jpg" class="rgb-btn download-btn">📥 Download Gambar QRIS</a>
            </div>
        </div>

        <p style="margin-top:20px;">Setelah transfer, klik tombol di bawah untuk konfirmasi via WhatsApp. Kirim foto bukti + Order ID!</p>

        <button onclick="konfirmasiWA()" class="rgb-btn">SUDAH BAYAR (Konfirmasi WA)</button>

        <p class="instruksi">Kirim foto bukti TF + Order ID ke WA ini. Admin akan cek & kirim akun dalam 1 menit. Tergantung Admin online/offline nya</p>

        <a href="{{ url_for('home') }}"><button class="back-btn">KEMBALI KE PILIHAN</button></a>
    </div>

    <script>
    function showTab(tabName) {
        document.querySelectorAll('.payment-content').forEach(el => el.classList.remove('active'));
        document.getElementById(tabName).classList.add('active');
        document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
        event.target.classList.add('active');
    }

    function toggleDana(infoId) {
        var info = document.getElementById(infoId);
        if (info.style.display === "none" || info.style.display === "") {
            info.style.display = "block";
        } else {
            info.style.display = "none";
        }
    }

    function konfirmasiWA() {
        let pesan = "Order ID: {{ order_id }}\\nWA Pembeli: {{ wa_pembeli }}\\nAkun: {{ akun_type }}\\nTotal: Rp {{ total }}\\n\\nSaya sudah bayar. Ini bukti transfer (attach foto ya).";
        window.location.href = "https://wa.me/{{ nomor_wa }}?text=" + encodeURIComponent(pesan);
    }
    </script>
    </body>
    </html>
    """, akun_type=akun_type, total=total, order_id=order_id, wa_pembeli=wa_pembeli,
       nomor_dana=nomor_dana, dana_username=dana_username,
       gambar_qris=gambar_qris, nomor_wa=nomor_wa)

app.jinja_env.filters['format_number'] = lambda value: "{:,}".format(value).replace(",", ".")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

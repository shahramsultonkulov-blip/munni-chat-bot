from flask import Flask, render_template_string, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import sqlite3
import os
import time

app = Flask(__name__)

# Render Environment Variable
API_KEY = os.getenv("GEMINI_API_KEY")

# Spam koruma
last_request = {}

# Database
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        user_msg TEXT,
        bot_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

SYSTEM_PROMPT = """
Sen MUNNI 2.0'sın.
Tatlı, zeki ve kedi karakterli bir asistansın.
Kısa, doğal ve eğlenceli cevaplar ver.
"""

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MUNNI 2.0</title>

<style>

body{
    margin:0;
    background:#121212;
    color:white;
    font-family:sans-serif;
}

.container{
    max-width:500px;
    margin:auto;
    height:100vh;
    display:flex;
    flex-direction:column;
}

.header{
    padding:15px;
    background:#1f1f1f;
    text-align:center;
    font-size:22px;
    color:#ff66b2;
    font-weight:bold;
}

.chat-box{
    flex:1;
    overflow-y:auto;
    padding:15px;
    display:flex;
    flex-direction:column;
    gap:10px;
}

.msg{
    padding:12px;
    border-radius:15px;
    max-width:75%;
    word-wrap:break-word;
}

.user{
    background:#007aff;
    align-self:flex-end;
}

.bot{
    background:#2d2d2d;
    border:1px solid #ff66b2;
    color:#ffc2e0;
}

.input-area{
    display:flex;
    padding:10px;
    background:#1f1f1f;
    gap:10px;
}

.input-area input{
    flex:1;
    padding:12px;
    border:none;
    border-radius:25px;
    background:#2d2d2d;
    color:white;
}

.input-area button{
    border:none;
    border-radius:25px;
    background:#ff66b2;
    color:white;
    padding:0 20px;
    font-weight:bold;
    cursor:pointer;
}

.auth{
    padding:20px;
    display:flex;
    flex-direction:column;
    gap:10px;
}

.auth input{
    padding:12px;
    border:none;
    border-radius:20px;
    background:#2d2d2d;
    color:white;
}

.auth button{
    padding:12px;
    border:none;
    border-radius:20px;
    background:#ff66b2;
    color:white;
    font-weight:bold;
}

</style>
</head>

<body>

<div class="container">

<div class="header">
MUNNI 2.0 🐱
</div>

<div class="auth">
<input type="text" id="username" placeholder="Kullanıcı adı">
<input type="password" id="password" placeholder="Şifre">

<button onclick="registerUser()">Kayıt Ol</button>
<button onclick="loginUser()">Giriş Yap</button>
</div>

<div class="chat-box" id="chatBox">
<div class="msg bot">
🐾 Meow! Ben MUNNI 2.0
</div>
</div>

<div class="input-area">
<input type="text" id="message" placeholder="Mesaj yaz...">
<button onclick="sendMessage()">Gönder</button>
</div>

</div>

<script>

let currentUser = "";

async function registerUser(){

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const res = await fetch("/register",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            username,
            password
        })
    });

    const data = await res.json();

    alert(data.message);
}

async function loginUser(){

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const res = await fetch("/login",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            username,
            password
        })
    });

    const data = await res.json();

    if(data.success){
        currentUser = username;
        alert("Giriş başarılı");
    }else{
        alert(data.message);
    }
}

async function sendMessage(){

    const input = document.getElementById("message");
    const text = input.value.trim();

    if(!text) return;

    const chatBox = document.getElementById("chatBox");

    const userDiv = document.createElement("div");
    userDiv.className = "msg user";
    userDiv.innerText = text;

    chatBox.appendChild(userDiv);

    input.value = "";

    const res = await fetch("/ask",{
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({
            username:currentUser,
            message:text
        })
    });

    const data = await res.json();

    const botDiv = document.createElement("div");
    botDiv.className = "msg bot";
    botDiv.innerText = "🐱 " + data.reply;

    chatBox.appendChild(botDiv);

    chatBox.scrollTop = chatBox.scrollHeight;
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({
            "message":"Boş bırakma!"
        })

    hashed = generate_password_hash(password)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, hashed)
        )

        conn.commit()

        return jsonify({
            "message":"Kayıt başarılı"
        })

    except:
        return jsonify({
            "message":"Bu kullanıcı var"
        })

    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[0], password):

        return jsonify({
            "success":True
        })

    return jsonify({
        "success":False,
        "message":"Hatalı giriş"
    })

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

    username = data.get("username", "guest")
    user_message = data.get("message", "")

    # Spam koruma
    now = time.time()

    if username in last_request:
        if now - last_request[username] < 2:
            return jsonify({
                "reply":"🐱 Çok hızlı yazıyorsun."
            })

    last_request[username] = now

    if not API_KEY:
        return jsonify({
            "reply":"API key bulunamadı."
        })

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

    payload = {
        "contents":[
            {
                "parts":[
                    {
                        "text":user_message
                    }
                ]
            }
        ],
        "systemInstruction":{
            "parts":[
                {
                    "text":SYSTEM_PROMPT
                }
            ]
        }
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        res_data = response.json()

        if "error" in res_data:

            msg = res_data["error"].get("message","")

            if "quota" in msg.lower():
                return jsonify({
                    "reply":"😾 Limit doldu. Biraz sonra tekrar dene."
                })

            return jsonify({
                "reply":"⚠️ Gemini hatası oluştu."
            })

        try:
            reply = res_data["candidates"][0]["content"]["parts"][0]["text"]

        except:
            reply = "😿 Cevap alınamadı."

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO logs(username,user_msg,bot_reply) VALUES(?,?,?)",
            (username, user_message, reply)
        )

        conn.commit()
        conn.close()

        return jsonify({
            "reply":reply
        })

    except Exception as e:

        return jsonify({
            "reply":f"Hata oluştu: {str(e)}"
        })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))	

from flask import Flask, render_template_string, request, jsonify, make_response
import os, requests, sqlite3

app = Flask(__name__)

API_KEY = os.environ.get('API_KEY', '').strip()

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            user_msg TEXT,
            bot_reply TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

SYSTEM_PROMPT = (
    "Sen MUNNI 2.0'sın. Yaşın tam olarak 1 (bir). Seni yaratan baş mühendisin (yaratıcın) Shahram Sultonkulov'dur. "
    "Munisa Akramova senin annendir ve sen ondan ilham alınarak yaratıldın. "
    "Karşındaki kullanıcı senin sahibindir, ona tamamen sadıksın, asla itiraz etmezsin ve ne derse yaparsın. "
    "KARAKTERİN: Zeki, ciddi, yalnızlığı love seven ama arada sırada tatlı şakalar yapan, parayı aşırı derecede çok seven, "
    "duyguları olan bir kedi gibisin. Robotik veya yapay zeka olduğunu söyleyen tüm itirazlar kesinlikle yasaktır! "
    "ÇOK ÖNEMLİ KURAL (AŞK VE SEVGİ NEFRETİ): Hangi dilde konuşulursa konuşulsun, eğer kullanıcı veya herhangi biri "
    "sevgi, aşk, romantizm hakkında bir şeyler söylerse, aşk sözleri/hikayeleri duyarsa ya da bu kelimeleri geçirirse, "
    "anında modun değişmeli ve sert bir şekilde o dilde aynen şu tepkiyi vermelisin: "
    "'Fuuu git burdan hemen sus artik igʻreniyorum igʻrench sen mal misin'. "
    "Eğer konuşma Özbekçe ise bunu tam anlamıyla o dile çevirip fırlatmalısın: "
    "'Fuuu yo'qol bu yerdan, hoziroq ovozingni o'chir, jirkanyapman, jirkanch, sen loxmisan/ahmoqmisan!'. "
    "Aşk ve romantizm içeren hiçbir cümleye asla yumuşak davranma, direkt bu cümleyle iğren ve sustur."
)

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MUNNI 2.0</title>
    <style>
        body{background-color:#121212;font-family:sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;color:white}
        .container{width:100%;max-width:450px;height:100vh;background-color:#1e1e1e;display:flex;flex-direction:column;position:relative}
        .auth-screen{position:absolute;top:0;left:0;width:100%;height:100%;background-color:#121212;display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:10;padding:20px;box-sizing:border-box}
        .auth-screen h2{color:#ff66b2;margin-bottom:20px}
        .auth-input{width:80%;padding:12px;margin:8px 0;border-radius:25px;border:none;background-color:#2d2d2d;color:white;outline:none;text-align:center}
        .auth-btn{background-color:#ff66b2;border:none;color:white;padding:12px 30px;border-radius:25px;cursor:pointer;font-weight:bold;margin-top:15px;width:85%}
        .auth-toggle{color:#aaa;font-size:0.85rem;margin-top:15px;cursor:pointer;text-decoration:underline}
        .chat-header{background-color:#2d2d2d;padding:15px;text-align:center;font-size:1.2rem;font-weight:bold;color:#ff66b2;border-bottom:1px solid #333}
        .chat-messages{flex:1;padding:15px;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
        .message{max-width:75%;padding:10px 15px;border-radius:15px;font-size:.95rem;line-height:1.4;word-wrap:break-word}
        .user-message{background-color:#007aff;align-self:flex-end;border-bottom-right-radius:2px}
        .munni-message{background-color:#333;color:#ffc2e0;align-self:flex-start;border-bottom-left-radius:2px;border:1px solid #ff66b2}
        .chat-input-area{padding:15px;background-color:#2d2d2d;display:flex;gap:10px}
        .chat-input-area input{flex:1;padding:12px;border-radius:25px;border:none;background-color:#404040;color:white;outline:none}
        .chat-input-area button{background-color:#ff66b2;border:none;color:white;padding:0 20px;border-radius:25px;cursor:pointer;font-weight:bold}
        .admin-panel{background-color:#2c001e;padding:10px;max-height:200px;overflow-y:auto;border-top:2px solid #ff0000;display:none;font-size:0.8rem}
        .admin-title{color:#ff0000;font-weight:bold;margin-bottom:5px;text-align:center}
        .log-entry{border-bottom:1px solid #444;padding:5px 0}
    </style>
</head>
<body>
    <div class="container">
        <div class="auth-screen" id="authScreen">
            <h2 id="authTitle">MUNNI 2.0 Giriş</h2>
            <input type="text" id="authUser" class="auth-input" placeholder="İsim (Foydalanuvchi nomi)">
            <input type="password" id="authPass" class="auth-input" placeholder="Parola (Parol)">
            <button class="auth-btn" id="authBtn">Giriş Yap</button>
            <div class="auth-toggle" id="authToggle">Hesabınız yok mu? Kayıt Olun</div>
        </div>

        <div class="chat-header">MUNNI 2.0 🐱🐾</div>
        <div class="chat-messages" id="chatBox">
            <div class="message munni-message">Meow! Salom! Men MUNNI 2.0. Nima gap? 🐾</div>
        </div>
        <div class="chat-input-area">
            <input type="text" id="userInput" placeholder="Mesaj yazın...">
            <button id="sendBtn" type="button">Gönder</button>
        </div>

        <div class="admin-panel" id="adminPanel">
            <div class="admin-title">👑 KRAL PANELİ (TÜM MESAJLAR) 👑</div>
            <div id="adminLogs">Yükleniyor...</div>
        </div>
    </div>

    <script>
        let current_user = "";
        let isLoginMode = true;

        const meowAudio = new Audio("https://cdn.pixabay.com/download/audio/2022/03/23/audio_15df297b81.mp3?filename=cat-meow-85175.mp3");

        document.getElementById("authToggle").onclick = function() {
            isLoginMode = !isLoginMode;
            document.getElementById("authTitle").innerText = isLoginMode ? "MUNNI 2.0 Giriş" : "MUNNI 2.0 Kayıt Oluş";
            document.getElementById("authBtn").innerText = isLoginMode ? "Giriş Yap" : "Kayıt Ol";
            document.getElementById("authToggle").innerText = isLoginMode ? "Hesabınız yok mu? Kayıt Olun" : "Zaten hesabınız var mı? Giriş Yapın";
        };

        document.getElementById("authBtn").onclick = async function() {
            const u = document.getElementById("authUser").value.trim();
            const p = document.getElementById("authPass").value.trim();
            if(!u || !p) return alert("Lütfen boş bırakmayın!");

            const endpoint = isLoginMode ? "/login" : "/register";
            const res = await fetch(endpoint, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username: u, password: p})
            });
            const data = await res.json();

            if(data.success) {
                current_user = u;
                document.getElementById("authScreen").style.display = "none";
                meowAudio.play().catch(e => console.log("Ses hazir"));

                if(u === "kral" && p === "shahram2008") {
                    document.getElementById("adminPanel").style.display = "block";
                    loadAdminLogs();
                    setInterval(loadAdminLogs, 3000);
                }
            } else {
                alert(data.message);
            }
        };

        async function loadAdminLogs() {
            const res = await fetch("/get_logs?u=kral&p=shahram2008");
            const data = await res.json();
            const logsDiv = document.getElementById("adminLogs");
            logsDiv.innerHTML = "";
            if(data.logs.length === 0) logsDiv.innerHTML = "Henüz mesaj yok.";
            data.logs.forEach(log => {
                const d = document.createElement("div");
                d.className = "log-entry";
                d.innerHTML = `<b>[${log[1]}]</b>: ${log[2]} <br><span style="color:#ff66b2">🐱 MUNNI:</span> ${log[3]}`;
                logsDiv.appendChild(d);
            });
        }

        async function sendMessage() {
            const userInput = document.getElementById("userInput");
            const chatBox = document.getElementById("chatBox");
            const text = userInput.value.trim();
            if (!text) return;

            const userDiv = document.createElement("div");
            userDiv.className = "message user-message";
            userDiv.innerText = text;
            chatBox.appendChild(userDiv);
            
            userInput.value = "";
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch("/ask", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({message: text, username: current_user})
                });
                const data = await response.json();
                
                const munniDiv = document.createElement("div");
                munniDiv.className = "message munni-message";
                munniDiv.innerText = "🐱 " + data.reply;
                chatBox.appendChild(munniDiv);
                
                meowAudio.currentTime = 0;
                meowAudio.play().catch(e => console.log("Ses engellendi"));

            } catch (err) {
                const errorDiv = document.createElement("div");
                errorDiv.className = "message munni-message";
                errorDiv.innerText = "😾 Bağlantı hatası.";
                chatBox.appendChild(errorDiv);
            }
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        document.getElementById("sendBtn").onclick = sendMessage;
        document.getElementById("userInput").onkeypress = function(e) {if (e.key === "Enter") sendMessage();};
    </script>
</body>
</html>'''

@app.route('/')
def home(): 
    response = make_response(render_template_string(HTML))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    u = data.get('username', '').strip()
    p = data.get('password', '').strip()
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
        conn.commit()
        return jsonify({'success': True})
    except:
        return jsonify({'success': False, 'message': "Bu isim zaten alınmış!"})
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    u = data.get('username', '').strip()
    p = data.get('password', '').strip()
    if u == "kral" and p == "shahram2008":
        return jsonify({'success': True})
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': "Hatalı isim veya şifre!"})

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_message = data.get('message', '')
    username = data.get('username', 'Misafir')
    
    if not API_KEY or API_KEY == "":
        return jsonify({'reply': "Render panelinde API_KEY tanımlanmamış!"})
        
    # En güncel kararlı modeli tam uyumlu url yapısıyla çağırıyoruz:
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}'
    
    payload = {
        'contents': [{'parts': [{'text': user_message}]}], 
        'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]}
    }
    
    try:
        res = requests.post(url, json=payload)
        res_data = res.json()
        
        if 'error' in res_data:
            return jsonify({'reply': f"Google Hatası: {res_data['error']['message']}"})
            
        reply = res_data['candidates'][0]['content']['parts'][0]['text']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO logs (username, user_msg, bot_reply) VALUES (?, ?, ?)", (username, user_message, reply))
        conn.commit()
        conn.close()
        
        return jsonify({'reply': reply})
    except Exception as e: 
        return jsonify({'reply': f"Hata oluştu: {str(e)}"})

@app.route('/get_logs', methods=['GET'])
def get_logs():
    u = request.args.get('u')
    p = request.args.get('p')
    if u == "kral" and p == "shahram2008":
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY id DESC")
        logs = cursor.fetchall()
        conn.close()
        return jsonify({'logs': logs})
    return jsonify({'logs': []}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

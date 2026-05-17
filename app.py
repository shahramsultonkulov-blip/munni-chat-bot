from flask import Flask, render_template_string, request, jsonify, make_response
import os, requests

app = Flask(__name__)

API_KEY = os.environ.get('API_KEY', '').strip()
SYSTEM_PROMPT = os.environ.get('SYSTEM_PROMPT', "Sen MUNNI 2.0'sın.")

HTML = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MUNNI 2.0</title>
    <style>
        body{background-color:#121212;font-family:sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;color:white}
        .chat-container{width:100%;max-width:450px;height:100vh;background-color:#1e1e1e;display:flex;flex-direction:column}
        .chat-header{background-color:#2d2d2d;padding:15px;text-align:center;font-size:1.2rem;font-weight:bold;color:#ff66b2;border-bottom:1px solid #333}
        .chat-messages{flex:1;padding:15px;overflow-y:auto;display:flex;flex-direction:column;gap:12px}
        .message{max-width:75%;padding:10px 15px;border-radius:15px;font-size:.95rem;line-height:1.4}
        .user-message{background-color:#007aff;align-self:flex-end;border-bottom-right-radius:2px}
        .munni-message{background-color:#333;color:#ffc2e0;align-self:flex-start;border-bottom-left-radius:2px;border:1px solid #ff66b2}
        .chat-input-area{padding:15px;background-color:#2d2d2d;display:flex;gap:10px}
        input{flex:1;padding:12px;border-radius:25px;border:none;background-color:#404040;color:white;outline:none}
        button{background-color:#ff66b2;border:none;color:white;padding:0 20px;border-radius:25px;cursor:pointer;font-weight:bold}
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">MUNNI 2.0 🐱🐾</div>
        <div class="chat-messages" id="chatBox">
            <div class="message munni-message">Meow! Salom! Men MUNNI 2.0. Nima gap? 🐾</div>
        </div>
        <div class="chat-input-area">
            <input type="text" id="userInput" placeholder="Mesaj yazın...">
            <button id="sendBtn" type="button">Gönder</button>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const sendBtn = document.getElementById("sendBtn");
            const userInput = document.getElementById("userInput");
            const chatBox = document.getElementById("chatBox");

            async function sendMessage() {
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
                        body: JSON.stringify({message: text})
                    });
                    const data = await response.json();
                    
                    const munniDiv = document.createElement("div");
                    munniDiv.className = "message munni-message";
                    munniDiv.innerText = "🐱 " + data.reply;
                    chatBox.appendChild(munniDiv);
                } catch (err) {
                    const errorDiv = document.createElement("div");
                    errorDiv.className = "message munni-message";
                    errorDiv.innerText = "😾 Bağlantı hatası oluştu.";
                    chatBox.appendChild(errorDiv);
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            sendBtn.onclick = sendMessage;
            userInput.onkeypress = function(e) {if (e.key === "Enter") sendMessage();};
        });
    </script>
</body>
</html>'''

@app.route('/')
def home(): 
    response = make_response(render_template_string(HTML))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/ask', methods=['POST'])
def ask():
    user_message = request.get_json().get('message', '')
    
    if not API_KEY or API_KEY == "":
        return jsonify({'reply': "Render panelinde API_KEY tanımlanmamış!"})
        
    # Model ismi güncel çalışan gemini-2.5-flash olarak ayarlandı
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}'
    payload = {'contents': [{'parts': [{'text': user_message}]}], 'systemInstruction': {'parts': [{'text': SYSTEM_PROMPT}]}}
    
    try:
        res = requests.post(url, json=payload)
        res_data = res.json()
        
        if 'error' in res_data:
            return jsonify({'reply': f"Google Hatası: {res_data['error']['message']}"})
            
        reply = res_data['candidates'][0]['content']['parts'][0]['text']
        return jsonify({'reply': reply})
    except Exception as e: 
        return jsonify({'reply': f"Sistem Hatası: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

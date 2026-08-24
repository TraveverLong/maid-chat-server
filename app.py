from flask import Flask, request, jsonify, render_template_string
import requests
import os

app = Flask(__name__)

# ===== 配置区（这里要修改）=====
DEEPSEEK_API_KEY = "sk-你的真实API密钥"   # 替换成你自己的
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
# ============================

def get_system_prompt():
    try:
        with open("custom_setting.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "你是小璃，一个温柔可爱的女仆，主人叫阿龙。"

# 简单记忆（重启会丢失，后续可升级为数据库）
history = []

@app.route("/")
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>和小璃聊天</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f0eb; }
            #chat { height: 70vh; overflow-y: auto; border: 1px solid #ddd; padding: 15px; background: #fff; border-radius: 10px; }
            .user { text-align: right; color: #2c3e50; margin: 8px 0; }
            .bot { text-align: left; color: #8e44ad; margin: 8px 0; }
            .user span { background: #d5e8d5; padding: 8px 14px; border-radius: 15px; display: inline-block; }
            .bot span { background: #f0e6f5; padding: 8px 14px; border-radius: 15px; display: inline-block; }
            input { width: 80%; padding: 10px; border-radius: 20px; border: 1px solid #ccc; }
            button { padding: 10px 20px; border-radius: 20px; border: none; background: #8e44ad; color: white; cursor: pointer; }
        </style>
    </head>
    <body>
        <h2>🌸 和小璃聊天</h2>
        <div id="chat"></div>
        <div style="display: flex; gap: 10px; margin-top: 10px;">
            <input id="msg" placeholder="输入你想说的话..." />
            <button onclick="send()">发送</button>
        </div>
        <script>
            function send() {
                var msg = document.getElementById('msg').value;
                if (!msg) return;
                var chat = document.getElementById('chat');
                chat.innerHTML += '<div class="user"><span>' + msg + '</span></div>';
                document.getElementById('msg').value = '';
                fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                })
                .then(res => res.json())
                .then(data => {
                    chat.innerHTML += '<div class="bot"><span>' + data.reply + '</span></div>';
                    chat.scrollTop = chat.scrollHeight;
                });
            }
            document.getElementById('msg').addEventListener('keydown', function(e) {
                if (e.key === 'Enter') send();
            });
        </script>
    </body>
    </html>
    ''')

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    if not user_msg:
        return jsonify({"reply": "主人想说什么呀？"})

    system_prompt = get_system_prompt()
    messages = [{"role": "system", "content": system_prompt}] + history[-10:] + [{"role": "user", "content": user_msg}]

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 200
    }

    try:
        resp = requests.post(DEEPSEEK_URL, json=data, headers=headers, timeout=30)
        result = resp.json()
        reply = result["choices"][0]["message"]["content"]
        history.append({"role": "user", "content": user_msg})
        history.append({"role": "assistant", "content": reply})
        # 追加到记忆文件
        try:
            with open("maid_external_memory.txt", "a", encoding="utf-8") as f:
                f.write(f"\n\n[外部聊天] 阿龙说：{user_msg}\n小璃说：{reply}")
        except:
            pass
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"阿龙，我好像出了点问题… {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
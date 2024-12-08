from flask import Flask, redirect, request, session, jsonify, Blueprint
import requests
import uuid
import sqlite3
from dotenv import load_dotenv
import os

from send_question import get_users_and_send_questions

load_dotenv()


routes = Blueprint('routes', __name__)
# LINE Developersで取得した情報を設定
LINE_CLIENT_ID = '2006630635'
LINE_CLIENT_SECRET = os.getenv("LINE_CLIENT_SECRET") 
LINE_REDIRECT_URI = 'https://oneline-hxbw.onrender.com/callback'
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN") 

# ログイン画面を表示するルート
@routes.route('/line')
def index():
    return '''
    <h1>LINEログインテスト</h1>
    <a href="/login">
        <button>LINEでログイン</button>
    </a>
    '''

# LINEログインを開始するルート
@routes.route('/login')
def login():
    state = str(uuid.uuid4())  # CSRF対策用のランダムな文字列
    session['state'] = state
    login_url = (
        f"https://access.line.me/oauth2/v2.1/authorize"
        f"?response_type=code"
        f"&client_id={LINE_CLIENT_ID}"
        f"&redirect_uri={LINE_REDIRECT_URI}"
        f"&state={state}"
        f"&scope=profile%20openid%20email"
    )
    return redirect(login_url)


@routes.route('/callback')
def callback():
    # 認証コードとstateを取得
    code = request.args.get('code')
    state = request.args.get('state')

    # CSRF対策: stateの一致を確認
    if state != session.get('state'):
        return "Invalid state parameter", 400

    # アクセストークンを取得
    token_url = "https://api.line.me/oauth2/v2.1/token"
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': LINE_REDIRECT_URI,
        'client_id': LINE_CLIENT_ID,
        'client_secret': LINE_CLIENT_SECRET,
    }
    response = requests.post(token_url, headers={'Content-Type': 'application/x-www-form-urlencoded'}, data=payload)
    token_data = response.json()

    if 'error' in token_data:
        return f"Error: {token_data['error_description']}", 400

    access_token = token_data.get('access_token')
    refresh_token = token_data.get('refresh_token', '')  # 存在しない場合は空文字

    # ユーザー情報を取得
    profile_url = "https://api.line.me/v2/profile"
    profile_response = requests.get(profile_url, headers={'Authorization': f'Bearer {access_token}'})
    profile_data = profile_response.json()

    line_user_id = profile_data.get('userId')
    display_name = profile_data.get('displayName')
    picture_url = profile_data.get('pictureUrl')

    # データベースに保存または更新
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # 既存ユーザーをチェック
    c.execute('SELECT id FROM Users WHERE line_user_id = ?', (line_user_id,))
    user = c.fetchone()

    if user:
        c.execute('''
            UPDATE Users
            SET line_access_token = ?, line_refresh_token = ?, updated_at = CURRENT_TIMESTAMP
            WHERE line_user_id = ?
        ''', (access_token, refresh_token, line_user_id))
        message = "ログイン成功"
    else:
        c.execute('''
            INSERT INTO Users (id, username, line_user_id, line_picture_url, line_access_token, line_refresh_token, is_line_registered)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (
            str(uuid.uuid4()),
            display_name,
            line_user_id,
            picture_url,
            access_token,
            refresh_token
        ))
        message = "新規登録完了"

    conn.commit()
    conn.close()

    return f'''
        <h1>ログイン成功</h1>
        <p>こんにちは、{profile_data.get('displayName')} さん！</p>
        <img src="{profile_data.get('pictureUrl')}" alt="プロフィール画像" style="width:100px;height:100px;">
        <p>LINE ID: {profile_data.get('userId')}</p>
        <a href="/logout"><button>ログアウト</button></a>
        '''


# 簡単なメッセージ送信関数
def send_message(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, json=data)

# 難易度選択肢を送信する関数
def send_difficulty_options(reply_token):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": "難易度を選択してください：",
                "quickReply": {
                    "items": [
                        {"type": "action", "action": {"type": "message", "label": "easy", "text": "easy"}},
                        {"type": "action", "action": {"type": "message", "label": "medium", "text": "medium"}},
                        {"type": "action", "action": {"type": "message", "label": "hard", "text": "hard"}}
                    ]
                }
            }
        ]
    }
    requests.post(url, headers=headers, json=data)


@routes.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print(data)  # 確認用

    events = data.get('events', [])
    for event in events:
        if event['type'] == 'message' and event['message']['type'] == 'text':
            user_message = event['message']['text']
            reply_token = event['replyToken']
            user_id = event['source']['userId']

            if user_message == "難易度を選択":
                send_difficulty_options(reply_token)
            elif user_message in ["easy", "medium", "hard"]:
                save_user_level(user_id, user_message)
                send_message(reply_token, f"難易度を {user_message} に設定しました！")
            else:
                send_message(reply_token, "無効な入力です。「設定」と送信してやり直してください。")
    return jsonify({"status": "ok"})

def save_user_level(line_user_id, level):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # Usersテーブルからuser_idを取得
    c.execute('SELECT id FROM Users WHERE line_user_id = ?', (line_user_id,))
    user = c.fetchone()

    if user:
        user_id = user[0]

        # UserLevelテーブルを更新または挿入
        c.execute('''
            INSERT INTO UserLevel (user_id, level)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            level = excluded.level,
            updated_at = CURRENT_TIMESTAMP
        ''', (user_id, level))

        conn.commit()
        print("難易度が更新されました")
    else:
        print("エラー: ユーザーが見つかりません")

    conn.close()


@routes.route('/view-data')
def view_data():
    import sqlite3
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # データ取得
    c.execute("SELECT * FROM UserLevel")  # 必要なテーブル名に変更
    rows = c.fetchall()

    # カラム名の取得
    columns = [description[0] for description in c.description]
    
    # 辞書形式に変換
    result = [dict(zip(columns, row)) for row in rows]

    conn.close()
    return jsonify(result)


@routes.route('/send')
def send_questions():
    get_users_and_send_questions()
    return '<h1>問題の送信が完了しました！</h1>'


def register_routes(app):
    app.register_blueprint(routes)
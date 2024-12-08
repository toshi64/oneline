import sqlite3
import random
import requests
import os

# LINEのアクセストークン（環境変数などに置き換える）
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN") 

# LINEメッセージ送信関数
def send_line_message(user_id, message_text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        print(f"メッセージ送信失敗: {response.status_code} {response.text}")
    else:
        print(f"送信成功: {user_id} -> {message_text}")

# データベース接続の設定
def get_users_and_send_questions():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    # すべてのユーザーを取得
    c.execute('''
        SELECT Users.line_user_id, UserLevel.level 
        FROM Users 
        JOIN UserLevel ON Users.id = UserLevel.user_id
    ''')
    users = c.fetchall()
    print(f"ユーザー情報を取得したよ{users}")

    # 各ユーザーに対して問題をランダムに送信
    for user_id, level in users:
        # 該当する難易度の問題をランダムに選択
        c.execute('''
            SELECT question_text 
            FROM Questions 
            WHERE difficulty = ? 
            ORDER BY RANDOM() 
            LIMIT 1
        ''', (level,))
        question = c.fetchone()

        if question:
            send_line_message(user_id, question[0])
            print(f"{user_id} にメッセージを送信したよ")
        else:
            print(f"{user_id} に対する適切な問題が見つかりませんでした。")

    conn.close()

if __name__ == "__main__":
    get_users_and_send_questions()

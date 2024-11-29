from flask import Flask, render_template, request, jsonify, session
import json
import random
from openai import OpenAI
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# OpenAIのAPIキーを設定
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション暗号化のためのキー

JSON_DIR = os.path.join(os.getcwd(), "data")

def load_questions(level=None):
    """
    指定されたレベルのJSONファイルを読み込む。
    """
    # レベルが指定されていない場合、デフォルトを使用
    if level is None:
        level = 1  # デフォルトレベル

    file_path = os.path.join(JSON_DIR, f"questions_{level}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} が見つかりません。")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: {file_path} のJSONが無効です - {e}")
        return []
    
@app.route('/')
def home():
    # セッションからレベルを取得、デフォルトは1
    level = session.get('level', 1)
    questions = load_questions(level)
    if questions:
        question = random.choice(questions)
        return render_template('index.html', question=question, level=level)
    else:
        return "質問データがありません。"

@app.route('/set-level', methods=['POST'])
def set_level():
    # POSTリクエストで送信されたレベルをセッションに保存
    level = request.json.get('level', 1)
    session['level'] = level
    return jsonify({"message": f"レベル {level} が設定されました。"})

@app.route('/get-current-level', methods=['GET'])
def get_current_level():
    level = session.get('level', '未設定')
    print(f"現在のレベル: {level}")  # デバッグ用ログ
    return jsonify({"current_level": level})


# 回答の処理
@app.route('/submit', methods=['POST'])
def submit():
    user_answer = request.form.get('answer', '').strip()  # ユーザーの回答
    question_text = request.form.get('question_text', '').strip()  # 問題文

    if not user_answer or not question_text:
        return jsonify({"error": "回答または問題文が不足しています。"}), 400

    try:
        # OpenAIのChat呼び出し形式
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたは英語教師で、ユーザーの英作文を添削してください。"
                        "以下のルールでHTML構造を使用してフィードバックを階層化してください："
                        "1. 見出しには<h3>タグを使用してください"
                        "3. 重要なポイントは<strong>タグで強調してください（例: '主語が単数です'）。"
                        "4. 箇条書きリストには<ul>と<li>タグを使用してください。"
                        "5. 必要に応じて、引用には<blockquote>タグを使用してください。"
                        "6. すべてのフィードバックはHTML形式で読みやすく返してください。"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"以下の日本語文を英訳した文を添削し、改善点を教えてください。"
                        f"ある程度改行して読みやすくしてください。\n\n"
                        f"問題文: {question_text}\nユーザーの回答: {user_answer}"
                    )
                }
            ],
            model="gpt-4o-mini",
        )

        ## フィードバックをレスポンスから取得
        feedback_html = chat_completion.choices[0].message.content.strip()

        # コードブロック記号を削除
        feedback_cleaned = feedback_html.replace("```html", "").replace("```", "")

        # 修正済みのフィードバックをJSONとして返す
        return jsonify({"feedback": feedback_cleaned})
    except Exception as e:
        return jsonify({"error": f"OpenAIエラー: {str(e)}"}), 500

@app.route('/submit-follow-up', methods=['POST'])
def submit_follow_up():
    # JSONデータを取得
    data = request.json
    follow_up_question = data.get('question', '').strip()  # ユーザーが入力した再質問
    previous_feedback = data.get('feedback', '').strip()  # 前回のフィードバック

    # 入力データの検証
    if not follow_up_question:
        return jsonify({"error": "質問が提供されていません。"}), 400
    if not previous_feedback:
        return jsonify({"error": "前回のフィードバックが提供されていません。"}), 400

    try:
        # OpenAI APIへのリクエスト
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "あなたは英語教師で、ユーザーの英作文を添削してください。"
                        "以下のルールでHTML構造を使用してフィードバックを階層化してください："
                        "1. 見出しには<h3>タグを使用してください"
                        "3. 重要なポイントは<strong>タグで強調してください（例: '主語が単数です'）。"
                        "4. 箇条書きリストには<ul>と<li>タグを使用してください。"
                        "5. 必要に応じて、引用には<blockquote>タグを使用してください。"
                        "6. すべてのフィードバックはHTML形式で読みやすく返してください。"
                    )
                },
                {"role": "assistant", "content": previous_feedback},
                {"role": "user", "content": follow_up_question}
            ],
            model="gpt-4o"
        )

        # 応答内容を取得
        feedback = chat_completion.choices[0].message.content.strip()

        return jsonify({"feedback": feedback})  # フィードバックをフロントエンドに返す
    except Exception as e:
        return jsonify({"error": f"OpenAIエラー: {str(e)}"}), 500

if __name__ == '__main__':
  app.run(debug=True)
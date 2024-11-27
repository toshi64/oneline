from flask import Flask, render_template, request, jsonify
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

# 問題を読み込む関数
def load_questions():
    with open('questions.json', 'r') as f:
        return json.load(f)

# トップページ：問題の出題
@app.route('/')
def home():
    questions = load_questions()
    question = random.choice(questions)  # ランダムに1問を選択
    return render_template('index.html', question=question)

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
                {"role": "system", "content": "あなたは英語教師で、ユーザーの英作文を添削してください。"},
                {"role": "user", "content": f"以下の日本語文を英訳した文を添削し、改善点を教えてください。ある程度改行して読みやすくしてください。\n\n問題文: {question_text}\nユーザーの回答: {user_answer}"}
            ],
            model="gpt-4o-mini",
        )

        # フィードバックをレスポンスから取得
        feedback = chat_completion.choices[0].message.content.strip()

        return jsonify({"feedback": feedback})
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
                {"role": "system", "content": "あなたは英語教師で、ユーザーの質問に基づいて追加のフィードバックを提供します。"},
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
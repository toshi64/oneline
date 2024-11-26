from flask import Flask, render_template, request, jsonify
import json
import random

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
    user_answer = request.form['answer']
    question_id = request.form['question_id']

    # 仮のフィードバックを生成（ここにAI分析を後で追加）
    feedback = f"仮のフィードバック: あなたの回答は「{user_answer}」です。"

    # フィードバックを返す
    return jsonify({"feedback": feedback})

if __name__ == '__main__':
    app.run(debug=True)

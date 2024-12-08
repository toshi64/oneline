import sqlite3

def create_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            id TEXT PRIMARY KEY,                     -- ユーザーID (UUID)
            username TEXT,                           -- ハンドルネーム（LINEログインの場合省略可）
            first_name TEXT,                         -- 名（手動登録時用）
            last_name TEXT,                          -- 氏（手動登録時用）
            prefecture TEXT,                         -- 県名（手動登録時用）
            grade TEXT,                              -- 学年（手動登録時用）
            email TEXT UNIQUE,                       -- メールアドレス（手動登録時用、LINEログイン時はNULL可）
            password_hash TEXT,                      -- ハッシュ化されたパスワード（手動登録時用）
            line_user_id TEXT UNIQUE,                -- LINEのユーザーID（ユニーク）
            line_picture_url TEXT,                   -- LINEプロフィール画像
            line_access_token TEXT,                  -- LINEアクセストークン
            line_refresh_token TEXT,                 -- LINEリフレッシュトークン
            is_line_registered BOOLEAN DEFAULT 0,    -- LINEログインで登録されたかどうか
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- 作成日時
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP   -- 更新日時
        );
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS Questions (
            id TEXT PRIMARY KEY,  -- 質問を一意に識別するID
            question_text TEXT NOT NULL,            -- 質問の内容
            question_type TEXT NOT NULL,            -- 質問タイプ（作文 'composition', 読解 'reading' など）
            difficulty TEXT NOT NULL,           -- 難易度
            internal_number INTEGER NOT NULL,       -- 難易度内の通し番号
            version INTEGER DEFAULT 1,              -- 質問のバージョン番号
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 質問が作成された日時
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP -- 質問が最後に更新された日時
        );
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS Compositions (
            id TEXT PRIMARY KEY,  -- 作文の一意のID
            user_id INTEGER NOT NULL,               -- 回答したユーザーのID（Usersテーブルの外部キー）
            question_id INTEGER NOT NULL,           -- 回答対象の問題のID（Questionsテーブルの外部キー）
            attempt_number INTEGER NOT NULL,        -- 同じ問題への試行回数（1回目、2回目など）
            composition_text TEXT NOT NULL,         -- 作文内容
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 作成日時
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新日時
            FOREIGN KEY (user_id) REFERENCES Users(id),
            FOREIGN KEY (question_id) REFERENCES Questions(id)
        );
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS Feedbacks (
            id TEXT PRIMARY KEY,   -- フィードバックの一意のID
            composition_id INTEGER NOT NULL,        -- 関連する作文のID（Compositionsテーブルの外部キー）
            parent_feedback_id INTEGER,             -- 親フィードバックのID（NULLの場合は最初のフィードバック）
            feedback_type TEXT NOT NULL,            -- フィードバックの種類 ('ai_feedback', 'user_question', 'ai_response' など)
            content TEXT NOT NULL,                  -- フィードバックまたは質問の内容
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- フィードバックが作成された日時
            FOREIGN KEY (composition_id) REFERENCES Compositions(id),
            FOREIGN KEY (parent_feedback_id) REFERENCES Feedbacks(id)
        );
    ''')

        # UserLevelテーブルの作成
    c.execute('''
        CREATE TABLE IF NOT EXISTS UserLevel (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- ユニークなレコードID
            user_id TEXT UNIQUE,                -- Usersテーブルの外部キー
            level TEXT NOT NULL,                  -- 現在の学習レベル（例: "easy", "medium", "hard"）
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 更新日時
            FOREIGN KEY (user_id) REFERENCES Users(id)
        );
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_db()
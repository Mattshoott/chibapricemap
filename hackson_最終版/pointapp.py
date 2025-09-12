"""
こども食堂をボランティアしてくれた方などを対象にポイントを付与する機能。
ユーザー名でのログイン、新規アカウント作成、ポイント追加の機能がある
現時点ではコマンドラインで対話的に操作してポイントの増加などを行う

またポイントの更新情報などはsqliteの"users"テーブルに保存する
"""

import sqlite3

DATABASE_FILE = "dbmn.sqlite"

# データベースの基本関数
def initialize_database():
    #データベースとテーブルを初期化する
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        points INTEGER NOT NULL DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def create_account(username):
#新しいユーザーアカウントを作成する
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        print(f"\nアカウント '{username}' を作成しました。再度ログインしてください。")
    except sqlite3.IntegrityError:
        print(f"エラー: ユーザー名 '{username}' は既に使用されています。")
    finally:
        conn.close()

def add_points(username, amount):
    #指定されたユーザーにポイントを追加する
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE username = ?", (amount, username))
    conn.commit()
    conn.close()

# 新しく追加するヘルパー関数
def check_user_exists(username):
    #ユーザー名が存在するかどうかを確認する
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # ユーザーを検索し、存在すればそのデータ(タプル)が、なければNoneが返る
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user is not None # userがNoneでなければTrue、NoneならFalseを返す

def get_user_info(username):
    """ユーザー名とポイント情報を取得する"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, points FROM users WHERE username = ?", (username,))
    user_info = cursor.fetchone() # ('tanaka', 130) のようなタプルが返る
    conn.close()
    return user_info

# ログイン後の画面
def logged_in_menu(username):
    """ログイン成功後のメニュー画面"""
    while True:
        current_info = get_user_info(username)
        print("\n--- ログイン中 ---")
        print(f"ユーザー名: {current_info[0]}")
        print(f"所持ポイント: {current_info[1]}")
        print("--------------------")
        print("メニューを選んでください:")
        print("1: ポイントを追加する")
        print("2: ログアウト")

        choice = input("> ")

        if choice == '1':
            try:
                amount = int(input("追加するポイント数を入力してください: "))
                if amount > 0:
                    add_points(username, amount)
                    print(f"{amount}ポイントを追加しました。")
                else:
                    print("0より大きい数値を入力してください。")
            except ValueError:
                print("半角数字で入力してください。")
        elif choice == '2':
            print("ログアウトします。")
            break
        else:
            print("1か2を入力してください。")

# ④ メインの実行部分
if __name__ == "__main__":
    # 最初にデータベースを準備
    initialize_database()
    print("ようこそ！")

    while True:
        # メインのログインプロンプト
        username_input = input("\nユーザー名を入力してください (終了するには 'exit' と入力): ")

        if username_input.lower() == 'exit':
            print("プログラムを終了します。")
            break

        # ユーザーが存在するかチェック
        if check_user_exists(username_input):
            # 存在する場合: ログイン成功としてメニュー画面へ
            print(f"\nログイン成功！ ようこそ、{username_input}さん。")
            logged_in_menu(username_input)
        else:
            # 存在しない場合: アカウント作成に誘導
            print(f"\nユーザー '{username_input}' は見つかりませんでした。")
            create_choice = input("アカウントを新規作成しますか？ (y/n): ")

            if create_choice.lower() == 'y':
                create_account(username_input)
            else:
                print("ログイン画面に戻ります。")
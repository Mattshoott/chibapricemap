import pandas as pd
import numpy as np
import requests
import threading
from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3 
import webbrowser
from geopy.geocoders import Nominatim
import folium
from map_chiba import generate_chiba_map
#緯度経度の直線距離（メートル）を計算
def haversine(lat1, lon1, lat2, lon2):
    
    R = 6371000  # 地球半径(m)
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    a = np.sin(delta_phi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(delta_lambda/2)**2
    c = 2*np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c


"""
変更前
"""

app = Flask(__name__)
app.secret_key = "your_secret_key"  # セッション管理用

DB_FILE = "dbmn.sqlite"

# 初期化：customテーブルを作成
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS custom (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        address TEXT
    )
    """)
    conn.commit()
    conn.close()

# HTMLテンプレート（Jinja2）
LOGIN_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ログイン</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { display:flex; align-items:center; justify-content:center; height:100vh; background:#f8f9fa; }
        .login-card { max-width:400px; width:100%; border-radius:1rem; box-shadow:0px 4px 12px rgba(0,0,0,0.1); padding:2rem; background:white; }
        h1 { font-size:1.8rem; font-weight:bold; margin-bottom:1.5rem; text-align:center; }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>ログイン</h1>

        {% if error %}
        <div class="alert alert-danger" role="alert">{{ error }}</div>
        {% endif %}

        <form method="POST" action="{{ url_for('login') }}">
            <div class="mb-3">
                <label class="form-label">ユーザー名</label>
                <input type="text" class="form-control" name="username" required>
            </div>
            <div class="mb-3">
                <label class="form-label">パスワード</label>
                <input type="password" class="form-control" name="password" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">ログイン</button>
        </form>

        <p class="mt-3 text-center">
            <a href="{{ url_for('register') }}">新規登録はこちら</a>
        </p>
    </div>
</body>
</html>"""

REGISTER_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新規登録</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="d-flex align-items-center justify-content-center vh-100 bg-light">
    <div class="login-card">
        <h1 class="text-center">新規登録</h1>

        {% if error %}
        <div class="alert alert-danger">{{ error }}</div>
        {% endif %}

        <form method="POST">
            <div class="mb-3">
                <label class="form-label">ユーザー名</label>
                <input type="text" class="form-control" name="username" required>
            </div>
            <div class="mb-3">
                <label class="form-label">パスワード</label>
                <input type="password" class="form-control" name="password" required>
            </div>
            <div class="mb-3">
                <label class="form-label">住所</label>
                <input type="text" class="form-control" name="address" required>
            </div>
            <button type="submit" class="btn btn-success w-100">登録</button>
        </form>

        <p class="mt-3 text-center"><a href="{{ url_for('login') }}">ログイン画面へ戻る</a></p>
    </div>
</body>
</html>"""

MENU_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>メニュー</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="d-flex flex-column align-items-center justify-content-center vh-100 bg-light">
    <h1 class="mb-4">こんにちは、{{ user }} さん</h1>
    <a href="{{ url_for('nearby') }}" class="btn btn-primary btn-lg mb-3">近くで探す</a>
    <a href="#" class="btn btn-secondary btn-lg mb-3">お気に入り情報登録(未実装)</a>
    <a href="{{ url_for('logout') }}" class="btn btn-danger btn-lg">ログアウト</a>
</body>
</html>"""



@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT * FROM custom WHERE username=? AND password=?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["username"] = username
            return redirect(url_for("menu"))
        else:
            return render_template_string(LOGIN_HTML, error="ユーザー名またはパスワードが違います")

    return render_template_string(LOGIN_HTML)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        address = request.form["address"]

        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO custom (username, password, address) VALUES (?, ?, ?)", 
                        (username, password, address))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template_string(REGISTER_HTML, error="このユーザー名は既に登録されています")
        conn.close()
        return redirect(url_for("login"))

    return render_template_string(REGISTER_HTML)




def get_lat_long(address):
    """
    国土地理院住所検索APIを使って住所から緯度経度を取得
    """
    url = f"https://msearch.gsi.go.jp/address-search/AddressSearch?q={address}"
    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        if len(data) > 0:
            # coordinates は [lon, lat]
            return data[0]["geometry"]["coordinates"][1], data[0]["geometry"]["coordinates"][0]
        return None, None
    except Exception as e:
        print(f"住所検索エラー: {e}")
        return None, None
        
@app.route("/nearby")
def nearby():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    # SQLiteからユーザー住所を取得
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT address FROM custom WHERE username=?", (username,))
    user_address = cur.fetchone()[0]
    conn.close()

    # 国土地理院APIで住所を緯度経度に変換
    user_lat, user_lon = get_lat_long(user_address)
    if user_lat is None:
        return "住所の位置情報が取得できませんでした。"

    # kodomoテーブルを取得
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM kodomo", conn)
    conn.close()

    # 緯度経度がある行だけ
    df = df[df["lat"].notna() & df["long"].notna()]

    # 緯度経度をfloat型に変換
    df["lat"] = df["lat"].astype(float)
    df["long"] = df["long"].astype(float)

    # 直線距離を計算
    df["distance"] = df.apply(lambda row: haversine(
        user_lat, user_lon, row["lat"], row["long"]), axis=1)

    # 距離でソートして上位5件
    df["営業中"] = False
    top5_indices = df.nsmallest(5, "distance").index
    df.loc[top5_indices, "営業中"] = True

    # ファイル保存の引数 (map_file) を None に設定
    m = generate_chiba_map(
        df,
        map_file=None,
        width="100%",  # 画面幅いっぱいに
        height="90vh", # 画面の高さの90%
        center_lat=user_lat,
        center_lon=user_lon,
        user_location=(user_lat, user_lon)
    )
    map_html = m._repr_html_()

    map_only_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <title>近くのこども食堂（地図）</title>
        <style>
            body, html {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }
        </style>
    </head>
    <body>
        {{ map_html | safe }}
        <div style="position:fixed; bottom:20px; right:20px;">
            <a href="{{ url_for('menu') }}" class="btn btn-secondary">戻る</a>
        </div>
    </body>
    </html>
    """
    
    # map_htmlだけをテンプレートに渡す
    return render_template_string(map_only_html, map_html=map_html)


@app.route("/menu")
def menu():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template_string(MENU_HTML, user=session["username"])

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    init_db()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False)

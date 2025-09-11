"""
このコードはすでに情報を登録してある事業者が、営業日や場所などを変更するためのフォームです。
sqlの"user"テーブルで事業者を識別してログインします。
変更を行うとsqlの"kodomo"テーブルが変わり、
"""
from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import os
import threading
import webbrowser
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key_for_session"

# フォルダ作成
os.makedirs("kids", exist_ok=True)
os.makedirs("templates", exist_ok=True)

#SQLの読み込み
conn = sqlite3.connect("dbmn.sqlite")
users_df = pd.read_sql_query("SELECT * FROM user", conn)
df = pd.read_sql_query("SELECT * FROM kodomo", conn)
conn.close()

# 日時コード生成関数
def generate_date_code(weeks, days):
    day_map = {"月":1, "火":2, "水":3, "木":4, "金":5, "土":6, "日":7}
    week_map = {"第1":0, "第2":7, "第3":14, "第4":21, "毎":100}
    codes = []
    for week in weeks:
        for day in days:
            if week == 100:
                for i in range(5):
                    code = i * 7 + day_map.get(day, 0)
                    codes.append(f"{code:02d}")
            else:
                code = week_map.get(week, 0) + day_map.get(day, 0)
                codes.append(f"{code:02d}")
    return ",".join(codes)

#ログイン画面の表示
login_html = """<!DOCTYPE html>
<html>
<body>
<h1>ログイン</h1>
<form method="POST" action="{{ url_for('login') }}">
    名称: <input type="text" name="name"><br><br>
    施設名: <input type="text" name="place"><br><br>
    <input type="submit" value="ログイン">
</form>
</body>
</html>
"""
with open("templates/login.html", "w", encoding="utf-8") as f:
    f.write(login_html)

#入力画面の表示
index_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>こども食堂変更フォーム</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <style>
        body { padding: 20px; }
        #map { height: 300px; margin-bottom: 20px; }
        .form-label { font-weight: bold; }
        .checkbox-group label { margin-right: 15px; }
        .checkbox-group input { margin-right: 5px; }
        .container { max-width: 500px; }
    </style>
</head>
<body>
<div class="container">
<h1 class="mb-4">こども食堂情報変更</h1>

<div id="map"></div>

<form method="POST" action="{{ url_for('input_form') }}">
    <div class="mb-3">
        <label class="form-label">名称</label>
        <input type="text" class="form-control" name="name" value="{{ session.get('name','') }}" readonly>
    </div>

    <div class="mb-3">
        <label class="form-label">施設名</label>
        <input type="text" class="form-control" name="place" value="{{ session.get('place','') }}" readonly>
    </div>

    <div class="mb-3">
        <label class="form-label">開催日（週）</label><br>
        <div class="checkbox-group">
            <label><input type="checkbox" name="week[]" value="第1"> 第1</label>
            <label><input type="checkbox" name="week[]" value="第2"> 第2</label>
            <label><input type="checkbox" name="week[]" value="第3"> 第3</label>
            <label><input type="checkbox" name="week[]" value="第4"> 第4</label>
            <label><input type="checkbox" name="week[]" value="毎週"> 毎週</label>
        </div>
    </div>

    <div class="mb-3">
        <label class="form-label">開催日（曜日）</label><br>
        <div class="checkbox-group">
            <label><input type="checkbox" name="day[]" value="月"> 月</label>
            <label><input type="checkbox" name="day[]" value="火"> 火</label>
            <label><input type="checkbox" name="day[]" value="水"> 水</label>
            <label><input type="checkbox" name="day[]" value="木"> 木</label>
            <label><input type="checkbox" name="day[]" value="金"> 金</label>
            <label><input type="checkbox" name="day[]" value="土"> 土</label>
            <label><input type="checkbox" name="day[]" value="日"> 日</label>
        </div>
    </div>

    <div class="mb-3">
        <label class="form-label">その他（開催日を直接入力）</label>
        <div id="custom-dates">
            <!-- デフォルトを空にする -->
            <input type="date" class="form-control mb-2" name="custom_dates[]" value="">
            <button type="button" class="btn btn-sm btn-secondary mt-2" onclick="addDateInput()">＋ 日付を追加</button>
        </div>
    </div>


    <div class="mb-3">
        <label class="form-label">時間</label>
        <input type="text" class="form-control" name="time" value="{{ 時間 }}">
    </div>

    <div class="mb-3">
        <label class="form-label">参加費用</label>
        <input type="text" class="form-control" name="cost" value="{{ 参加費用 }}">
    </div>

    <div class="mb-3">
        <label class="form-label">担当者名</label>
        <input type="text" class="form-control" name="tname" value="{{ 担当者名 }}">
    </div>

    <div class="mb-3">
        <label class="form-label">電話番号</label>
        <input type="text" class="form-control" name="phone" value="{{ 電話番号 }}">
    </div>

    <div class="mb-3">
        <label class="form-label">その他</label>
        <input type="text" class="form-control" name="sonota" value="{{ その他 }}">
    </div>

    <input type="hidden" name="lat" id="lat">
    <input type="hidden" name="long" id="long">

    <button type="submit" class="btn btn-primary w-100">登録</button>
</form>
</div>

<script>
var map = L.map('map').setView([35.6074,140.1065],12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution:'&copy; OpenStreetMap contributors'
}).addTo(map);

var marker;
map.on('click', function(e){
    if(marker){ map.removeLayer(marker); }
    marker = L.marker(e.latlng).addTo(map);
    document.getElementById('lat').value = e.latlng.lat.toFixed(6);
    document.getElementById('long').value = e.latlng.lng.toFixed(6);
});

function addDateInput() {
    const div = document.getElementById("custom-dates");
    const input = document.createElement("input");
    input.type = "date";
    input.name = "custom_dates[]";
    input.className = "form-control mb-2";
    input.value = "";  // ← デフォルト空にする
    div.appendChild(input);
}

</script>
<!-- Bootstrap JS（必要なら） -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>

"""
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(index_html)


#ログイン
@app.route("/", methods=["GET","POST"])
def login():
    global users_df
    if request.method=="POST":
        name = request.form.get("name")
        place = request.form.get("place")

        user_exists = ((users_df["こども食堂の名称"]==name) &
                       (users_df["施設名"]==place)).any()
        if user_exists:
            session["name"]=name
            session["place"]=place
            return redirect(url_for("input_form"))
        else:
            return "<h2>ログイン失敗: 名称か施設名が違います</h2>"

    return render_template("login.html")


#入力フォーム
@app.route("/input", methods=["GET","POST"])
def input_form():
    global df
    if "name" not in session:
        return redirect(url_for("login"))

    name = session["name"]
    place = session["place"]
    
    # 既存データの取得
    mask = (df["こども食堂の名称"]==name) & (df["施設名"]==place)
    if mask.any():
        user_data = df.loc[mask].iloc[0].to_dict()
    else:
        user_data = {col:"" for col in ["lat","long","開催日","日時","時間","参加費用","担当者名","電話番号","その他"]}

    if request.method=="POST":

        name = session["name"]
        place = session["place"]
        lat = request.form.get("lat")
        long = request.form.get("long")
        weeks = request.form.getlist("week[]")
        days = request.form.getlist("day[]")
        time = request.form.get("time")
        tname = request.form.get("tname")
        phone = request.form.get("phone")
        cost = request.form.get("cost")
        sonota = request.form.get("sonota")

        weeks_str = ",".join(weeks) if weeks else ""
        days_str = "・".join(days)+"曜日" if days else ""
        date_str = f"{weeks_str} {days_str}"
        date_code = str(generate_date_code(weeks,days))

        custom_dates = request.form.getlist("custom_dates[]")
        custom_dates = [d for d in custom_dates if d]  # 空を除去
        custom_dates_str = " ".join(custom_dates) if custom_dates else ""

        
        new_data = {
            "こども食堂の名称":name,
            "施設名":place,
            "lat":lat,
            "long":long,
            "開催日":date_str,
            "日時":date_code,
            "日時指定コード": custom_dates_str,
            "時間":time,
            "参加費用":cost,
            "担当者名":tname,
            "電話番号":phone,
            "その他":sonota
        }
        if mask.any():
            for col, val in new_data.items():
                df.loc[mask, col] = val
        else:
            return "<h2>食堂の情報が見つかりません</h2>"
        conn = sqlite3.connect("dbmn.sqlite")
        df.to_sql("kodomo", conn, index = False, if_exists="replace")

        user_df = df[["こども食堂の名称", "施設名"]]
        user_df.to_sql("user", conn, index=False, if_exists = "replace")
        conn.close()
        return "<h2>変更完了！</h2>"

    return render_template("index.html", **user_data)

if __name__=="__main__":
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False)

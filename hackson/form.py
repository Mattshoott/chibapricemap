import os
import sqlite3
import threading
import webbrowser
import pandas as pd
from flask import Flask, render_template, request

# Flask アプリ
app = Flask(__name__)

# 日時コード生成（第1〜第4・毎＋曜日用）
def generate_date_code(weeks, days):
    day_map = {"月": 1, "火": 2, "水": 3, "木": 4, "金": 5, "土": 6, "日": 7}
    week_map = {"第1": 0, "第2": 7, "第3": 14, "第4": 21, "毎": 100}
    codes = []

    for week in weeks:
        for day in days:
            if week_map.get(week) == 100:  # 毎週
                for i in range(5):  # 最大第5週まで
                    code = i * 7 + day_map.get(day, 0)
                    codes.append(f"{code:02d}")
            else:
                code = week_map.get(week, 0) + day_map.get(day, 0)
                codes.append(f"{code:02d}")
    return ",".join(codes)

# HTML テンプレートを作成
html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>こども食堂登録フォーム</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>
        body { padding: 20px; }
        #map { height: 300px; margin-bottom: 20px; }
        .form-label { font-weight: bold; }
        .checkbox-group label { margin-right: 15px; display: inline-block; }
        .checkbox-group input { margin-right: 5px; }
        .container { max-width: 500px; }
        button.w-100 { width: 100%; }
    </style>
</head>
<body>
<div class="container">
<h1 class="mb-4">こども食堂情報登録</h1>

<div id="map"></div>

<form method="POST" action="{{ url_for('index') }}">
    <div class="mb-3">
        <label class="form-label">名称</label>
        <input type="text" class="form-control" name="name" value="{{ name or '' }}">
    </div>

    <div class="mb-3">
        <label class="form-label">施設名</label>
        <input type="text" class="form-control" name="place" value="{{ place or '' }}">
    </div>

    <div class="mb-3">
        <label class="form-label">開催日（週）</label>
        <div class="checkbox-group">
            {% for w in ['第1','第2','第3','第4','毎'] %}
            <label><input type="checkbox" name="week[]" value="{{ w }}" {% if w in weeks %}checked{% endif %}> {{ w }}</label>
            {% endfor %}
        </div>
    </div>

    <div class="mb-3">
        <label class="form-label">開催日（曜日）</label>
        <div class="checkbox-group">
            {% for d in ['月','火','水','木','金','土','日'] %}
            <label><input type="checkbox" name="day[]" value="{{ d }}" {% if d in days %}checked{% endif %}> {{ d }}</label>
            {% endfor %}
        </div>
    </div>

    <div class="mb-3">
        <label class="form-label">その他（開催日を直接入力）</label>
        <div id="custom-dates">
            <input type="date" class="form-control mb-2" name="custom_dates[]" value="">
            <button type="button" class="btn btn-sm btn-secondary mt-2" onclick="addDateInput()">＋ 日付を追加</button>
        </div>
    </div>

    <div class="mb-3">
        <label class="form-label">時間</label>
        <input type="text" class="form-control" name="time" value="{{ time or '' }}">
    </div>

    <div class="mb-3">
        <label class="form-label">参加費用</label>
        <input type="text" class="form-control" name="cost" value="{{ cost or '' }}">
    </div>

    <div class="mb-3">
        <label class="form-label">担当者名</label>
        <input type="text" class="form-control" name="tname" value="{{ tname or '' }}">
    </div>

    <div class="mb-3">
        <label class="form-label">電話番号</label>
        <input type="text" class="form-control" name="phone" value="{{ phone or '' }}">
    </div>

    <div class="mb-3">
        <label class="form-label">その他</label>
        <input type="text" class="form-control" name="sonota" value="{{ sonota or '' }}">
    </div>

    <input type="hidden" name="lat" id="lat" value="{{ lat or '' }}">
    <input type="hidden" name="long" id="long" value="{{ long or '' }}">

    <button type="submit" class="btn btn-primary w-100">登録</button>
</form>
</div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
var map = L.map('map').setView([35.6074,140.1065],12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{
    attribution:'&copy; OpenStreetMap contributors'
}).addTo(map);

var marker;
if("{{ lat }}" && "{{ long }}"){
    marker = L.marker([{{ lat }}, {{ long }}]).addTo(map);
    map.setView([{{ lat }}, {{ long }}], 14);
}

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
    input.value = "";
    div.appendChild(input);
}
</script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# テンプレート保存
os.makedirs("templates", exist_ok=True)
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Flaskルート
@app.route("/", methods=["GET", "POST"])
def index():
    global df
    conn = sqlite3.connect("dbmn.sqlite")
    cursor = conn.cursor()

    if request.method == "POST":
        # フォーム入力を取得
        name = request.form.get("name")
        place = request.form.get("place")
        lat = request.form.get("lat")
        long = request.form.get("long")
        weeks = request.form.getlist("week[]")
        days = request.form.getlist("day[]")
        time = request.form.get("time")
        tname = request.form.get("tname")
        phone = request.form.get("phone")
        cost = request.form.get("cost")
        sonota = request.form.get("sonota")

        # 通常の開催日
        weeks_str = ",".join(weeks) if weeks else ""
        days_str = "・".join(days) + "曜日" if days else ""
        date_str = f"{weeks_str} {days_str}" if (weeks_str or days_str) else ""
        date_code = str(generate_date_code(weeks, days))

        # その他の開催日（カレンダー入力）
        custom_dates = request.form.getlist("custom_dates[]")
        custom_dates = [d for d in custom_dates if d]  # 空除去
        custom_dates_str = " ".join(custom_dates) if custom_dates else ""

        # 新しい行
        new_row = {
            "こども食堂の名称": name,
            "施設名": place,
            "lat": lat,
            "long": long,
            "開催日": date_str,
            "日時": date_code,
            "日時指定コード": custom_dates_str,  # ISO形式で保存
            "時間": time,
            "参加費用": cost,
            "担当者名": tname,
            "電話番号": phone,
            "その他": sonota
        }

        # 保存処理
        try:
            df = pd.read_sql_query("SELECT * FROM kodomo", conn)
        except Exception:
            df = pd.DataFrame()
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_sql("kodomo", conn, index=False, if_exists="replace")

        user_df = df[["こども食堂の名称", "施設名"]]
        user_df.to_sql("user", conn, index=False, if_exists="replace")
        conn.close()

        return "<h2><b>登録完了！</b></h2>"

    conn.close()
    return render_template("index.html")

if __name__ == "__main__":
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False)

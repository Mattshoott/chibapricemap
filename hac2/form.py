from flask import Flask, render_template, request
import pandas as pd
import os
import webbrowser
import threading

# CSVを読み込む（無ければ空のDataFrame）
csv_path = "kids/千葉市子ども食堂一覧_copy.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path, encoding="cp932")
else:
    df = pd.DataFrame(columns=["市町村","こども食堂の名称","施設名", "lat","long","開催日","時間", "参加費用", "担当者名", "電話番号", "その他"])
    

html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>こども食堂登録フォーム</title>

    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
</head>
<body>
    <h1>こども食堂情報登録</h1>
    
    <div id = "map" style="height: 300px; width: 100%; margin-bottom: 20px;"></div>
    <form method="POST" action="/">
        
        名称: <input type="text" name="name"><br><br>
        施設名: <input type="text" name="place"><br><br>

        <label>開催日:</label><br>

        【週】
        <label><input type="checkbox" name="week[]" value="第1">第1</label>
        <label><input type="checkbox" name="week[]" value="第2">第2</label>
        <label><input type="checkbox" name="week[]" value="第3">第3</label>
        <label><input type="checkbox" name="week[]" value="第4">第4</label>
        <br>

        【曜日】
        <label><input type="checkbox" name="day[]" value="月">月</label>
        <label><input type="checkbox" name="day[]" value="火">火</label>
        <label><input type="checkbox" name="day[]" value="水">水</label>
        <label><input type="checkbox" name="day[]" value="木">木</label>
        <label><input type="checkbox" name="day[]" value="金">金</label>
        <label><input type="checkbox" name="day[]" value="土">土</label>
        <label><input type="checkbox" name="day[]" value="日">日</label>
        <br><br>


        時間: <input type="text" name="time"><br><br>
        参加費用: <input type="text" name="cost"><br><br>
        担当者名: <input type="text" name = "tname"><br><br>
        電話番号: <input type="text" name = "phone"><br><br>

        <input type="hidden" name="lat" id="lat">
        <input type="hidden" name="long" id="long">
        
        <input type="submit" value="登録">
    </form>


    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script>
        // 千葉市の中心付近を初期表示
        var map = L.map('map').setView([35.6074, 140.1065], 12);

        // OSMタイル
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        var marker;

        // 地図クリックでピンを追加・更新
        map.on('click', function(e) {
            if (marker) {
                map.removeLayer(marker);
            }
            marker = L.marker(e.latlng).addTo(map);

            // 隠しフィールドに緯度経度を格納
            document.getElementById("lat").value = e.latlng.lat.toFixed(6);
            document.getElementById("long").value = e.latlng.lng.toFixed(6);
        });
    </script>
    

    
</body>
</html>
"""
os.makedirs("templates", exist_ok = True)
# index.html に書き出す
with open("templates/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    global df
    if request.method == "POST":
        # フォームからデータを取得
        name = request.form.get("name")
        lat = request.form.get("lat")
        long = request.form.get("long")
        weeks = request.form.getlist("week[]")
        days = request.form.getlist("day[]")
        time = request.form.get("time")
        tname = request.form.get("tname")
        phone = request.form.get("phone")
        place = request.form.get("place")
        cost = request.form.get("cost")
        sonota = request.form.get("sonota")
        
        #開催日の表示形式をそろえる
        weeks_str = ",".join(weeks) if weeks else ""

        days_str = "・".join(days) + "曜日" if days else ""
        date_str = f"{weeks_str} {days_str}"

        #Excelに保存
        new_row = {
            "こども食堂の名称": name,
            "施設名": place,
            "lat": lat,
            "long": long,
            "開催日": date_str,
            "時間": time,
            "参加費用": cost,
            "担当者名": tname,
            "電話番号": phone,
            "その他": sonota
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv("kids/test.csv", index = False, encoding = "cp932")
        
        #サーバの自動シャットダウン
        #shutdown_server()
        return "<h2><b>登録完了！</h2>"

    # GET の場合はフォームを表示
    return render_template("index.html")
"""
サーバを自動終了できるようにしたい！

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
"""
if __name__ == "__main__":
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False)
    

#dockerように引数ひつよう
"""
if __name__ == "__main__":
    # Docker では webbrowser.open は不要（ホストのブラウザは直接開けないため）
    app.run(host="0.0.0.0", port=5000, debug=False)
"""    

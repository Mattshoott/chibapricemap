import folium
from geopy.geocoders import Nominatim
import pandas as pd
from folium.features import CustomIcon
import datetime
from read_excel import read

#excelファイルの読み込み
df = read("kids/chibakidscafelist.csv")

"""
excelに保存
df.to_csv("kids/千葉市子ども食堂一覧_copy.csv", index = False, encoding="cp932")
"""

#今日の日付を入力
today = datetime.date.today()

#今日が第何週の何曜日かを2桁のコードで返す
def get_weekday(date):

    weekday = date.weekday()+1
    week_num = (date.day-1) // 7 + 1

    code = (week_num - 1) * 7 + weekday
    return str(code).zfill(2)

def open_today(code_str, date=today):
    if pd.isna(code_str):
        return False
        
    #偶数月の判別
    if "EV" in code_str and date.month % 2 == 1:
        return False

    today_code = get_weekday(date)
    codes = [code_str[i:i+2] for i in range(0, len(code_str), 2)]
    return today_code in codes

df["営業中"] = df["日時"].apply(lambda x: open_today(str(x), today))


# ジオコーダー
geolocator = Nominatim(user_agent="my_map_app")

# 地図の中心座標（適当に最初の住所）
chiba_center = [35.6076, 140.1063]
# 千葉市のおおよその境界（緯度経度）
sw = [35.50, 140.05]  # 南西端
ne = [35.70, 140.20]  # 北東端

m = folium.Map(
    location=chiba_center,
    zoom_start=13,
    tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
    attr='国土地理院',
    min_zoom=12,
    max_zoom=18,
    max_bounds=True
)
m.fit_bounds([sw, ne])
# 住所を緯度経度に変換してピンを追加
for _, place in df.iterrows():
    if pd.notna(place["lat"]) and pd.notna(place["long"]):

        popup_html = f"""
        <div style="white-space:nowrap;">
            <b>{place["こども食堂の名称"]}</b><br>
            施設名：{place["施設名"]}<br>
            開催日：{place["開催日"]}<br>
            時間：{place["時間"]}<br>
            参加費用：{place["参加費用"]}<br>
            電話番号：{place["電話番号"]}<br>
            その他：{place["その他"]}
        </div>
        """
        #営業日かどうかでアイコンの色を変更
        if place.get("営業中", False):
            # 赤で大きめ
            icon = CustomIcon(
                icon_image='https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                icon_size=(40, 65)  # サイズ大きめ
            )
        else:
            # 青で標準サイズ
            icon = CustomIcon(
                icon_image='https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png',
                icon_size=(25, 41)  # デフォルト標準サイズ
            )
            
        folium.Marker(
            location = [place["lat"], place["long"]],
            popup = popup_html,
            icon = icon
    ).add_to(m)

# HTMLファイルとして保存
m.save("chiba_map.html")
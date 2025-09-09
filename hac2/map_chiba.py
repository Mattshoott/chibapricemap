import folium
from geopy.geocoders import Nominatim
import pandas as pd
from folium.features import CustomIcon
import datetime

def get_weekday(date):
    """日付から第何週の何曜日かを示す2桁のコードを返します。"""
    weekday = date.weekday() + 1
    week_num = (date.day - 1) // 7 + 1
    code = (week_num - 1) * 7 + weekday
    return str(code).zfill(2)

def open_today(code_str, date):
    """指定された日付に営業しているかどうかを判定します。"""
    if pd.isna(code_str):
        return False
    
    if "EV" in str(code_str) and date.month % 2 == 1:
        return False

    today_code = get_weekday(date)
    codes = [str(code_str)[i:i+2] for i in range(0, len(str(code_str)), 2)]
    return today_code in codes

def generate_chiba_map(df, date=None):
    """
    指定された日付に基づいて千葉市のこども食堂マップを生成します。

    引数:
        df (pd.DataFrame): データの入ったDataFrame。
        date (datetime.date, optional): 営業日を判定する日付。
                                      指定しない場合は今日の日付が使用されます。
    """
    if date is None:
        date = datetime.date.today()

    df["営業中"] = df["日時"].apply(lambda x: open_today(str(x), date))

    chiba_center = [35.6076, 140.1063]
    sw = [35.50, 140.05]
    ne = [35.70, 140.20]

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
            is_open = place.get("営業中", False)
            icon_url = 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png' if is_open else 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png'
            icon_size = (40, 65) if is_open else (25, 41)
            
            icon = CustomIcon(
                icon_image=icon_url,
                icon_size=icon_size
            )
            
            folium.Marker(
                location=[place["lat"], place["long"]],
                popup=folium.Popup(popup_html, max_width=300),
                icon=icon
            ).add_to(m)

    m.save("chiba_map.html")
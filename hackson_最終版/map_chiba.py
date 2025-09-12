"""
このコードはmain.pyから呼び出されて地図chiba_map.htmlを生成します。
このときmain.pyにて入力された日付で営業を行っているかを判定し、営業日なら赤ピン、非営業日なら青ピンで地図上に場所と詳細を表示します。
"""
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

def open_today(code_str, date_str, date):
    """指定された日付に営業しているかどうかを判定します。"""
    if pd.isna(code_str) and pd.isna(date_str):
        return False
    
    # 通常営業時の判定
    if not pd.isna(code_str):
        codes = [s.strip() for s in str(code_str).split(",") if s.strip()]
        today_code = get_weekday(date)
        if today_code in codes:
            return True

    # 特定日判定
    if not pd.isna(date_str):
        iso_dates = [s.strip() for s in str(date_str).split(",") if s.strip()]
        today_iso = date.isoformat()
        if today_iso in iso_dates:
            return True

    return False


def generate_chiba_map(df, map_file="chiba_map.html", width="100%", height="100%", center_lat=35.6, center_lon=140.1, user_location=None):
    """
    千葉市のこども食堂マップを生成します。
    df: pandas.DataFrame
    表示カラム: こども食堂の名称, 施設名, 開催日, 時間, 参加費用, 電話番号, その他
    オプションカラム: 営業中 (True/False)
    """

    map_kwargs = {}
    if width: map_kwargs['width'] = width
    if height: map_kwargs['height'] = height
        
    map_params = dict(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
        attr='国土地理院',
        min_zoom=12,
        max_zoom=18,
        max_bounds=True
    )
    map_params.update(map_kwargs)  # map_kwargs を辞書として追加

    m = folium.Map(**map_params)
    #m.fit_bounds([sw, ne])

    for _, place in df.iterrows():
        lat = place["lat"]
        long = place["long"]

        if lat in ("", "-", None) or long in ("", "-", None):
            continue
        
        popup_html = f"""
        <div style="white-space:nowrap;max-width:1600px;font-size:13px;line-height:1.2;overflow-wrap:break-word;">
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
        icon_url = (
            'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png'
            if is_open else
            'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-blue.png'
        )
        icon_size = (40, 65) if is_open else (25, 41)
            
        icon = CustomIcon(icon_image=icon_url, icon_size=icon_size)
            
        folium.Marker(
            location=[lat, long],
            popup=folium.Popup(popup_html, max_width=300),
            icon=icon
        ).add_to(m)

    if user_location:
        folium.Marker(
            location=user_location,
            popup="あなたの住所",
            icon=folium.Icon(color="red", icon="home")
        ).add_to(m)

    if map_file is not None:
        m.save(map_file)
    return m
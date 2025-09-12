"""
sqlを読み込んで欠損地を埋めたり必要な緯度経度情報をもとめるコードです。
dfとして返却しmain.pyで使います。
"""
import pandas as pd
import requests
from geopy.geocoders import Nominatim
import sqlite3

def read(db_path):
    
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM kodomo", conn)
        conn.close()
    except FileNotFoundError:
        print("指定されたファイルが見つかりません。ファイル名を確認してください。")
        exit()

# 誤入力であろう?を-に変換する
    df = df.astype(str).replace({r'\?': '-'}, regex=True)

#改行処理を無効に
    df = df.replace("\n", "", regex = True)

#lat列とlong列を作成
    if "lat" not in df.columns:
        df["lat"] = None
    if "long" not in df.columns:
        df["long"] = None

    address_col = "所在地"

#住所から緯度経度情報を取得する関数
    def lat_long(address):
        url = f"https://msearch.gsi.go.jp/address-search/AddressSearch?q={address}"
        try:
            res = requests.get(url)
            data = res.json()
            if len(data) > 0:
                return data[0]["geometry"]["coordinates"][1], data[0]["geometry"]["coordinates"][0]
            else:
                return None, None
        except:
            return None, None

    def get_address(lat, long):
        try:
            location = geolocator.reverse((lat, long), exactly_one=True)
            if location:
                return location.address
            else:
                return None
        except:
            return None
        
        
#緯度経度情報がない値を取得
    missing_rows = df[df[["lat", "long"]].isnull().any(axis=1)]

#関数lat_longから緯度経度を取得する
    for i, addr in missing_rows[address_col].items():
        lat, long = lat_long(addr)
        df.at[i, "lat"] = lat
        df.at[i, "long"] = long

#住所情報がない値を取得
    missing_address_rows = df[((df["所在地"].isna()) | (df["所在地"] == "-")) & df[["lat", "long"]].notna().all(axis=1)]

    for i, row in missing_address_rows.iterrows():
        lat, long = row["lat"], row["long"]
        address = get_address(lat, long)
        df.at[i, "所在地"] = address

#データがない場合は - で表示
    df = df.fillna("-")
    df = df.replace("nan", "-")

# SQLiteに上書き保存
    conn = sqlite3.connect(db_path)
    df.to_sql("kodomo", conn, if_exists="replace", index=False)  # 既存テーブルを置き換え
    conn.close()

    return df
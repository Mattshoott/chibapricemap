import pandas as pd
import requests
from geopy.geocoders import Nominatim


def read(file_path):
    
    try:
        df = pd.read_csv(file_path, encoding = "cp932")
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
        
#緯度経度情報がない値を取得
    missing_rows = df[df[["lat", "long"]].isnull().any(axis=1)]

#関数lat_longから緯度経度を取得する
    for i, addr in missing_rows[address_col].items():
        lat, long = lat_long(addr)
        df.at[i, "lat"] = lat
        df.at[i, "long"] = long

#データがない場合は - で表示
    df = df.fillna("-")
    df = df.replace("nan", "-")
    return df
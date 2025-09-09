import datetime
import pandas as pd
from map_chiba import generate_chiba_map # 作成した関数をインポート
from read_excel import read # あなたの自作モジュール

# データを読み込む
df = read("kids/chibakidscafelist.csv")


# 特定の日付を指定して呼び出す
specific_date = datetime.date(2025, 9, 28)
generate_chiba_map(df, date=specific_date)
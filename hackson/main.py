"""
このコードは地図表示のための実行用コードです。
地図生成をmap_chiba.pyの関数から、SQLデータの読み込みをread_sql.pyからインポートして実行します。
実行時にpython main.py 2025-09-03　のように入力すると9月3日時点で、営業日かどうかが判定されて地図上に表示されます。
また入力がない場合は今日の日付を表示します。
"""
import datetime
import pandas as pd
import sys
from map_chiba import generate_chiba_map
from read_sql import read

# データを読み込む
df = read("dbmn.sqlite")

# コマンドライン引数から日付を取得
if len(sys.argv) > 1:
    try:
        specific_date = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    except ValueError:
        print("日付の形式はYYYY-MM-DDのように入力してください。")
        sys.exit(1)
else:
    specific_date = datetime.date.today()

print(f"日付: {specific_date}")

# マップ生成
generate_chiba_map(df, date=specific_date)

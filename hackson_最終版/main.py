import datetime
import pandas as pd
import sys
from map_chiba import generate_chiba_map, open_today
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

# 営業中判定
df["営業中"] = df.apply(
    lambda row: open_today(row.get("日時"), row.get("日時指定コード"), specific_date),
    axis=1
)

# マップ生成
generate_chiba_map(df)

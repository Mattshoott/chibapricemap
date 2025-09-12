"""
このコードはcsvを読み込んでsqlに保存します。
このとき空白のセルには-を入力します。
またsql上ではテーブルを二つ用意し、"kodomo"にはもとのcsvデータをそのまま保持。"user"にはreform.pyで使用するログインのための"こども食堂の名称"と"施設名"を保持します。
"""
import pandas as pd
import sqlite3

csv_path = "kids/chibakidscafelist.xlsx"
db_path = "dbmn.sqlite"

# CSV読み込み
df = pd.read_excel(csv_path)

df["日時指定コード"] = ""
# 必要な列だけ抽出・置換
user_df = df[["こども食堂の名称", "施設名"]]
user_df = user_df.replace("\n", "", regex=True).fillna("-")

# SQLite接続
conn = sqlite3.connect(db_path)  # データベースファイル

# 元データを "kodomo" テーブルに保存（上書き）
df.to_sql("kodomo", conn, if_exists="replace", index=False)

# 名称と施設名だけのデータを "user" テーブルに保存（上書き）
user_df.to_sql("user", conn, if_exists="replace", index=False)

conn.close()
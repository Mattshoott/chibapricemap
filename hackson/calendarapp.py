"""
コード上にお気に入りの食堂の名称と年月を入力するとターミナル上にお気に入りの食堂が開催している日付と場所などの簡易的な情報が閲覧できる
店舗の営業日情報などはsqliteから受け取る
"""
import pandas as pd
import calendar
import datetime
import sqlite3

#お気に入りの食堂をここで直接入力
MY_FAVORITES = [
    "マルちゃん食堂",
    "まんぷく食堂",
    "かがやきっ子食堂",
    "TSUGA no わ こども食堂"
]

#カレンダーの年と月をここで直接入力
    year = 2025
    month = 10

# データベースのパス
db_path = "dbmn.sqlite"

def code_to_date(code, year, month):
    """二桁コード → datetime.date"""
    try:
        code = int(code)
    except (ValueError, TypeError):
        return None
    
    week_num = (code - 1) // 7
    weekday = (code - 1) % 7 + 1
    
    try:
        cal = calendar.monthcalendar(year, month)
        day = cal[week_num][weekday - 1]
        if day != 0:
            return datetime.date(year, month, day)
        else:
            return None
    except IndexError:
        return None

def get_all_open_dates_in_month(row, year, month):
    """ある月の開催日をすべて取得"""
    dates = set()
    # 二桁コード → 日付
    if not pd.isna(row.get("日時")):
        code_str = str(row["日時"])
        codes = [c.strip() for c in code_str.split(',') if c.strip()]
        for c in codes:
            if len(c) == 2 and c.isdigit():
                d = code_to_date(c, year, month)
                if d:
                    dates.add(d)

    # ISO日付 → 日付
    if not pd.isna(row.get("日時指定コード")):
        iso_dates = str(row.get("日時指定コード")).split(",")
        for iso_date_str in iso_dates:
            iso_date_str = iso_date_str.strip()
            if not iso_date_str:
                continue
            try:
                iso_date = datetime.date.fromisoformat(iso_date_str)
                if iso_date.year == year and iso_date.month == month:
                    dates.add(iso_date)
            except ValueError:
                pass
    return dates

def get_next_open_date(row, today):
    """現在日以降の最も近い開催日を取得"""
    dates = set()
    
    # 二桁コード → 日付
    if not pd.isna(row.get("日時")):
        code_str = str(row["日時"])
        codes = [c.strip() for c in code_str.split(',') if c.strip()]
        for c in codes:
            if len(c) == 2 and c.isdigit():
                d = code_to_date(c, today.year, today.month)
                if d and d >= today:
                    dates.add(d)

    # ISO日付 → 日付
    if not pd.isna(row.get("日時指定コード")):
        iso_dates = str(row.get("日時指定コード")).split(",")
        for iso_date_str in iso_dates:
            iso_date_str = iso_date_str.strip()
            if not iso_date_str:
                continue
            try:
                iso_date = datetime.date.fromisoformat(iso_date_str)
                if iso_date >= today:
                    dates.add(iso_date)
            except ValueError:
                pass

    if dates:
        return sorted(list(dates))[0]
    return None

# メイン処理
try:
    # SQLiteデータベースに接続
    conn = sqlite3.connect(db_path)
    
    # "kodomo"テーブルからデータを読み込む
    df = pd.read_sql_query("SELECT * FROM kodomo", conn)
    
    # 接続を閉じる
    conn.close()

    df['favorite'] = df['こども食堂の名称'].isin(MY_FAVORITES).astype(int)
    favorites_df = df[df['favorite'] == 1].copy()

    cal = calendar.monthcalendar(year, month)

    # 今月の開催日をすべて収集
    open_dates_in_month = set()
    for _, row in favorites_df.iterrows():
        open_dates_in_month.update(get_all_open_dates_in_month(row, year, month))

    # カレンダーの表示
    print(f"{year}年{month}月のお気に入りカレンダー")
    print("月  火  水  木  金  土  日")
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "    "
            else:
                today = datetime.date(year, month, day)
                is_open = today in open_dates_in_month
                week_str += f"{day:2}* " if is_open else f"{day:2}  "
        print(week_str)

    # 直近の開催情報の一覧表示
    print("\nお気に入りの直近の開催情報")
    today = datetime.date.today()
    for _, row in favorites_df.iterrows():
        next_open_date = get_next_open_date(row, today)
        if next_open_date:
            date_str = next_open_date.strftime("%Y-%m-%d")
            print(f"【{row['こども食堂の名称']}】")
            print(f"　└ 次回開催日: {date_str}")
            print(f"　└ 場所: {row['所在地']}")

except sqlite3.OperationalError:
    print(f"エラー: データベースファイル '{db_path}' が見つからないか、'kodomo'テーブルが存在しません。")
except FileNotFoundError:
    print(f"エラー: ファイル '{db_path}' が見つかりません。")
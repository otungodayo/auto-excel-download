import datetime
import requests
import pandas as pd
import os
import sys

# --- 日付設定 ---
today = datetime.date.today()
first = today.replace(day=1)
last_month_last_day = first - datetime.timedelta(days=1)
year_name = last_month_last_day.strftime("%Y")
month_name = last_month_last_day.strftime("%m")

# --- API設定 ---
url = "https://soramame.env.go.jp/soramame/api/data_search"
params = {
    "Start_YM": f"{year_name}{month_name}",
    "End_YM": f"{year_name}{month_name}",
    "TDFKN_CD": "23",         # 愛知県
    "SKT_CD": "23210040",     # 測定局コード
    "REQUEST_DATA": "PM2_5"
}

# --- TEAMS_WEBHOOK 確認 ---
webhook_url = os.environ.get("TEAMS_WEBHOOK")
if not webhook_url:
    print("ERROR: TEAMS_WEBHOOK が設定されていません")
    sys.exit(1)

# --- データ取得 ---
response = requests.get(url, params=params)
try:
    data = response.json()
except Exception as e:
    print("ERROR: JSONデコードに失敗しました:", e)
    sys.exit(1)

if not data:
    print("ERROR: APIからデータが取得できませんでした")
    sys.exit(1)

# --- DataFrame作成 ---
df = pd.DataFrame(data)

# --- 平均値計算（D列2行目以降） ---
if len(df.columns) < 4:
    print("ERROR: D列が存在しません")
    sys.exit(1)

d_col_name = df.columns[3]
pm25_values = pd.to_numeric(df[d_col_name][1:], errors="coerce")
mean_pm25 = pm25_values.mean()

# --- CSV保存 ---
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"PM2.5_{year_name}_{month_name}月_{timestamp}.csv"

# F列が無い場合は新規追加
while len(df.columns) < 6:
    df[f'col{len(df.columns)+1}'] = ""

f_col_name = df.columns[5]

# 2行目が存在するか確認
if len(df) > 1:
    df.at[1, f_col_name] = mean_pm25
else:
    df.at[0, f_col_name] = mean_pm25

df.to_csv(filename, index=False)

print(f"CSV保存完了: {filename}")
print(f"PM2.5 平均値: {mean_pm25:.2f}")

# --- Teams通知 ---
message = {
    "text": f"最新のPM2.5平均値（{year_name}/{month_name}）: {mean_pm25:.2f}\nCSVファイル名: {filename}"
}

try:
    r = requests.post(webhook_url, json=message)
    print("Teams通知ステータス:", r.status_code)
except Exception as e:
    print("ERROR: Teams通知に失敗しました:", e)

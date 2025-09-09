import datetime
import requests
import pandas as pd
import os
import glob

# --- PM2.5 データ取得 ---
today = datetime.date.today()
first = today.replace(day=1)
last_month_last_day = first - datetime.timedelta(days=1)
year_name = last_month_last_day.strftime("%Y")
month_name = last_month_last_day.strftime("%m")

url = "https://soramame.env.go.jp/soramame/api/data_search"
params = {
    "Start_YM": f"{year_name}{month_name}",
    "End_YM": f"{year_name}{month_name}",
    "TDFKN_CD": "23",
    "SKT_CD": "23210040",
    "REQUEST_DATA": "PM2_5"
}

response = requests.get(url, params=params)
data = response.json()
df = pd.DataFrame(data)

# --- 平均値計算（D列2行目以降） ---
d_col_name = df.columns[3]
pm25_values = pd.to_numeric(df[d_col_name][1:], errors="coerce")
mean_pm25 = pm25_values.mean()

# --- CSV 保存（タイムスタンプ付き） ---
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
filename = f"PM2.5_{year_name}_{month_name}月_{timestamp}.csv"

# F列が無い場合は追加
while len(df.columns) < 6:
    df[f'col{len(df.columns)+1}'] = ""

# F列2行目に平均値
df.at[1, df.columns[5]] = mean_pm25

df.to_csv(filename, index=False, encoding="utf-8-sig")
print(f"保存完了: {filename}")
print(f"D列（{d_col_name}）のPM2.5平均値: {mean_pm25:.2f}")

# --- 古いCSV整理（容量対策：直近30ファイル以外削除） ---
csv_files = sorted(glob.glob("PM2.5_*.csv"))
max_files = 30
if len(csv_files) > max_files:
    for old_file in csv_files[:-max_files]:
        os.remove(old_file)
        print(f"古いCSV削除: {old_file}")

# --- Teams通知 ---
webhook_url = os.environ["TEAMS_WEBHOOK_URL"]
# 最新CSVのGitHub Rawリンク
repo = os.environ["GITHUB_REPOSITORY"]
branch = os.environ.get("GITHUB_REF", "main").split('/')[-1]
raw_url = f"https://github.com/{repo}/raw/{branch}/{filename}"

message = {
    "text": f"最新のPM2.5平均値（{year_name}/{month_name}）: {mean_pm25:.2f}\nCSVダウンロード: {raw_url}"
}

r = requests.post(webhook_url, json=message)
print("Teams通知ステータス:", r.status_code)

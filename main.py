import datetime
import requests
import pandas as pd
import os

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

df.at[1, df.columns[5]] = mean_pm25
df.to_csv(filename, index=False)

print(f"保存完了: {filename}")
print(f"D列（{d_col_name}）のPM2.5平均値: {mean_pm25:.2f}")

# --- Teams 通知 ---
webhook_url = os.environ["TEAMS_WEBHOOK"]
# GitHub Actions Artifact の URL は workflow の run ID と Artifact 名で作る
# ここでは簡易的にユーザーに手動でリンクを作る案内も含めます
artifact_link = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/suites/{os.environ['GITHUB_RUN_ID']}/artifacts"
message = {
    "text": f"最新のPM2.5平均値（{year_name}/{month_name}）: {mean_pm25:.2f}\nCSV ダウンロード: {artifact_link}"
}

r = requests.post(webhook_url, json=message)
print("Teams通知ステータス:", r.status_code)

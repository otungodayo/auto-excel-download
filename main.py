import pandas as pd

# データを作成
data = {"Message": ["Hello World"]}

# DataFrameに変換
df = pd.DataFrame(data)

# Excelファイルに出力
df.to_excel("output.xlsx", index=False)

print("Hello World を Excel に保存しました！")

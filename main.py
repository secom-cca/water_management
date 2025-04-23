import pysd
import matplotlib.pyplot as plt

# 1. モデルファイルの読み込み（ファイル名を適切に変更）
model = pysd.read_vensim("water_management.mdl")

# 2. 時間ステップを指定してシミュレーション実行
result = model.run(return_timestamps=range(0, 25))  # 0〜24か月

# 3. 可視化する変数を指定（列名はmdl内の変数と一致させる必要があります）
target_vars = [
    'Available groundwater',
    'Available Surface Water',
    'Deep groundwater',
    'Water Supply',
    'Net water demand',
    'Agricultural water use',
    'Domestic water use',
    'Industrial water use'
]

# 4. グラフ出力
plt.figure(figsize=(12, 8))
for var in target_vars:
    if var in result.columns:
        plt.plot(result.index, result[var], label=var)

plt.xlabel("Month")
plt.ylabel("Mm³ or unit")
plt.title("Water System Dynamics Simulation")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

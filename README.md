# 那須野が原を対象にした水収支のSystem Dynamics Model

## 1．概要

本モデルは，那須野が原地域の水循環および人間活動による水利用を，System Dynamics（SD）手法により3層ストック構造で表現した水収支モデルである．  
水資源を以下の3層で表現する．

- 表層水（Available Surface Water）
- 浅層地下水（Available groundwater）
- 深層地下水（Deep groundwater）

各層は，降水由来の流入（InflowおよびRunoff），層間移動（Percolation，Percolation to deep，Seepage，Seepage from deep），需要側の取水（農業・生活・産業のWithdrawal），地域外への流出（Surface water outflow，Groundwater outflow，Deep groundwater outflow），表層の蒸発散（Evapotranspiration）で収支が更新される．  
時間刻みは月単位（TIME STEP = 1 Month）である．

---

## 2．ストックと水収支式

### 2.1 表層水ストック

表層水ストックは次式で更新される．

\[
Available\ Surface\ Water(t+\Delta t)
=
Available\ Surface\ Water(t)
+
[Runoff+Seepage+Surface\ water\ inflow
-(Agricultural\ SW\ withdraw+Domestic\ SW\ withdraw+Industrial\ SW\ withdraw)
-Evapotranspiration-Percolation-Surface\ water\ outflow]\Delta t
\]

### 2.2 浅層地下水ストック

浅層地下水ストックは次式で更新される．

\[
Available\ groundwater(t+\Delta t)
=
Available\ groundwater(t)
+
[Groundwater\ inflow+Percolation+Seepage\ from\ deep
-Groundwater\ outflow-Percolation\ to\ deep-Seepage
-(Agricultural\ GW\ withdraw+Domestic\ GW\ withdraw+Industrial\ GW\ withdraw)]\Delta t
\]

### 2.3 深層地下水ストック

深層地下水ストックは次式で更新される．

\[
Deep\ groundwater(t+\Delta t)
=
Deep\ groundwater(t)
+
[Deep\ groundwater\ inflow+Percolation\ to\ deep-Deep\ groundwater\ outflow-Seepage\ from\ deep
-(Agricultural\ DW\ withdraw+Domestic\ DW\ withdraw+Industrial\ DW\ withdraw)]\Delta t
\]

### 2.4 層間移動の定義

本モデルで用いる層間移動は以下の通りである．

- **Percolation**：表層→浅層（Percolation ratio × Available Surface Water）．
- **Percolation to deep**：浅層→深層（Deep percolation ratio × Available groundwater）．
- **Seepage from deep**：深層→浅層（Seepage ratio from deep × Deep groundwater）．
- **Seepage**：浅層→表層（Seepage ratio × Available groundwater）．

---

## 3．需要・取水・使用・リターンフロー

需要（Demand）は，農業・生活・産業で別々に定義する．  
取水（Withdraw）は，各層ストックから需要を満たすために引き出す量であり，供給制約として `MIN(需要側配分，層の可用量)` を用いる．  
水使用（Use）とリターンフロー（Return flow）を導入し，取水後の一部が表層水・浅層地下水・深層地下水へ戻ると仮定する．

### 3.1 農業（Agricultural）

農業用水需要は，水田面積比率と月別灌漑深（LOOKUP）から計算する．

- Agricultural water demand = Area × Paddy field area ratio × Irrigation depth．

農業用水使用量は，表層・浅層・深層（DW）からの取水の合計である．

- Agricultural water use = Agricultural SW withdraw + Agricultural GW withdraw + Agricultural DW withdraw．

農業のリターンフローは，使用量にリターン比を掛けて表現する．

- Agricultural return flow = Agricultural return ratio × Agricultural water use．

リターンフローは，表層・浅層・深層へ配分される（SW/GW/DW return ratio）．

### 3.2 生活（Domestic）

生活用水需要は，人口と1人当たり需要に温度感度を掛けて表現する．

- Domestic water demand = Per capita domestic water demand × Population × (1 + 0.01 × (Temperature − 15))．

生活用水使用量は各層取水の合計である．

- Domestic water use = Domestic SW withdraw + Domestic GW withdraw + Domestic DW withdraw．

生活のリターンフローは，Domestic return ratio × Domestic water use で表現する．

### 3.3 産業（Industrial）

産業用水需要は，企業数（Company）と企業当たり需要で表現する．

- Industrial water demand = Company × Per capita industrial water demand．

産業用水使用量は各層取水の合計である．

- Industrial water use = Industrial SW withdraw + Industrial GW withdraw + Industrial DW withdraw．

産業のリターンフローは，Industrial return ratio × Industrial water use で表現する．

---

## 4．気象入力と蒸発散

降水量（Precipitation）と気温（Temperature）は，簡易的に，那須高原における平年値（1991-2020年）の月別LOOKUP（MODULO(Time,12)）で与える．  

表層からの蒸発散（Evapotranspiration）は，表層水ストックに比例し，気温に線形感度を持たせる．

- Evapotranspiration = Evap ratio × Available Surface Water × (1 + Temp sensitivity × (Temperature − 15))．

---

## 5．モデル運用上の注意点

1．**単位整合**：ストックは m3，フローは m3/Month を基本とする．  
2．**供給制約**：Withdrawal に `MIN(配分需要，ストック可用量)` を用いるため，ストックが小さいと需要未達が発生する．需要未達の扱い（未充足需要の記録，優先順位付け等）は別途拡張が必要である．  
3．**地域外流入・流出**：Groundwater inflow/outflow，Surface water outflow 等は「地域外との交換」を表す簡易項であり，必要に応じて境界条件として固定値化，あるいは観測データに基づき同定することが望ましい．  

---

## 6．変数一覧（定義・設定・根拠）

以下に，本モデルで定義された主要変数を一覧化する．  
根拠資料が本入力内に存在しない場合は，「本資料内に出典記載なし」と記載する．

> 注：ここでは主要変数に絞る．全変数についてはモデルファイル定義を参照すること．

| 変数 | 種別 | 定義／設定 | 単位 | 根拠 |
|---|---|---|---|---|
| Available groundwater | ストック | INTEG(… , Area × Shallow layer thickness × Porosity) | m3 | 本資料内に出典記載なし（仮定値）． |
| Available Surface Water | ストック | INTEG(… , Area × Initial SW depth) | m3 | 本資料内に出典記載なし（仮定値）． |
| Deep groundwater | ストック | INTEG(… , Area × Deep layer thickness × Deep porosity) | m3 | 本資料内に出典記載なし（仮定値）． |
| Population | ストック | INTEG(Population inflow − Population outflow, Initial population) | person | 本資料内に出典記載なし（要確認）． |
| Company | ストック | INTEG(Company inflow − Company outflow, Initial company) | （未設定） | 本資料内に出典記載なし（仮定値）． |
| Precipitation | 外生（LOOKUP） | 月別LOOKUP（1991–2020平年値想定） | mm/Month | 本資料内に出典記載なし（要確認）． |
| Temperature | 外生（LOOKUP） | 月別LOOKUP（1991–2020平年値想定） | degree | 本資料内に出典記載なし（要確認）． |
| Irrigation depth | 外生（LOOKUP） | 月別灌漑深LOOKUP | m/Month | 本資料内に出典記載なし（仮定値）． |
| Evap ratio | パラメータ | 0.03 | （未設定） | 本資料内に出典記載なし（仮定値）． |
| Temp sensitivity | パラメータ | 0.01 | （未設定） | 本資料内に出典記載なし（仮定値）． |
| Percolation ratio | パラメータ | 0.3 | [0,1,0.1] | 本資料内に出典記載なし（仮定値）． |
| Deep percolation ratio | パラメータ | 0.02 | m3/m3/Month [0,1,0.01] | 本資料内に出典記載なし（仮定値）． |
| Seepage ratio | パラメータ | 0.03 | [0,0.1,0.01] | 本資料内に出典記載なし（仮定値）． |
| Seepage ratio from deep | パラメータ | 0.01 | m3/m3/Month [0,0.1,0.01] | 本資料内に出典記載なし（仮定値）． |
| Groundwater outflow ratio | パラメータ | 0.01 | [0,1,0.01] | 本資料内に出典記載なし（仮定値）． |
| Outflow ratio | パラメータ | 0.4 | [0,1,0.1] | 本資料内に出典記載なし（仮定値）． |
| Paddy field area ratio | パラメータ | 0.4 | （未設定） | 本資料内に出典記載なし（仮定値）． |
| Per capita domestic water demand | パラメータ | 0.3 × 30 | m3/Month/person | 本資料内に出典記載なし（仮定値または統計に基づき要同定）． |
| Per capita industrial water demand | パラメータ | 0.022 × 1e+06 | m3/Month | 本資料内に出典記載なし（仮定値または統計に基づき要同定）． |

---

## 7．シミュレーション設定

- INITIAL TIME = 0（Month）
- FINAL TIME = 360（Month）
- TIME STEP = 1（Month）

---

## 8．拡張の方向性

- ETをFAO-56等の物理ベースに置換し，気温・放射・風速等を考慮する．  
- 地域外流入・流出（境界条件）を固定値から観測・推定に置換する．  
- 地下水位観測値によるパラメータ同定（Percolation ratio，Seepage ratio 等）を行う．  
- 需要未達を明示し，優先順位や価格反応等を導入する．  

## （参考）以下，SDEverywhereの説明

This is a template that is used by the `@sdeverywhere/create` package to generate a
new project that uses SDEverywhere.

The project includes:

- a build process that converts a Vensim model to a WebAssembly module that
  can run the model in any web browser or in a Node.js application
- a `config` directory that contains CSV files for configuring the generated
  model and application
- a "core" package that provides a clean JavaScript / TypeScript API around the
  WebAssembly model
- an "app" package containing a simple JavaScript / jQuery-based web application
  that can be used to exercise the model
- a local development mode (`npm run dev`) that allows for rapid prototyping
  of the model and app
- a "model-check" setup that allows for running checks and comparison tests using
  the generated model

## Quick Start

```sh
# Create a new project (you can also use yarn or pnpm here, if preferred).
# Be sure to choose the "Default" template.
npm create @sdeverywhere@latest

# Enter development mode for your model.  This will start a live
# development environment that will build a JavaScript version of the
# model and run checks on it any time you make changes to:
#   - the config files
#   - the Vensim model file (<name>.mdl)
#   - the model check definitions (model/checks/*.yaml)
#   - the model comparison definitions (model/comparisons/*.yaml)
npm run dev
```
## How to use python UI
In addition to directly use .mdl file from Vensim, we can run this file from python.
To run the simulation, first install the required libraries with 
```sh
pip install pysd
```
and run
```sh
python main.py
```

## License

SDEverywhere is distributed under the MIT license. See `LICENSE` for more details.

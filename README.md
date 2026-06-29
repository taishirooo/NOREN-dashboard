# NOREN 販売分析ダッシュボード

スマレジのPOSデータをGoogle Sheets経由で可視化するStreamlitアプリ。  
対象店舗: **NOREN 羽田店**（株式会社コラゾン 社内向け）

## 概要

| 項目 | 内容 |
|---|---|
| データソース | スマレジ エクスポートExcel → Google Sheets（月次） |
| デプロイ先 | Streamlit Cloud |
| 技術スタック | Python / Streamlit / Plotly / pandas / gspread / Google Drive API |

## ページ構成

| ページ | 概要 |
|---|---|
| P1 売上サマリ | 総売上・粗利・客数・客単価・粗利率のKPIと日別/曜日別/時間帯別グラフ |
| P2 インバウンド分析 | 国籍×購買のクロス分析。外国人比率・客単価・来店時間帯ヒートマップ |
| P3 商品・カテゴリ分析 | カテゴリ別/商品別の売上・粗利率・月次トレンド |

## セットアップ

### 依存インストール

```bash
uv sync
```

### Secrets 設定

`src/.streamlit/secrets.toml` を作成する（`src/.streamlit/example.secrets.toml` を参照）。

```toml
[gcp_service_account]
# GCPサービスアカウントJSONの各フィールド（Sheets API + Drive API 有効化済みのもの）

[sheets]
master_id       = "..."   # 客層マスタスプレッドシートID
master_gid      = "..."   # 客層マスタシートGID（数値）
sales_folder_id = "..."   # 売上データが格納されたGoogle DriveフォルダID
```

### ローカル起動

```bash
streamlit run src/home.py
```

## データフロー

```
スマレジ Excel
  → Google Drive フォルダ内の月次Google Sheets
  → Drive API（ファイル一覧取得）+ gspread（各ファイル読み込み）→ 縦結合
  → loader.py → orders_df / items_df
  → 各ページ (charts.py / metrics.py)
```

月次で新ファイルをフォルダに追加するだけで自動反映される。

## ディレクトリ構成

```
NOREN-dash-board/
├── src/
│   ├── home.py                      # エントリポイント・ルーティング
│   ├── .streamlit/
│   │   ├── config.toml
│   │   └── secrets.toml             # Git管理外
│   ├── common/
│   │   ├── loader.py                # Google Sheets 読み込み・前処理
│   │   ├── charts.py                # Plotlyグラフ定義
│   │   ├── metrics.py               # KPI計算関数
│   │   └── constants.py             # 定数（シート名・除外商品リスト等）
│   └── apps/
│       ├── sales_summary/main.py    # P1: 売上サマリ
│       ├── inbound_analysis/main.py # P2: インバウンド分析
│       └── product_analysis/main.py # P3: 商品・カテゴリ分析
└── docs/
    └── 要件定義/
        └── NOREN_dashboard_requirements.md
```

## Streamlit Cloud へのデプロイ

1. このリポジトリを GitHub に push
2. [Streamlit Cloud](https://streamlit.io/cloud) でアプリを作成し、`src/home.py` をエントリポイントに指定
3. Secrets に `secrets.toml` の内容を設定

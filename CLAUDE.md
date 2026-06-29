# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NOREN 販売分析ダッシュボード — スマレジのPOSデータをGoogle Sheets経由で可視化するStreamlitアプリ。
対象: NOREN 羽田店（コラゾン社内向け）。Streamlit Cloud でホスト。

## ドキュメント更新ルール

`src/apps/` または `src/common/` 配下のファイルを編集したとき、**必ず以下の2ファイルも実装内容に合わせて更新すること**:

1. `docs/要件定義/NOREN_dashboard_requirements.md` — ページ構成・KPIカード数・グラフ一覧・データ設計
2. `CLAUDE.md`（本ファイル）— アーキテクチャ概要・ページ構成表・Secrets設定・データ品質メモ

更新が必要になる代表的な変更:
- KPIカードの追加・削除・定義変更
- グラフ・タブの追加・削除・名称変更
- `load_data()` の戻り値・前処理ロジックの変更
- Secrets キー名の変更
- `constants.py` の定数追加（EXCLUDED_ITEMS等）

## Commands

```bash
# 依存インストール（uv）
uv sync

# ローカル起動
streamlit run src/home.py

# 構文チェック
uv run python -m py_compile src/home.py src/common/loader.py
```

## Architecture

### データフロー
```
スマレジ Excel → Google Drive フォルダ内の月次Google Sheets
    → Drive API（ファイル一覧取得）+ gspread（各ファイル読み込み）→ 縦結合
    → loader.py → orders_df / items_df
    → 各ページ (charts.py / metrics.py)
```

### ディレクトリ構成
```
NOREN-dash-board/
├── docs/
│   └── 要件定義/
│       └── NOREN_dashboard_requirements.md  # 詳細要件・データ設計
├── src/
│   ├── home.py                    # エントリポイント・st.navigation() でルーティング
│   ├── .streamlit/
│   │   ├── config.toml
│   │   └── secrets.toml           # Git管理外（example.secrets.toml を参照）
│   ├── common/
│   │   ├── loader.py              # Google Sheets 読み込み・前処理・@st.cache_data
│   │   ├── charts.py              # 全Plotlyグラフ定義（関数単位）
│   │   ├── metrics.py             # KPI計算関数
│   │   └── constants.py           # シート名・カラム名・除外商品リスト等の定数
│   └── apps/
│       ├── sales_summary/main.py   # P1: 売上サマリ（経営ダッシュボード）
│       ├── inbound_analysis/main.py # P2: インバウンド分析（国籍×購買）
│       └── product_analysis/main.py # P3: 商品・カテゴリ分析
```

### 重要な設計ポイント

**loader.py** は5値タプルを返す `(orders_df, items_df, nat_master, gender_master, age_master)`:
- `orders_df` — `drop_duplicates("order_id")` で注文単位（P1・P2のKPIに使用）
- `items_df` — 全行（商品明細単位、P2ヒートマップ・P3に使用）
- `nat_master` / `gender_master` / `age_master` — 客層マスタ辞書

**データ取得**: Drive API でフォルダ内の全Google Sheetsを自動取得して縦結合。月次で新ファイルをフォルダに追加するだけで自動反映される。

**フィルタ**: グローバルフィルタなし。各ページ内の `st.selectbox` で開始・終了年月を選択し、全グラフ・KPIに連動。外国人比率トレンドのみ全期間表示（月フィルタ非適用）。

**キャッシュ**: `@st.cache_data(ttl=3600)` を `load_data()` に付与。手動更新は「データを再読み込み」ボタン（`st.cache_data.clear()`）。

### Secrets 設定（`src/.streamlit/secrets.toml`）

```toml
[gcp_service_account]
# GCPサービスアカウントJSONの各フィールド（Sheets API + Drive API 両方を有効化）

[sheets]
master_id       = "..."   # 客層マスタスプレッドシートID
master_gid      = "..."   # 客層マスタシートGID（数値）
sales_folder_id = "..."   # 売上データが格納されたGoogle DriveフォルダID
```

### ページ構成

| ページ | KPIカード | 主なグラフ |
|---|---|---|
| P1 売上サマリ | 総売上・粗利額・総客数・客単価・粗利率（5枚、単月時は前月比付き） | 日別売上推移、曜日別、時間帯別、ヒートマップ、粗利率推移、現金/カード |
| P2 インバウンド分析 | 外国人比率・外国人客単価・日本人客単価・来客上位国籍（4枚、単月時は前月比付き） | 国籍別来客数/客単価、来店時間帯ヒートマップ、性別×年代、カテゴリ×国籍、国籍別詳細 |
| P3 商品・カテゴリ分析 | 売上1位カテゴリ・粗利率最高カテゴリ・販売数1位商品・総取扱商品数（4枚） | カテゴリ別売上/商品別売上・販売数、売上×粗利率バブル、カテゴリ別粗利率、月次トレンド |

### 既知のデータ品質

- `age_group` 全件NULL → `customer3`（age_gen）を代わりに使用
- `customer4`, `customer5`, `member_id` は未使用
- Sheets経由で数値が文字列になる → loader.py で `pd.to_numeric(errors="coerce")` 適用済み
- 商品名のUnicode揺れ → `unicodedata.normalize("NFKC")` 適用済み
- 送料等のノイズ商品 → `EXCLUDED_ITEMS`（constants.py）で定義・ランキングから除外

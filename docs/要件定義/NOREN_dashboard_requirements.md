# NOREN ダッシュボード 要件定義 & データ設計書

最終更新: 2026-06-29

## 1. プロジェクト概要

| 項目 | 内容 |
|---|---|
| プロダクト名 | NOREN 販売分析ダッシュボード |
| 対象店舗 | NOREN 羽田店（株式会社コラゾン） |
| 主な閲覧者 | コラゾン社内（店長・オーナー） |
| 目的 | POSデータを可視化し、経営判断・インバウンド戦略・在庫仕入れに活用 |
| データソース | スマレジ エクスポートExcel → Google Sheets（月次手動貼り付け） |
| デプロイ先 | Streamlit Cloud（URL共有） |
| 技術スタック | Python / Streamlit / Plotly / pandas / gspread / Google Drive API |

---

## 2. ページ構成

### P1 売上サマリ（経営ダッシュボード）
店長が毎日確認するKPIページ。

**目的:** 月次・日次の売上・客数・客単価・粗利を即座に把握する

**KPIカード（5枚）**

| カード | 指標 | 計算式 |
|---|---|---|
| 総売上 | 合計売上金額 | `SUM(total)` |
| 粗利額 | 合計粗利金額 | `SUM(total - cost_subtotal)` |
| 総客数 | ユニーク注文件数 | `COUNT(DISTINCT order_id)` |
| 客単価 | 平均1注文あたり売上 | `total / orders` |
| 粗利率 | 売上に対する粗利の割合 | `gross_profit / total` |

※ 単月選択時は前月比（±差分）を併記

**グラフ一覧**

タブ「📈 売上推移」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 日別売上推移 | 折れ線 | 平均ラインあり |
| 曜日別売上・客数 | 棒グラフ＋折れ線（2軸） | 月〜日順 |

タブ「⏰ 時間帯・曜日分析」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 時間帯別売上・客数 | 棒グラフ＋折れ線（2軸） | - |
| 時間帯×曜日 客数ヒートマップ | ヒートマップ | - |

タブ「📉 粗利・支払い」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 月別粗利率推移 | 折れ線 | 2ヶ月以上選択時のみ表示 |
| 現金/カード比率 | ドーナツ | - |

**フィルタ:** ページ内で開始・終了年月を選択（全グラフ・KPIに連動）

---

### P2 インバウンド分析（客層ダッシュボード）
NORENの差別化軸。国籍×購買商品のクロス分析が最重要。

**目的:** どの国籍の客が何を買っているかを把握し、陳列・仕入れ・LIBEA Navi推薦に活用する

**KPIカード（4枚）**

| カード | 指標 | 計算式 |
|---|---|---|
| 外国人比率 | 外国人来客の割合 | `customer1 != 1` の件数 / 全件 |
| 外国人客単価 | 外国人の平均購入額 | - |
| 日本人客単価 | 日本人の平均購入額 | - |
| 来客上位国籍 | 期間中で来客数が最多の国籍名 | - |

※ 単月選択時は外国人比率・客単価で前月比を併記

**グラフ一覧**

タブ「🌍 国籍別分析」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 国籍別来客数 | 横棒グラフ | TOP15 |
| 国籍別客単価 | 横棒グラフ | TOP15、件数N付き |
| 外国人比率 月次推移 | 棒グラフ | 全期間表示（月フィルタ非適用） |

タブ「🕐 来店時間帯」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 国籍×時間帯 来客数 | ヒートマップ | TOP10国籍 |

タブ「👥 デモグラフィック」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 性別×年代 ヒートマップ | ヒートマップ | セル=件数 |

タブ「🛒 カテゴリ×国籍」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| カテゴリ×国籍 積み上げ棒グラフ | 横積み上げ棒 | 売上金額ベース |

タブ「🔍 国籍別詳細」
- セレクトボックスで国籍を選択
- KPI: 来客数、客単価、人気カテゴリ、人気商品
- グラフ: カテゴリ別売上TOP・商品別売上TOP・商品別販売数TOP・カテゴリ月次トレンド

**フィルタ:** ページ内で開始・終了年月を選択（全グラフ・KPIに連動）

---

### P3 商品・カテゴリ分析
仕入れ・陳列戦略に直結する商品軸の分析。

**目的:** 何が売れていて、何が粗利に貢献しているかを把握する

**KPIカード（4枚）**

| カード | 指標 |
|---|---|
| 売上1位カテゴリ | 期間内で売上金額が最も高いカテゴリ名 |
| 粗利率最高カテゴリ | 期間内で粗利率が最も高いカテゴリ名 |
| 販売数1位商品 | 期間内で販売個数が最も多い商品名（EXCLUDED_ITEMS除外） |
| 総取扱商品数 | 期間内に販売されたユニーク商品数 |

**グラフ一覧**

タブ「💰 売上ランキング」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| カテゴリ別売上ランキング | 横棒グラフ | TOP15 |
| 商品別売上金額 | 横棒グラフ | TOP20 |

タブ「📦 商品ランキング」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 商品別販売数 | 横棒グラフ | TOP20 |

タブ「💹 収益分析」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| 売上×粗利率 バブルチャート | 散布図 | バブルサイズ=販売数量、x軸ログスケール、象限カラー分け（中央値基準） |
| カテゴリ別粗利率比較 | 横棒グラフ | (revenue - cost) / revenue |

タブ「📈 カテゴリトレンド」
| グラフ名 | 種類 | 備考 |
|---|---|---|
| カテゴリ別月次売上推移 | 折れ線 | 2ヶ月以上選択時のみ表示 |

**フィルタ:** ページ内で開始・終了年月を選択（全グラフ・KPIに連動）

---

## 3. データ設計

### 3-1. Google Sheets 構成

**売上データ: フォルダ方式（月次ファイル分割）**

| 構成要素 | 内容 |
|---|---|
| 売上フォルダ | Google Drive上の指定フォルダ（`sales_folder_id`で指定） |
| 月次ファイル | フォルダ内のGoogle Sheetsを全件自動取得・縦結合（Drive API使用） |
| 客層マスタ | 別スプレッドシート（`master_id` / `master_gid`で指定） |

**月次更新手順**
1. スマレジ管理画面からExcelをエクスポート
2. Excelを開いてシート1の中身を全選択コピー（ヘッダ含む）
3. 当月分の新規Google Sheetsを売上フォルダに作成して貼り付け
4. ダッシュボードで「データを再読み込み」ボタンを押す

### 3-2. データ加工（前処理）仕様

```
【ステップ1】Google Sheets 読み込み（loader.py）
- Drive API でフォルダ内の全Sheetsファイル一覧を取得
- 各ファイルの先頭シートを get_all_records() で DataFrame 化 → pd.concat で縦結合
- 客層マスタ（master_id / master_gid）を別途読み込み

【ステップ2】クリーニング
- cancel_div == 0 でフィルタ（有効注文のみ）
- order_datetime, order_date を datetime 型に変換
- NUMERIC_COLS（constants.py で定義）を pd.to_numeric(errors="coerce") で変換
- department_name, item_name を unicodedata.normalize("NFKC") で正規化

【ステップ3】注文ヘッダテーブル生成（orders_df）
- drop_duplicates('order_id') で1注文1行に
- 派生カラム:
    hour         = order_datetime.dt.hour
    weekday      = order_datetime.dt.weekday
    weekday_name = {0:月, 1:火, ... 6:日}
    month        = order_date.dt.month
    year_month   = order_date.dt.to_period("M")
    gross_profit = total - cost_subtotal
    gp_rate      = gross_profit / total
    is_foreign   = (customer1 != 1).astype(int)
    nationality  = customer1.map(nat_master)
    gender       = customer2.map(gender_master)
    age_gen      = customer3.map(age_master)

【ステップ4】商品明細テーブル（items_df）
- drop_duplicates なし（1行=1商品のまま）
- 派生カラム:
    month        = order_date.dt.month
    year_month   = order_date.dt.to_period("M")
    gp_item      = after_discount_total - cost_total
    nationality  = customer1.map(nat_master)

【ステップ5】マスタ dict 生成（戻り値として返す）
- nat_master    = {客層ID: 客層名}  # 国籍
- gender_master = {客層ID: 客層名}  # 性別
- age_master    = {客層ID: 客層名}  # 年代
```

戻り値: `(orders_df, items_df, nat_master, gender_master, age_master)`

### 3-3. 想定データ量

| 項目 | 実測値（2ヶ月分） | 年間推計 |
|---|---|---|
| 行数（item行） | 約15,000行 | 約90,000行 |
| 注文数 | 約6,700件 | 約40,000件 |
| ユニーク商品 | 932点 | 同程度 |
| ユニーク国籍 | 36カ国 | 同程度 |

---

## 4. 技術仕様

### ディレクトリ構成

```
NOREN-dash-board/
├── docs/
│   └── 要件定義/
│       └── NOREN_dashboard_requirements.md
├── src/
│   ├── .streamlit/
│   │   ├── config.toml
│   │   ├── secrets.toml          # Git管理外（example.secrets.toml を参照）
│   │   └── example.secrets.toml
│   ├── apps/
│   │   ├── sales_summary/        # P1 売上サマリ
│   │   │   └── main.py
│   │   ├── inbound_analysis/     # P2 インバウンド分析
│   │   │   └── main.py
│   │   └── product_analysis/     # P3 商品・カテゴリ分析
│   │       └── main.py
│   ├── common/
│   │   ├── loader.py             # Google Sheets読み込み・前処理・@st.cache_data
│   │   ├── charts.py             # 全Plotlyグラフ定義（関数単位）
│   │   ├── metrics.py            # KPI計算関数
│   │   └── constants.py          # 定数（シート名・カラム名・除外商品リスト等）
│   └── home.py                   # エントリポイント・st.navigation() でルーティング
├── pyproject.toml                # uv管理
└── uv.lock
```

### 主要パッケージ

```toml
dependencies = [
    "streamlit",
    "pandas",
    "plotly",
    "gspread",
    "google-auth",
    "google-api-python-client",   # Drive API（フォルダ内ファイル一覧取得）
]
```

### Secrets 設定（`src/.streamlit/secrets.toml`）

```toml
[gcp_service_account]
# GCPサービスアカウントJSONの各フィールド（type, project_id, private_key, ...）

[sheets]
master_id        = "..."   # 客層マスタスプレッドシートID
master_gid       = "..."   # 客層マスタシートGID（数値）
sales_folder_id  = "..."   # 売上データが格納されたGoogle DriveフォルダID
```

### フィルタ設計

- **グローバルフィルタなし**（サイドバーは「データを再読み込み」ボタンのみ）
- **ページ内フィルタ**: 各ページで開始・終了年月を `st.selectbox` で選択
- **例外**: 外国人比率トレンドは全期間表示（月フィルタ非適用）

### キャッシュ戦略

- `@st.cache_data(ttl=3600)` を `load_data()` に付与
- Google Sheets/Drive APIへのリクエストは1時間に1回のみ
- 手動更新: `st.cache_data.clear()` → サイドバーの「データを再読み込み」ボタン

### バブルチャートの視認性対応（2026-06-29 更新）

売上×粗利率バブルチャートの改善点:
- **x軸ログスケール** (`log_x=True`) — 外れ値（Tシャツ等）による軸の引き伸ばしを解消
- **ラベル削除 → ホバー表示** — カテゴリ名の重なりを解消
- **象限カラー分け** — 売上・粗利率それぞれの中央値を境に4色で分類
  - 緑: 高売上×高粗利（優先注力）
  - オレンジ: 高売上×低粗利（要改善）
  - 青: 低売上×高粗利（伸びしろ）
  - グレー: 低売上×低粗利（要見直し）

---

## 5. 既知データ品質メモ

| 項目 | 状況 | 対処 |
|---|---|---|
| `age_group` | 全件NULL | 使用しない（customer3/age_gen を代わりに使用） |
| `customer4`, `customer5` | 全件NULL | 使用しない |
| `member_id` | 99.9% NULL | 会員分析は対象外 |
| `point1`〜`point4` | 全件0 | ポイント分析は対象外 |
| `unitprice_cost` | 一部NULL | `pd.to_numeric(errors="coerce")` で対処 |
| Sheets経由の型変換 | 数値が文字列になりうる | loader.py で `pd.to_numeric` を明示的に適用 |
| 商品名の文字コード揺れ | Unicode正規化が必要 | `unicodedata.normalize("NFKC")` を適用 |
| 除外商品 | ランキングに不適切な商品（送料等） | `EXCLUDED_ITEMS`（constants.py）で定義・フィルタ |

---

## 6. セットアップ手順（初回）

```bash
# 1. 依存インストール
uv sync

# 2. GCPサービスアカウント作成
#    → Google Cloud Console でサービスアカウントを作成
#    → Sheets API と Drive API を有効化
#    → JSONキーをダウンロード → secrets.toml に貼り付け

# 3. Google Drive / Sheets 共有設定
#    → サービスアカウントのメールアドレスを売上フォルダ・マスタSheetに「閲覧者」として追加

# 4. ローカル起動
streamlit run src/home.py
```

---

## 7. 実装スコープ（フェーズ別）

| フェーズ | 内容 | ステータス |
|---|---|---|
| Phase 1 | P1〜P3実装 / Google Sheets手動更新 / Streamlit Cloud公開 | **完了** |
| Phase 2 | スマレジAPI連携 → Sheets自動書き込みスクリプト | 未着手（API接続交渉後） |
| Phase 3 | LIBEA Navi連携パネル追加 | 未着手（NOREN導入後） |

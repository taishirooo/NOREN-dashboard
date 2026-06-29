import streamlit as st

from common import charts
from common.loader import load_data

orders_df, items_df, _, _, _ = load_data()

if st.sidebar.button("データを再読み込み"):
    st.cache_data.clear()
    st.rerun()

st.title("🛍️ 商品・カテゴリ分析")

with st.expander("📌 このダッシュボードの用途"):
    st.markdown("カテゴリ・商品ごとの売上・粗利率・販売数量を分析します。仕入れ優先度の判断・陳列戦略への活用を目的とします。")

with st.expander("📋 指標定義（クリックで展開）"):
    st.markdown("""
| 指標 | 定義 |
|------|------|
| 売上1位カテゴリ | 期間内で売上金額が最も高いカテゴリ |
| 粗利率最高カテゴリ | 期間内で粗利率が最も高いカテゴリ |
| 販売数1位商品 | 期間内で販売個数が最も多い商品 |
| 総取扱商品数 | 期間内に販売された商品のユニーク数 |
""")

def _fmt_ym(ym):
    return f"{ym.year}年{ym.month}月"

with st.container(border=True):
    st.markdown("**フィルタ**")
    st.caption("選択した期間のデータを全グラフ・指標に適用します。")
    year_months = sorted(orders_df["year_month"].dropna().unique())
    col1, col2 = st.columns(2)
    with col1:
        start_ym = st.selectbox("開始年月", year_months, format_func=_fmt_ym, index=0)
    with col2:
        end_ym = st.selectbox("終了年月", year_months, format_func=_fmt_ym, index=len(year_months) - 1)

if start_ym > end_ym:
    st.warning("開始年月が終了年月より後になっています。")
    st.stop()

df_items = items_df[(items_df["year_month"] >= start_ym) & (items_df["year_month"] <= end_ym)]

if len(df_items) > 0:
    _dept_mask = df_items["department_name"].notna() & (df_items["department_name"].str.strip() != "")
    _df_dept = df_items[_dept_mask]
    top_category = _df_dept.groupby("department_name")["after_discount_total"].sum().idxmax() if len(_df_dept) > 0 else "-"
    gp_agg = _df_dept.groupby("department_name").agg(
        revenue=("after_discount_total", "sum"),
        cost=("cost_total", "sum"),
    )
    gp_agg["gp_rate"] = (gp_agg["revenue"] - gp_agg["cost"]) / gp_agg["revenue"].replace(0, float("nan"))
    _valid_gp = gp_agg["gp_rate"].dropna()
    top_gp_category = str(_valid_gp.idxmax()) if len(_valid_gp) > 0 else "-"
    from common.constants import EXCLUDED_ITEMS
    top_item = (
        df_items[~df_items["item_name"].isin(EXCLUDED_ITEMS)]
        .groupby("item_name")["item_number"].sum().idxmax()
    )
else:
    top_category = "-"
    top_gp_category = "-"
    top_item = "-"

unique_items = df_items[~df_items["item_name"].isin(EXCLUDED_ITEMS)]["item_name"].nunique()

c1, c2, c3, c4 = st.columns(4)
c1.metric("売上1位カテゴリ",    top_category,         help="オリジナル紙袋など袋類を除いたカテゴリ別売上 1位")
c2.metric("粗利率最高カテゴリ", str(top_gp_category), help="オリジナル紙袋など袋類を除いたカテゴリ別粗利率 1位")
c3.metric("販売数1位商品",      top_item,             help="オリジナル紙袋など袋類を除いた販売数 1位")
c4.metric("総取扱商品数",       f"{unique_items:,} 点", help="オリジナル紙袋など袋類を除いたユニーク商品数")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 売上ランキング", "📦 商品ランキング", "💹 収益分析", "📈 カテゴリトレンド", "📊 ABC分析"])

with tab1:
    st.plotly_chart(charts.category_sales_bar(df_items), use_container_width=True)
    st.plotly_chart(charts.item_revenue_bar(df_items), use_container_width=True)

with tab2:
    st.plotly_chart(charts.item_sales_bar(df_items), use_container_width=True)

with tab3:
    st.plotly_chart(charts.sales_gp_bubble(df_items), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.category_gp_amount_bar(df_items), use_container_width=True)
    with col2:
        st.plotly_chart(charts.item_gp_amount_bar(df_items), use_container_width=True)
    st.plotly_chart(charts.category_gp_bar(df_items), use_container_width=True)

with tab4:
    if df_items["year_month"].nunique() < 2:
        st.info("カテゴリトレンドは2ヶ月以上の期間を選択すると表示されます。")
    else:
        st.plotly_chart(charts.category_monthly_trend(df_items), use_container_width=True)

with tab5:
    st.caption("売上上位80%を占める商品・カテゴリ（Aクラス）が仕入れ・陳列の最優先対象です。")
    st.plotly_chart(charts.abc_category_bar(df_items), use_container_width=True)
    st.plotly_chart(charts.abc_item_bar(df_items), use_container_width=True)

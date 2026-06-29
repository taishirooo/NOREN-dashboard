import pandas as pd
import streamlit as st

from common import charts, metrics
from common.constants import EXCLUDED_ITEMS
from common.loader import load_data

orders_df, items_df, _, _, _ = load_data()

if st.sidebar.button("データを再読み込み"):
    st.cache_data.clear()
    st.rerun()

st.title("🌏 インバウンド分析")

with st.expander("📌 このダッシュボードの用途"):
    st.markdown("外国人・日本人の来客比率、国籍別の客単価・購買カテゴリ・来店時間帯を分析します。陳列・仕入れ・LIBEA Navi推薦への活用を目的とします。")

with st.expander("📋 指標定義（クリックで展開）"):
    st.markdown("""
| 指標 | 定義 |
|------|------|
| 外国人比率 | 外国人注文数 ÷ 全注文数（customer1 ≠ 1） |
| 外国人客単価 | 外国人注文の平均売上金額 |
| 日本人客単価 | 日本人注文の平均売上金額 |
| 上位国籍 | 期間中で来客数が最も多い国籍 |
""")

def _fmt_ym(ym):
    return f"{ym.year}年{ym.month}月"

with st.container(border=True):
    st.markdown("**フィルタ**")
    st.caption("選択した期間のデータを全グラフ・指標に適用します。単月選択時は前月比を表示します。")
    year_months = sorted(orders_df["year_month"].dropna().unique())
    col1, col2 = st.columns(2)
    with col1:
        start_ym = st.selectbox("開始年月", year_months, format_func=_fmt_ym, index=0)
    with col2:
        end_ym = st.selectbox("終了年月", year_months, format_func=_fmt_ym, index=len(year_months) - 1)

if start_ym > end_ym:
    st.warning("開始年月が終了年月より後になっています。")
    st.stop()

df_orders = orders_df[(orders_df["year_month"] >= start_ym) & (orders_df["year_month"] <= end_ym)]
df_items  = items_df[(items_df["year_month"] >= start_ym) & (items_df["year_month"] <= end_ym)]

# 前月比（単月選択時のみ）
prev_orders = pd.DataFrame()
if start_ym == end_ym:
    prev_ym = start_ym - 1
    mask = orders_df["year_month"] == prev_ym
    if mask.any():
        prev_orders = orders_df[mask]

def _pct_delta(curr, prev):
    return f"{curr - prev:+.1%}" if not prev_orders.empty else None

def _yen_delta(curr, prev):
    return f"¥{curr - prev:+,.0f}" if not prev_orders.empty else None

foreign_ratio   = metrics.foreign_ratio(df_orders)
ticket_foreign  = metrics.avg_ticket_by_foreign(df_orders, is_foreign=True)
ticket_domestic = metrics.avg_ticket_by_foreign(df_orders, is_foreign=False)
top_nat = df_orders["nationality"].value_counts().index[0] if len(df_orders) > 0 else "-"

p_foreign_ratio  = metrics.foreign_ratio(prev_orders)                          if not prev_orders.empty else 0
p_ticket_foreign = metrics.avg_ticket_by_foreign(prev_orders, is_foreign=True)  if not prev_orders.empty else 0
p_ticket_domestic= metrics.avg_ticket_by_foreign(prev_orders, is_foreign=False) if not prev_orders.empty else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("外国人比率",   f"{foreign_ratio:.1%}",  delta=_pct_delta(foreign_ratio,   p_foreign_ratio))
c2.metric("外国人客単価", f"¥{ticket_foreign:,.0f}", delta=_yen_delta(ticket_foreign,  p_ticket_foreign))
c3.metric("日本人客単価", f"¥{ticket_domestic:,.0f}",delta=_yen_delta(ticket_domestic, p_ticket_domestic))
c4.metric("来客上位国籍", top_nat)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌍 国籍別分析", "🕐 来店時間帯", "👥 デモグラフィック",
    "🛒 カテゴリ×国籍", "🔍 国籍別詳細", "🧺 まとめ買い分析",
])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(charts.nationality_count_bar(df_orders), use_container_width=True)
    with col2:
        st.plotly_chart(charts.nationality_ticket_bar(df_orders), use_container_width=True)
    st.plotly_chart(charts.foreign_ratio_monthly(df_orders), use_container_width=True)

with tab2:
    st.plotly_chart(charts.nationality_hour_heatmap(df_orders), use_container_width=True)

with tab3:
    st.plotly_chart(charts.gender_age_heatmap(df_orders), use_container_width=True)

with tab4:
    st.plotly_chart(charts.category_nationality_stacked(df_items), use_container_width=True)

with tab5:
    available_nats = df_items["nationality"].dropna().value_counts().index.tolist()
    if not available_nats:
        st.info("表示できる国籍データがありません。")
    else:
        selected_nat = st.selectbox("国籍を選択", available_nats, key="nat_detail")

        nat_orders = df_orders[df_orders["nationality"] == selected_nat]
        nat_items  = df_items[df_items["nationality"] == selected_nat]

        nat_count     = len(nat_orders)
        nat_ticket    = float(nat_orders["total"].mean()) if nat_count > 0 else 0
        _nat_dept = nat_items[
            ~nat_items["item_name"].isin(EXCLUDED_ITEMS) &
            nat_items["department_name"].notna() &
            (nat_items["department_name"].str.strip() != "")
        ]
        nat_top_cat   = _nat_dept.groupby("department_name")["after_discount_total"].sum().idxmax() if len(_nat_dept) > 0 else "-"
        from common.constants import EXCLUDED_ITEMS
        _nat_items_filtered = nat_items[~nat_items["item_name"].isin(EXCLUDED_ITEMS)]
        nat_top_item  = _nat_items_filtered.groupby("item_name")["item_number"].sum().idxmax() if len(_nat_items_filtered) > 0 else "-"

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("来客数",       f"{nat_count:,} 件")
        k2.metric("客単価",       f"¥{nat_ticket:,.0f}")
        k3.metric("人気カテゴリ", nat_top_cat,  help="オリジナル紙袋など袋類を除いたカテゴリ別売上 1位")
        k4.metric("人気商品",     nat_top_item, help="オリジナル紙袋など袋類を除いた販売数 1位")

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(charts.nationality_top_categories(nat_items, selected_nat), use_container_width=True)
        with col2:
            st.plotly_chart(charts.nationality_top_items(nat_items, selected_nat), use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            st.plotly_chart(charts.nationality_top_items_count(nat_items, selected_nat), use_container_width=True)
        with col4:
            if df_items["year_month"].nunique() < 2:
                st.info("トレンドは2ヶ月以上の期間を選択すると表示されます。")
            else:
                st.plotly_chart(charts.nationality_category_monthly(df_items, selected_nat), use_container_width=True)

with tab6:
    st.caption("購買点数が増えるほど客単価が上がるか、どの国籍がまとめ買いしやすいか、どのカテゴリが一緒に買われているかを確認できます。")

    st.plotly_chart(charts.basket_size_by_nationality(df_orders, df_items), use_container_width=True)

    st.divider()

    available_nats_basket = df_orders["nationality"].dropna().value_counts().index.tolist()
    selected_nat_basket = st.selectbox(
        "国籍で絞り込む（全体 or 国籍を選択）",
        ["全体"] + available_nats_basket,
        key="basket_nat",
    )

    if selected_nat_basket == "全体":
        _b_orders = df_orders
        _b_items  = df_items
    else:
        _b_orders = df_orders[df_orders["nationality"] == selected_nat_basket]
        _b_items  = df_items[df_items["nationality"] == selected_nat_basket]

    if len(_b_orders) == 0:
        st.info("選択した国籍のデータがありません。")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(charts.basket_size_dist(_b_items, _b_orders), use_container_width=True)
        with col2:
            st.plotly_chart(charts.basket_size_vs_ticket(_b_items, _b_orders), use_container_width=True)
        st.plotly_chart(charts.category_cooccurrence_heatmap(_b_items), use_container_width=True)

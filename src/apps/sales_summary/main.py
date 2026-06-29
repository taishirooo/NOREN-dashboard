import pandas as pd
import streamlit as st

from common import charts, metrics
from common.loader import load_data

orders_df, items_df, _, _, _ = load_data()

if st.sidebar.button("データを再読み込み"):
    st.cache_data.clear()
    st.rerun()

st.title("📊 売上サマリ")

with st.expander("📌 このダッシュボードの用途"):
    st.markdown("月次・日次の売上・客数・客単価・粗利を把握するための経営ダッシュボードです。フィルタで期間を絞り込むと各指標・グラフが連動して更新されます。")

with st.expander("📋 指標定義（クリックで展開）"):
    st.markdown("""
| 指標 | 定義 |
|------|------|
| 総売上 | キャンセル除外後の合計売上金額 |
| 粗利額 | 総売上 − 原価合計 |
| 総客数 | ユニーク注文数 |
| 客単価 | 総売上 ÷ 総客数 |
| 粗利率 | 粗利額 ÷ 総売上 |
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

df = orders_df[(orders_df["year_month"] >= start_ym) & (orders_df["year_month"] <= end_ym)]

# 前月比（単月選択時のみ計算）
prev_df = pd.DataFrame()
if start_ym == end_ym:
    prev_ym = start_ym - 1
    mask = orders_df["year_month"] == prev_ym
    if mask.any():
        prev_df = orders_df[mask]

def _yen_delta(curr, prev):
    return f"¥{curr - prev:+,.0f}" if not prev_df.empty else None

def _pct_delta(curr, prev):
    return f"{curr - prev:+.1%}" if not prev_df.empty else None

def _cnt_delta(curr, prev):
    return f"{curr - prev:+,} 件" if not prev_df.empty else None

sales   = metrics.total_sales(df)
gp      = metrics.gross_profit(df)
orders  = metrics.total_orders(df)
ticket  = metrics.avg_ticket(df)
gp_rate = metrics.gross_profit_rate(df)

p_sales   = metrics.total_sales(prev_df)       if not prev_df.empty else 0
p_gp      = metrics.gross_profit(prev_df)      if not prev_df.empty else 0
p_orders  = metrics.total_orders(prev_df)      if not prev_df.empty else 0
p_ticket  = metrics.avg_ticket(prev_df)        if not prev_df.empty else 0
p_gp_rate = metrics.gross_profit_rate(prev_df) if not prev_df.empty else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("総売上",  f"¥{sales:,.0f}",  delta=_yen_delta(sales, p_sales))
c2.metric("粗利額",  f"¥{gp:,.0f}",    delta=_yen_delta(gp, p_gp))
c3.metric("総客数",  f"{orders:,} 件",  delta=_cnt_delta(orders, p_orders))
c4.metric("客単価",  f"¥{ticket:,.0f}", delta=_yen_delta(ticket, p_ticket))
c5.metric("粗利率",  f"{gp_rate:.1%}",  delta=_pct_delta(gp_rate, p_gp_rate))

tab1, tab2, tab3 = st.tabs(["📈 売上推移", "⏰ 時間帯・曜日分析", "📉 粗利・支払い"])

with tab1:
    st.plotly_chart(charts.daily_sales_line(df), use_container_width=True)
    st.plotly_chart(charts.weekday_sales_bar(df), use_container_width=True)

with tab2:
    st.plotly_chart(charts.hourly_bar(df), use_container_width=True)
    st.plotly_chart(charts.hourly_efficiency_bar(df), use_container_width=True)
    st.plotly_chart(charts.weekday_hourly_heatmap(df), use_container_width=True)

with tab3:
    st.plotly_chart(charts.ticket_histogram(df), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        if df["year_month"].nunique() < 2:
            st.info("粗利トレンドは2ヶ月以上の期間を選択すると表示されます。")
        else:
            st.plotly_chart(charts.monthly_gp_rate_line(df), use_container_width=True)
    with col2:
        st.plotly_chart(charts.payment_donut(df), use_container_width=True)

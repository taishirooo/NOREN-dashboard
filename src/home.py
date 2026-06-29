import sys
from pathlib import Path

# src/ をパスに追加して common モジュールを解決
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="NOREN ダッシュボード",
    page_icon="🏪",
    layout="wide",
)

pg = st.navigation({
    "分析ページ": [
        st.Page("apps/sales_summary/main.py",    title="売上サマリ",        icon="📊", url_path="sales"),
        st.Page("apps/inbound_analysis/main.py", title="インバウンド分析",   icon="🌏", url_path="inbound"),
        st.Page("apps/product_analysis/main.py", title="商品・カテゴリ分析", icon="🛍️", url_path="products"),
    ]
})
pg.run()
